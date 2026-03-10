# Pydantic Schemas Reference

## Overview

Complete reference for Pydantic v2 schemas used for request/response DTOs throughout the PDF Platform API.

## Schema Organization

Schemas are organized by model with consistent naming conventions:

- **Base** - Common fields shared across schemas
- **Create** - Request payloads for POST endpoints
- **Update** - Request payloads for PATCH/PUT endpoints
- **Response** - Response payloads from the API
- **WithRelations** - Response with nested related data

## User Schemas

### UserBase
Common user fields.

```python
email: EmailStr
full_name: Optional[str]
phone_number: Optional[str]
```

### UserCreate
Request schema for creating users.

```python
email: EmailStr
full_name: Optional[str]
phone_number: Optional[str]
password: str  # min 8 characters
```

**Example:**
```json
{
  "email": "user@example.com",
  "phone_number": "+201012345678",
  "full_name": "Ahmed Hassan",
  "password": "SecurePassword123"
}
```

### UserUpdate
Request schema for updating users.

```python
email: Optional[EmailStr]
full_name: Optional[str]
phone_number: Optional[str]
password: Optional[str]  # min 8 characters if provided
```

### UserResponse
API response schema for users.

```python
id: UUID
email: EmailStr
phone_number: Optional[str]
full_name: Optional[str]
is_active: bool
is_verified: bool
created_at: datetime
updated_at: datetime
```

### UserWithSubscriptions
User with nested subscription list.

```python
# All UserResponse fields +
subscriptions: list[SubscriptionWithPlan]
```

### UserWithSessions / UserWithJobs / UserWithPayments
Similar nested structures for other relationships.

---

## Plan Schemas

### PlanBase / PlanCreate
Plan creation/definition.

```python
name: str  # max 50 characters
description: Optional[str]
price_egp: Decimal  # 10 digits, 2 decimal places
max_files_per_month: int  # -1 for unlimited
max_file_size_mb: int
rate_limit_per_hour: Optional[int]  # -1 for unlimited
```

**Example:**
```json
{
  "name": "pro",
  "description": "Professional plan",
  "price_egp": "149.99",
  "max_files_per_month": -1,
  "max_file_size_mb": 10,
  "rate_limit_per_hour": null
}
```

### PlanResponse
API response for plans.

```python
id: int
name: str
description: Optional[str]
price_egp: Decimal
max_files_per_month: int
max_file_size_mb: int
rate_limit_per_hour: Optional[int]
created_at: datetime
```

---

## Subscription Schemas

### SubscriptionBase / SubscriptionCreate
Subscription creation.

```python
plan_id: int
is_active: bool = True
```

**Example:**
```json
{
  "plan_id": 2,
  "is_active": true
}
```

### SubscriptionUpdate
Update subscription.

```python
is_active: Optional[bool]
plan_id: Optional[int]
```

### SubscriptionResponse
Basic subscription response.

```python
id: UUID
user_id: UUID
plan_id: int
is_active: bool
expires_at: Optional[datetime]
created_at: datetime
updated_at: datetime
```

### SubscriptionWithPlan
Subscription with nested plan details.

```python
# All SubscriptionResponse fields +
plan: PlanResponse
```

---

## Session Schemas

### SessionCreate
Create authentication session.

```python
token: str
expires_at: datetime
user_agent: Optional[str]
ip_address: Optional[str]
```

### SessionResponse
Full session details (with token).

```python
id: UUID
user_id: UUID
token: str
user_agent: Optional[str]
ip_address: Optional[str]
expires_at: datetime
created_at: datetime
```

### SessionPublicResponse
Session details without sensitive token (for listings).

```python
id: UUID
user_agent: Optional[str]
ip_address: Optional[str]
expires_at: datetime
created_at: datetime
```

---

## Job Schemas

### JobCreate
Submit PDF processing job.

```python
job_type: str  # max 50 characters
input_file_path: str
```

**Example:**
```json
{
  "job_type": "convert",
  "input_file_path": "s3://bucket/uploads/document.pdf"
}
```

### JobUpdate
Update job status/progress.

```python
status: Optional[str]
output_file_path: Optional[str]
error_message: Optional[str]
started_at: Optional[datetime]
completed_at: Optional[datetime]
```

### JobResponse
Job details.

```python
id: UUID
user_id: UUID
status: str  # queued, processing, completed, failed
job_type: str
input_file_path: str
output_file_path: Optional[str]
error_message: Optional[str]
created_at: datetime
started_at: Optional[datetime]
completed_at: Optional[datetime]
```

---

## Payment Schemas

### PaymentCreate
Create payment record.

```python
amount_egp: Decimal  # 10 digits, 2 decimal places
payment_method: str  # credit_card, bank_transfer, wallet
description: Optional[str]
```

**Example:**
```json
{
  "amount_egp": "69.00",
  "payment_method": "credit_card",
  "description": "Monthly subscription renewal"
}
```

### PaymentUpdate
Update payment (typically for confirming/completing).

```python
status: Optional[str]
gateway_ref: Optional[str]
```

### PaymentResponse
Payment details.

```python
id: UUID
user_id: UUID
amount_egp: Decimal
status: str  # pending, completed, failed, refunded
gateway_ref: Optional[str]
payment_method: str
description: Optional[str]
created_at: datetime
updated_at: datetime
```

---

## API Endpoint Examples

### Create User

**Request:**
```http
POST /api/users
Content-Type: application/json

{
  "email": "newuser@example.com",
  "phone_number": "+201012345678",
  "full_name": "Ahmed El-Sayed",
  "password": "SecurePass123"
}
```

**Response (201 Created):**
```python
response_model = UserResponse
# Status 201
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "phone_number": "+201012345678",
  "full_name": "Ahmed El-Sayed",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-09T10:30:00+00:00",
  "updated_at": "2026-03-09T10:30:00+00:00"
}
```

### Create Job

**Request:**
```http
POST /api/jobs
Content-Type: application/json
Authorization: Bearer <token>

{
  "job_type": "convert",
  "input_file_path": "s3://pdf-bucket/uploads/resume.pdf"
}
```

**Response (201 Created):**
```python
response_model = JobResponse
# Status 201
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "job_type": "convert",
  "input_file_path": "s3://pdf-bucket/uploads/resume.pdf",
  "output_file_path": null,
  "error_message": null,
  "created_at": "2026-03-09T11:15:23+00:00",
  "started_at": null,
  "completed_at": null
}
```

### Get User with Subscriptions

**Request:**
```http
GET /api/users/550e8400-e29b-41d4-a716-446655440000/with-subscriptions
Authorization: Bearer <token>
```

**Response (200 OK):**
```python
response_model = UserWithSubscriptions
# Status 200
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "phone_number": "+201012345678",
  "full_name": "Ahmed El-Sayed",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-09T10:30:00+00:00",
  "updated_at": "2026-03-09T10:30:00+00:00",
  "subscriptions": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "plan_id": 2,
      "is_active": true,
      "expires_at": "2026-03-09T12:30:00+00:00",
      "created_at": "2026-03-09T11:30:00+00:00",
      "updated_at": "2026-03-09T11:30:00+00:00",
      "plan": {
        "id": 2,
        "name": "hourly",
        "description": "Hourly subscription plan",
        "price_egp": "7.50",
        "max_files_per_month": 3,
        "max_file_size_mb": 5,
        "rate_limit_per_hour": 60,
        "created_at": "2026-03-09T00:00:00+00:00"
      }
    }
  ]
}
```

---

## Validation Examples

### Valid User Creation

```python
from schemas import UserCreate

user_data = UserCreate(
    email="user@example.com",
    phone_number="+201012345678",
    full_name="Ahmed Hassan",
    password="SecurePass123"
)
# ✅ Valid
```

### Invalid - Short Password

```python
user_data = UserCreate(
    email="user@example.com",
    password="short"  # Less than 8 characters
)
# ❌ ValidationError: password must be at least 8 characters
```

### Invalid - Invalid Email

```python
user_data = UserCreate(
    email="not-an-email",  # Invalid format
    password="SecurePass123"
)
# ❌ ValidationError: invalid email format
```

### Valid Payment Creation

```python
from schemas import PaymentCreate
from decimal import Decimal

payment_data = PaymentCreate(
    amount_egp=Decimal("69.00"),
    payment_method="credit_card",
    description="Monthly subscription"
)
# ✅ Valid
```

---

## Common Patterns

### Request Validation

```python
from fastapi import FastAPI
from schemas import UserCreate, UserResponse

app = FastAPI()

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    # Pydantic validates automatically
    # If invalid, returns 422 Unprocessable Entity
    db_user = User(**user.model_dump())
    return db_user
```

### Partial Updates

```python
from schemas import UserUpdate

@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, user_update: UserUpdate):
    # Only provided fields are updated
    update_data = user_update.model_dump(exclude_unset=True)
    # update database...
    return updated_user
```

### List Response

```python
@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs(user_id: UUID):
    jobs = await db.execute(select(Job).where(Job.user_id == user_id))
    return jobs.scalars().all()
```

### Nested Response

```python
@app.get("/users/{user_id}/profile", response_model=UserWithSubscriptions)
async def get_user_profile(user_id: UUID):
    # Fetch user with relationships eager-loaded
    return user_with_subscriptions
```

---

## Configuration

All schemas use `ConfigDict(from_attributes=True)` for ORM mode:

```python
from pydantic import ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # Can be created directly from ORM objects
    id: UUID
    email: EmailStr
```

This allows converting SQLAlchemy models to Pydantic schemas:

```python
db_user = User(...)
response = UserResponse.model_validate(db_user)
```

---

## Type Hints

Supported types in schemas:

- `str` - String
- `int` - Integer
- `Decimal` - Decimal numbers (for money)
- `bool` - Boolean
- `UUID` - UUID identifier
- `datetime` - DateTime with timezone
- `EmailStr` - Email validation
- `Optional[T]` - Optional field
- `list[T]` - List of items
- `dict` - Dictionary

---

## Decimal Precision

For financial amounts use `Decimal` with proper precision:

```python
from decimal import Decimal

# Define in schema
amount_egp: Decimal = Field(..., decimal_places=2, max_digits=10)

# In validation
payment_data = PaymentCreate(
    amount_egp=Decimal("69.00")  # ✅ Correct
)

# Also works with string
payment_data = PaymentCreate(
    amount_egp="69.00"  # ✅ Automatically converted
)

# But not float (precision loss)
payment_data = PaymentCreate(
    amount_egp=69.00  # ❌ Avoid due to float precision
)
```
