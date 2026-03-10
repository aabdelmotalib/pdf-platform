"""
FastAPI dependency injection functions for authentication and authorization.

Provides:
- get_current_user: Decode JWT and fetch user from database
- require_active_subscription: Check for active, non-expired subscription
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_utils import decode_token
from db import Subscription, User, get_db


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and verify JWT access token from Authorization header.

    Required header: `Authorization: Bearer <token>`

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User object if token is valid and user exists

    Raises:
        HTTPException: 401 Unauthorized if:
            - No Authorization header
            - Invalid token format
            - Token expired or invalid
            - User not found
            - User email not verified
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Bearer token
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode JWT token
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID (subject)
    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify email is verified
    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify account is active
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return db_user


async def require_active_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Subscription:
    """
    Verify user has an active, non-expired subscription.

    Can be used as a dependency to protect endpoints that require subscription.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Active Subscription object

    Raises:
        HTTPException: 403 Forbidden if:
            - No active subscription found
            - Subscription is expired
            - Subscription is inactive
    """
    now = datetime.now(timezone.utc)

    # Query for active, non-expired subscription
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.is_active == True,
                Subscription.expires_at > now
            )
        )
    )
    subscription = result.scalars().first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active subscription found. Plan has expired or is inactive."
        )

    return subscription


# Type annotation for easy use in route handlers
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveSubscription = Annotated[Subscription, Depends(require_active_subscription)]
