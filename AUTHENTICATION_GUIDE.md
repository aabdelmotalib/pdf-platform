# Authentication System Guide

Complete authentication system for PDF Platform API with JWT tokens, email verification, and rate limiting.

---

## ✨ Features

- ✅ **Email Verification** - Users must verify email before login
- ✅ **JWT Access Tokens** - 15-minute expiry for API access
- ✅ **Refresh Tokens** - 30-day HttpOnly cookies for session persistence
- ✅ **Password Security** - bcrypt hashing with strength validation
- ✅ **Rate Limiting** - 5 login attempts per 15 minutes per IP
- ✅ **Brevo SMTP** - Email sending via Brevo transactional email service
- ✅ **CORS Enabled** - Secure cross-origin requests
- ✅ **OpenAPI Docs** - Full documentation at `/docs`

---

## 📁 File Structure

```
api/
├── config.py                    # Settings & environment variables
├── auth_utils.py               # JWT & password utilities
├── email_service.py            # Brevo SMTP email sending
├── dependencies.py             # FastAPI dependency injection
├── routers/
│   ├── __init__.py
│   └── auth.py                 # Authentication endpoints
└── main.py                     # FastAPI app with auth router
```

---

## 🔐 API Endpoints

### 1. Register User
```http
POST /auth/register
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=SecurePass123&phone_number=%2B201234567890
```

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Ahmed Hassan",
  "phone_number": "+201234567890",
  "is_verified": false,
  "is_active": true,
  "created_at": "2025-03-09T10:30:00Z"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)

**Errors:**
- `400` - Email already registered
- `400` - Password doesn't meet requirements
- `422` - Validation error (invalid email, phone format)
- `429` - Rate limited (10 attempts per hour)

---

### 2. Verify Email
```http
GET /auth/verify-email?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com",
  "verified_at": "2025-03-09T10:35:00Z"
}
```

**Token Validity:** 24 hours from registration

**Errors:**
- `400` - Invalid or expired token
- `400` - Wrong token type
- `404` - User not found

---

### 3. Login
```http
POST /auth/login?email=user@example.com&password=SecurePass123
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "full_name": "Ahmed Hassan",
    "is_verified": true,
    "is_active": true
  }
}
```

**Cookies Set:**
- `refresh_token` - HttpOnly, 30 days expiry
- Only accessible server-side (not from JavaScript)

**Access Token Expiry:** 15 minutes

**Errors:**
- `401` - Invalid email or password
- `401` - Email not verified
- `401` - Account deactivated
- `429` - Rate limited (5 attempts per 15 minutes)

---

### 4. Refresh Token
```http
POST /auth/refresh

# Cookie automatically sent by browser: refresh_token=...
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` - Refresh token not found in cookies
- `401` - Invalid or expired refresh token

---

### 5. Logout
```http
POST /auth/logout
```

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

**Effect:** Clears `refresh_token` cookie

---

### 6. Get Current User
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "Ahmed Hassan",
  "phone_number": "+201234567890",
  "is_verified": true,
  "is_active": true,
  "created_at": "2025-03-09T10:30:00Z",
  "updated_at": "2025-03-09T10:35:00Z"
}
```

**Errors:**
- `401` - Missing or invalid access token
- `401` - Email not verified

---

## 🛡️ Using Access Tokens

### In JavaScript/Frontend:

```javascript
// After login, store access token
const response = await fetch('/auth/login?email=user@example.com&password=Pass');
const data = await response.json();
const accessToken = data.access_token;

// Use in API calls
const userResponse = await fetch('/auth/me', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// Refresh token cookie sent automatically by browser
const refreshResponse = await fetch('/auth/refresh', {
  method: 'POST',
  credentials: 'include'  // Include cookies
});
```

### In Python/FastAPI:

```python
from dependencies import get_current_user, CurrentUser

@app.get("/protected")
async def protected_route(current_user: CurrentUser):
    # current_user is automatically injected from JWT token
    return {"user_id": current_user.id, "email": current_user.email}
```

### In curl:

```bash
# Login
curl -X POST "http://localhost:8000/auth/login?email=user@example.com&password=SecurePass123" \
  -i

# Extract access token and use
TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📧 Email Verification Flow

### Step 1: User Registers
```bash
POST /auth/register
# Returns 201, user is NOT verified yet
```

### Step 2: Verification Email Sent
- Email sent to user's address via Brevo SMTP
- Contains verification link with JWT token
- Token valid for 24 hours

### Step 3: User Clicks Verification Link
```bash
GET /auth/verify-email?token=...
# Email is now verified
```

### Step 4: User Can Login
```bash
POST /auth/login
# Now succeeds because email is verified
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in `/api` directory:

```bash
# Strategy settings
SECRET_KEY=your-super-secret-key-change-this-minimum-32-characters
ENVIRONMENT=production

# Database
POSTGRES_DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_platform

# Brevo SMTP
BREVO_SMTP_HOST=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_USER=your-brevo-email@example.com
BREVO_SMTP_PASSWORD=your-brevo-smtp-key
BREVO_FROM_EMAIL=noreply@pdfplatform.com
BREVO_FROM_NAME=PDF Platform

# API
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Cookie settings
COOKIE_SECURE=true        # false in development
COOKIE_SAME_SITE=lax

# Features
DEBUG=false
```

### Password Policy

In `config.py`:

```python
PASSWORD_MIN_LENGTH = 8              # Minimum password length
PASSWORD_REQUIRE_UPPERCASE = True    # A-Z required
PASSWORD_REQUIRE_DIGITS = True       # 0-9 required
PASSWORD_REQUIRE_SPECIAL = True      # !@#$%^&* etc required
```

### JWT Configuration

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 15     # Access token validity
REFRESH_TOKEN_EXPIRE_DAYS = 30       # Refresh token validity
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24
```

### Rate Limiting

```python
RATE_LIMIT_LOGIN = "5/15minutes"     # 5 attempts per 15 minutes
RATE_LIMIT_REGISTER = "10/hour"      # 10 attempts per hour
```

---

## 🔧 Using Dependencies

### Get Current User

```python
from dependencies import CurrentUser, get_current_user
from fastapi import Depends

@app.get("/profile")
async def get_profile(current_user: CurrentUser):
    # current_user is User object
    return {"email": current_user.email, "verified": current_user.is_verified}

# Or manually:
@app.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return {"email": user.email}
```

### Require Active Subscription

```python
from dependencies import ActiveSubscription, require_active_subscription

@app.post("/jobs/submit")
async def submit_job(
    current_user: CurrentUser,
    subscription: ActiveSubscription,
):
    # Both dependencies satisfied, user has active subscription
    return {"job": "submitted", "plan": subscription.plan.name}

# Error if no active subscription:
# 403 Forbidden: "No active subscription found. Plan has expired or is inactive."
```

---

## 🧪 Testing Authentication

### Register and Login Flow

```bash
#!/bin/bash

API="http://localhost:8000"

# 1. Register
echo "1. Registering user..."
curl -X POST "$API/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=testuser@example.com&password=SecurePass123&phone_number=%2B201234567890&full_name=Test%20User"

# 2. Verify email (use token from email or check database)
echo "\n2. Verifying email..."
TOKEN="<paste-verification-token-from-email>"
curl -X GET "$API/auth/verify-email?token=$TOKEN"

# 3. Login
echo "\n3. Logging in..."
LOGIN_RESPONSE=$(curl -s -i -X POST "$API/auth/login?email=testuser@example.com&password=SecurePass123")
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -oP '"access_token":"?\K[^",}]*')
COOKIE=$(echo $LOGIN_RESPONSE | grep -oP 'refresh_token=\K[^;]+')

# 4. Use access token
echo "\n4. Getting user profile..."
curl -X GET "$API/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 5. Refresh token
echo "\n5. Refreshing token..."
curl -X POST "$API/auth/refresh" \
  -H "Cookie: refresh_token=$COOKIE"

# 6. Logout
echo "\n6. Logging out..."
curl -X POST "$API/auth/logout" \
  -H "Cookie: refresh_token=$COOKIE"
```

### Rate Limiting Test

```bash
# Try to login 6 times in 15 minutes
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST "http://localhost:8000/auth/login?email=user@example.com&password=WrongPass"
  echo "\n"
  sleep 1
done

# 6th attempt returns 429 Too Many Requests
```

---

## 🐛 Troubleshooting

### "Invalid or expired access token" on /auth/me

**Issues:**
- Token expired (15 minutes)
- Token malformed
- Token from wrong SECRET_KEY

**Solution:**
```bash
# Get new access token
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Cookie: refresh_token=..."
```

### "Rate limit exceeded" on login

**Cause:** More than 5 login attempts in 15 minutes from same IP

**Solution:**
- Wait 15 minutes
- Use different IP (VPN) for testing
- Reduce rate limit in config.py (development only)

### "Email not verified" on login

**Cause:** User hasn't clicked verification email link

**Solution:**
- Check spam folder for verification email
- Brevo SMTP config might be wrong
- Check logs for email sending errors

### "Refresh token not found in cookies"

**Cause:** Cookie not sent by client

**Solution (JavaScript):**
```javascript
const response = await fetch('/auth/refresh', {
  method: 'POST',
  credentials: 'include'  // Important! Include cookies
});
```

### Email not sending

**Causes:**
1. Brevo SMTP credentials wrong
2. BREVO_SMTP_HOST unreachable
3. Invalid recipient email

**Debug:**
```python
# Check config
from config import settings
print(settings.BREVO_SMTP_HOST)
print(settings.BREVO_SMTP_USER)

# Test email manually
import smtplib
smtp = smtplib.SMTP(settings.BREVO_SMTP_HOST, settings.BREVO_SMTP_PORT)
smtp.starttls()
smtp.login(settings.BREVO_SMTP_USER, settings.BREVO_SMTP_PASSWORD)
```

---

## 🔌 Integration Examples

### With Protected Job Submission Endpoint

```python
from fastapi import APIRouter
from dependencies import CurrentUser, ActiveSubscription

router = APIRouter()

@router.post("/jobs/submit")
async def submit_job(
    file_path: str,
    current_user: CurrentUser,
    subscription: ActiveSubscription,
):
    """Submit PDF conversion job (requires active subscription)"""
    return {
        "user_id": current_user.id,
        "file": file_path,
        "plan": subscription.plan.name,
        "files_used": 1,
        "files_available": subscription.plan.max_files
    }
```

### With Custom Exception Handling

```python
from fastapi import HTTPException

try:
    user = await get_current_user(request, db)
except HTTPException as e:
    # Handle 401 Unauthorized
    return custom_error_response(e.status_code, e.detail)
```

### With Token Refresh Validation

```python
from auth_utils import decode_token, verify_token_type

@router.post("/auth/refresh-safe")
async def safe_refresh(request: Request):
    """Refresh with extra validation"""
    token = request.cookies.get("refresh_token")
    token_data = decode_token(token)
    
    if not verify_token_type(token_data, "refresh"):
        raise HTTPException(status_code=401, detail="Not a refresh token")
    
    # Issue new access token...
```

---

## 📊 Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Authentication Flow                       │
└─────────────────────────────────────────────────────────────┘

1. REGISTRATION
   ┌──────────┐         ┌─────────┐         ┌────────┐
   │  Client  │◄───────►│  FastAPI │◄───────►│   DB   │
   └──────────┘         └─────────┘         └────────┘
        │                    │                    │
        ├─ POST /register    ├─ Hash password     │
        │                    ├─ Create user       ├─ INSERT user
        │                    ├─ Gen JWT token     │
        │◄─ Response 201     ├─ Send email        │
        └─ Check email       └──────┬─────────────┘
                                    │
                         Brevo SMTP │
                                    ▼
                            ┌────────────┐
                            │User Inbox  │
                            └────────────┘

2. EMAIL VERIFICATION
   User clicks link in email with JWT token
   
        ┌──────────┐         ┌─────────┐         ┌────────┐
        │  Client  │         │  FastAPI │         │   DB   │
        └──────────┘         └─────────┘         └────────┘
             │                    │                    │
        ├─ GET /verify-email?token=xxx               │
        │────────────────────►│                       │
        │                    ├─ Decode JWT token     │
        │                    ├─ Verify email=xxx     │
        │                    ├─ Update user          ├─ UPDATE user.is_verified=true
        │◄────────────────────┤─ Response 200        │
        ├─ Now can login      └───────────────────────┘
        │

3. LOGIN
   ┌──────────┐         ┌─────────┐         ┌────────┐
   │  Client  │         │  FastAPI │         │   DB   │
   └──────────┘         └─────────┘         └────────┘
        │                    │                    │
        ├─ POST /login       │                    │
        │ email, password     │                    │
        │────────────────────►│                    │
        │                    ├─ Query user        ├─ SELECT user BY email
        │                    │◄───────────────────┤
        │                    ├─ Verify password    │
        │                    ├─ Create JWT tokens  │
        │                    │  - access_token (15min)
        │                    │  - refresh_token (30d)
        │◄────────────────────┤─ Response + Cookie │
        ├─ Store access_token │                    │
        └─ Browser stores refresh_token cookie


4. AUTHENTICATED REQUEST
   ┌──────────┐         ┌─────────┐
   │  Client  │         │  FastAPI │
   └──────────┘         └─────────┘
        │                    │
        ├─ GET /auth/me      │
        │ Authorization: Bearer access_token
        │────────────────────►│
        │                    ├─ Decode JWT
        │                    ├─ Extract user_id
        │                    ├─ Fetch user from DB
        │◄────────────────────┤─ Return user data
        ├─ Got user info      │


5. TOKEN REFRESH
   ┌──────────┐         ┌─────────┐
   │  Client  │         │  FastAPI │
   └──────────┘         └─────────┘
        │                    │
        ├─ POST /refresh     │
        │ Cookie: refresh_token=xxx
        │────────────────────►│
        │                    ├─ Decode refresh_token
        │                    ├─ Verify it's refresh type
        │                    ├─ Create new access_token
        │◄────────────────────┤─ Response with new token
        ├─ Update access_token │


6. LOGOUT
   ┌──────────┐         ┌─────────┐
   │  Client  │         │  FastAPI │
   └──────────┘         └─────────┘
        │                    │
        ├─ POST /logout      │
        │────────────────────►│
        │                    ├─ Delete refresh_token cookie
        │◄────────────────────┤─ Response 200
        ├─ Clear cookies      │
        ├─ Clear local storage │
        └─ Redirect to login   │
```

---

## 📚 OpenAPI Documentation

View full API documentation:

```
http://localhost:8000/docs           # Swagger UI (interactive)
http://localhost:8000/redoc          # ReDoc (alternative UI)
http://localhost:8000/openapi.json   # OpenAPI schema (JSON)
```

### Try It Out in Swagger UI:
1. Go to http://localhost:8000/docs
2. Click on `/auth/register` endpoint
3. Click "Try it out"
4. Fill in example values
5. Click "Execute"
6. See response

---

## 🎯 Next Steps

1. **Test All Endpoints** - Use curl or Postman
2. **Build Frontend** - Implement login form using auth endpoints
3. **Add More Routers** - Create routers for jobs, payments, etc.
4. **Implement Rate Limiting** - Tune settings for production
5. **Setup Email Service** - Configure real Brevo account
6. **Enable CORS** - Configure for frontend domain
7. **Add Monitoring** - Log authentication events
8. **Security Audit** - Review production settings

---

## ✅ Checklist

- ✅ Config system with environment variables
- ✅ Password hashing with bcrypt
- ✅ JWT token creation/validation
- ✅ Email verification with Brevo SMTP
- ✅ Login with rate limiting
- ✅ Token refresh mechanism
- ✅ CurrentUser dependency
- ✅ ActiveSubscription dependency
- ✅ CORS configured
- ✅ All endpoints documented in OpenAPI

**Ready to use! 🚀**
