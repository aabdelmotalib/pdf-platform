# Authentication System - Quick Reference

## API Endpoints Summary

| Method | Endpoint | Parameters | Response | Rate Limit |
|--------|----------|-----------|----------|-----------|
| POST | `/auth/register` | `email`, `password`, `phone`, `full_name` | `201` User | 10/hour |
| GET | `/auth/verify-email` | `token` (query) | `200` Verified | None |
| POST | `/auth/login` | `email`, `password` (query) | `200` + Cookie | 5/15min |
| POST | `/auth/refresh` | `refresh_token` (cookie) | `200` Token | None |
| POST | `/auth/logout` | None | `200` Message | None |
| GET | `/auth/me` | `Authorization` header | `200` User | None |

---

## Usage Examples

### Register
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=user@example.com&password=SecurePass123&phone_number=%2B201234567890"
```

### Verify Email
```bash
curl "http://localhost:8000/auth/verify-email?token=<JWT_TOKEN>"
```

### Login
```bash
curl -i -X POST "http://localhost:8000/auth/login?email=user@example.com&password=SecurePass123"
# Returns: access_token in body + refresh_token in cookie
```

### Use Access Token
```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  "http://localhost:8000/auth/me"
```

### Refresh Token
```bash
curl -i -X POST "http://localhost:8000/auth/refresh" \
  -H "Cookie: refresh_token=<REFRESH_TOKEN>"
```

### Logout
```bash
curl -X POST "http://localhost:8000/auth/logout"
```

---

## Protected Endpoints

### Require Current User
```python
from dependencies import CurrentUser

@app.get("/profile")
async def get_profile(user: CurrentUser):
    return {"email": user.email}
```

### Require Active Subscription
```python
from dependencies import CurrentUser, ActiveSubscription

@app.post("/jobs/submit")
async def submit_job(
    user: CurrentUser,
    subscription: ActiveSubscription,
):
    return {"plan": subscription.plan.name}
```

---

## Error Codes

| Code | Error | Cause |
|------|-------|-------|
| 201 | Created | Register success |
| 200 | OK | All successful operations |
| 400 | Bad Request | Invalid data, email exists, short password |
| 401 | Unauthorized | Wrong credentials, expired token, not verified |
| 403 | Forbidden | No active subscription |
| 404 | Not Found | User not found |
| 422 | Validation Error | Invalid email/phone format |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Email sending failed |

---

## Configuration

### Environment Variables
```bash
SECRET_KEY=your-min-32-char-secret-key
POSTGRES_DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_platform
BREVO_SMTP_HOST=smtp-relay.brevo.com
BREVO_SMTP_USER=your-brevo-email@example.com
BREVO_SMTP_PASSWORD=your-brevo-smtp-key
API_BASE_URL=http://localhost:8000
```

### Token Timeouts
- Access Token: **15 minutes**
- Refresh Token: **30 days**
- Email Verification: **24 hours**

### Rate Limits
- Login: **5 per 15 minutes** per IP
- Register: **10 per hour** per IP

---

## Files Created

| File | Purpose |
|------|---------|
| `config.py` | Settings & environment variables |
| `auth_utils.py` | JWT & password functions |
| `email_service.py` | Brevo SMTP email sending |
| `dependencies.py` | FastAPI dependency injection |
| `routers/auth.py` | Authentication endpoints |
| `main.py` | Updated with auth router & CORS |

---

## JavaScript Example

```javascript
// Register
async function register(email, password, phone_number) {
  const formData = new FormData();
  formData.append('email', email);
  formData.append('password', password);
  formData.append('phone_number', phone_number);
  
  const res = await fetch('/auth/register', {
    method: 'POST',
    body: formData
  });
  return res.json();
}

// Login
async function login(email, password) {
  const res = await fetch(`/auth/login?email=${email}&password=${password}`, {
    method: 'POST',
    credentials: 'include'  // Include cookies
  });
  const data = await res.json();
  localStorage.setItem('access_token', data.access_token);
  return data;
}

// Use Access Token
async function getProfile(accessToken) {
  const res = await fetch('/auth/me', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  return res.json();
}

// Refresh Token
async function refreshToken() {
  const res = await fetch('/auth/refresh', {
    method: 'POST',
    credentials: 'include'  // Include cookies
  });
  const data = await res.json();
  localStorage.setItem('access_token', data.access_token);
  return data;
}

// Logout
async function logout() {
  await fetch('/auth/logout', { method: 'POST' });
  localStorage.removeItem('access_token');
}
```

---

## Python Client Example

```python
import httpx
import json

BASE_URL = "http://localhost:8000"

# Create client with cookie jar
client = httpx.Client()

# Register
response = client.post(
    f"{BASE_URL}/auth/register",
    data={
        "email": "user@example.com",
        "password": "SecurePass123",
        "phone_number": "+201234567890"
    }
)
print("Register:", response.json())

# Verify email (use token from email or DB)
response = client.get(
    f"{BASE_URL}/auth/verify-email?token=<TOKEN>"
)
print("Verify:", response.json())

# Login
response = client.post(
    f"{BASE_URL}/auth/login?email=user@example.com&password=SecurePass123"
)
login_data = response.json()
access_token = login_data['access_token']
print("Login:", login_data)

# Use access token
response = client.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
print("Me:", response.json())

# Refresh token (cookies maintained by client)
response = client.post(f"{BASE_URL}/auth/refresh")
new_token = response.json()['access_token']
print("Refresh:", new_token)

# Logout
response = client.post(f"{BASE_URL}/auth/logout")
print("Logout:", response.json())
```

---

## Password Requirements

✓ Minimum 8 characters  
✓ At least 1 UPPERCASE letter  
✓ At least 1 digit (0-9)  
✓ At least 1 special character (!@#$%^&*)  

**Example valid:** `SecurePass123!`  
**Example invalid:** `short` (too short, no uppercase, no special char)

---

## Content-Type Headers

- **Query Parameters:** No Content-Type needed
- **Form Data:** `Content-Type: application/x-www-form-urlencoded`
- **JSON:** `Content-Type: application/json`

---

## CORS Settings

Allowed origins from config:
- http://localhost:3000 (frontend dev)
- http://localhost:8000 (API dev)
- Custom via FRONTEND_URL env var

Set in `.env`:
```bash
FRONTEND_URL=https://yourfrontend.com
```

---

## Swagger UI

Test endpoints at: http://localhost:8000/docs

1. Click endpoint
2. "Try it out"
3. Fill values
4. "Execute"
5. See response

---

## Phone Number Format

Use E.164 international format:
- **Egypt:** `+20` prefix
- **Example:** `+201234567890`
- **Valid:** `+1234567890`, `+449876543210`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check token in header: `Authorization: Bearer <token>` |
| 429 Rate Limited | Wait 15 minutes or try from different IP |
| 400 Email Exists | Email already registered |
| No email received | Check spam folder, verify Brevo config |
| Token expired | Use refresh endpoint to get new access token |

---

## API Documentation

- **Swagger:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc  
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

**Complete authentication system ready! 🚀**
