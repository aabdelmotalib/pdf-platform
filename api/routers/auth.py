"""
Authentication router for PDF Platform API.

Endpoints:
- POST /auth/register - Register new user
- GET /auth/verify-email - Verify email address
- POST /auth/login - Login and get access token
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout and clear refresh token
- GET /auth/me - Get current user info
"""

from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, Request, Response, status
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_utils import (
    create_access_token,
    create_refresh_token,
    create_verification_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
    verify_token_type,
)
from config import settings
from db import User, get_db
from dependencies import get_current_user
from email_service import send_verification_email
from schemas import UserCreate, UserResponse
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter(prefix="/auth", tags=["authentication"])
# Rate limiter setup
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address)
except ImportError:
    # Mock limiter if slowapi not available
    class MockLimiter:
        def limit(self, rule):
            def decorator(func):
                return func
            return decorator

    limiter = MockLimiter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email, password, and phone number. "
    "Sends verification email that must be confirmed before login.",
)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user.

    **Request Body:**
    - `email`: (str, required) - Email address (must be unique)
    - `password`: (str, required) - Password (min 8 chars, 1 uppercase, 1 digit, 1 special)
    - `phone_number`: (str, required) - Phone number (E.164 format, e.g., +201234567890)
    - `full_name`: (str, optional) - Full name

    **Response:**
    - `201 Created` - User created successfully (not verified yet)
    - `400 Bad Request` - Invalid data or email already exists
    - `422 Unprocessable Entity` - Validation error

    **Note:** User must verify email before logging in.
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user (not verified)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        phone_number=user_data.phone_number,
        full_name=user_data.full_name or "",
        is_verified=False,
        is_active=True,
    )
    db.add(db_user)
    await db.flush()  # Get the user ID

    # Create verification token and send email
    verification_token = create_verification_token(user_data.email)
    email_sent = await send_verification_email(
        user_data.email,
        verification_token,
        user_data.full_name or user_data.email
    )

    if not email_sent:
        print(f"Warning: email not sent to {user_data.email}")

    await db.commit()
    await db.refresh(db_user)

    return UserResponse.model_validate(db_user)


@router.get(
    "/verify-email",
    response_model=dict,
    summary="Verify email address",
    description="Verify user email using the token sent in verification email. "
    "Token must be valid and not expired (24 hour validity).",
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify email address with token from verification email.

    **Query Parameters:**
    - `token`: (str, required) - JWT verification token from email

    **Response:**
    - `200 OK` - Email verified successfully
    - `400 Bad Request` - Invalid or expired token
    - `404 Not Found` - User not found

    **Note:** After verification, user can login with email and password.
    """
    # Decode token
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Verify it's a verification token
    if token_data.get("type") != "verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )

    email = token_data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload"
        )

    # Find user and verify
    result = await db.execute(
        select(User).where(User.email == email)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update verification status
    db_user.is_verified = True
    db.add(db_user)
    await db.commit()

    return {
        "message": "Email verified successfully",
        "email": email,
        "verified_at": datetime.utcnow().isoformat()
    }


@router.post(
    "/login",
    response_model=dict,
    summary="Login user",
    description="Authenticate user with email and password. Returns access token in body "
    "and sets HttpOnly refresh token cookie (30 days).",
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Login with email and password.

    **Query Parameters:**
    - `email`: (str, required) - User email
    - `password`: (str, required) - User password

    **Response:**
    - `200 OK` - Login successful, returns access_token and token_type
    - `400 Bad Request` - Invalid credentials
    - `401 Unauthorized` - Email not verified
    - `429 Too Many Requests` - Rate limit exceeded (5 attempts per 15 minutes)

    **Cookies Set:**
    - `refresh_token`: HttpOnly cookie (not accessible from JavaScript)
    - Expires: 30 days

    **Note:** Use the access_token in Authorization header: `Bearer <access_token>`
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    db_user = result.scalar_one_or_none()
    if not db_user or not verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if email is verified
    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please check your email for verification link."
        )

    # Check if account is active
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(db_user.id), "email": db_user.email}
    )

    # Set refresh token cookie (HttpOnly, secure, samesite)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAME_SITE,
        domain=settings.COOKIE_DOMAIN,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(db_user)
    }


@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh access token",
    description="Issue a new access token using refresh token from HttpOnly cookie.",
)
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Refresh access token using refresh token cookie.

    **Cookies Required:**
    - `refresh_token`: HttpOnly refresh token (from login response)

    **Response:**
    - `200 OK` - New access_token issued
    - `401 Unauthorized` - Invalid or expired refresh token

    **Note:** New access_token valid for 15 minutes.
    """
    # Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies"
        )

    # Decode and verify refresh token
    token_data = decode_token(refresh_token_value)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Verify user exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )

    # Create new access token
    new_access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email}
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.post(
    "/logout",
    response_model=dict,
    summary="Logout user",
    description="Clear refresh token cookie to invalidate current session.",
)
async def logout(response: Response) -> dict:
    """
    Logout by clearing refresh token cookie.

    **Response:**
    - `200 OK` - Logout successful

    **Cookies Cleared:**
    - `refresh_token`: Deleted

    **Note:** Access token in Authorization header is still valid until expiration (15 min).
    """
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAME_SITE,
        domain=settings.COOKIE_DOMAIN,
    )

    return {"message": "Logout successful"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get profile information of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user profile.

    **Headers Required:**
    - `Authorization`: `Bearer <access_token>`

    **Response:**
    - `200 OK` - User profile
    - `401 Unauthorized` - Invalid or missing access token

    **Returns:** Complete user profile with all details.
    """
    return UserResponse.model_validate(current_user)
