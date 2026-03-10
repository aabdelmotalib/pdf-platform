# SQLAlchemy Models Reference

## Overview

Complete reference for all SQLAlchemy ORM models in the PDF Platform database.

## Models

### User

User account model with authentication details.

**Columns:**
- `id` (UUID, PK): Unique identifier
- `email` (String, unique): User email address
- `phone_number` (String, optional): Phone number
- `password_hash` (String): Hashed password
- `full_name` (String, optional): User's full name
- `is_active` (Boolean, default=True): Account active status
- `is_verified` (Boolean, default=False): Email verification status
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- `subscriptions`: One-to-many with Subscription
- `sessions`: One-to-many with Session
- `jobs`: One-to-many with Job
- `payments`: One-to-many with Payment

**Indexes:**
- `uq_users_email`: Unique constraint on email
- `idx_users_email`: Regular index on email

**Example:**
```python
from db import User
from sqlalchemy import select

# Create user
user = User(
    email="user@example.com",
    password_hash=hash_password("password"),
    full_name="Ahmed Hassan",
    phone_number="+201012345678"
)
session.add(user)

# Query user
result = await session.execute(select(User).where(User.email == "user@example.com"))
user = result.scalar_one_or_none()
```

---

### Plan

Subscription plan definition.

**Columns:**
- `id` (Integer, PK): Plan identifier
- `name` (String, unique): Plan name (free, hourly, monthly)
- `description` (Text, optional): Plan description
- `price_egp` (Numeric): Price in EGP
- `max_files_per_month` (Integer): Max files (-1 for unlimited)
- `max_file_size_mb` (Integer): Max file size in MB
- `rate_limit_per_hour` (Integer, optional): Requests per hour (-1 for unlimited)
- `created_at` (DateTime): Creation timestamp

**Relationships:**
- `subscriptions`: One-to-many with Subscription

**Default Plans:**
```
1. Free:    0 EGP,  1 file/month,  2 MB
2. Hourly:  7.50 EGP, 3 files/month, 5 MB, 60 req/hour
3. Monthly: 69 EGP, unlimited files, 5 MB
```

**Example:**
```python
from db import Plan
from sqlalchemy import select

# Get plan
result = await session.execute(select(Plan).where(Plan.id == 1))
plan = result.scalar_one_or_none()  # Returns 'free' plan

# List all plans
result = await session.execute(select(Plan))
plans = result.scalars().all()
```

---

### Subscription

User subscription to a plan.

**Columns:**
- `id` (UUID, PK): Unique identifier
- `user_id` (UUID, FK): Reference to User
- `plan_id` (Integer, FK): Reference to Plan
- `is_active` (Boolean, default=True): Subscription active status
- `expires_at` (DateTime, optional): Subscription expiration time
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- `user`: Many-to-one with User
- `plan`: Many-to-one with Plan

**Indexes:**
- `idx_subscriptions_user_id_is_active`: Composite on (user_id, is_active)
- `idx_subscriptions_expires_at_partial`: Partial on expires_at WHERE is_active=true

**Example:**
```python
from db import Subscription, Plan
from sqlalchemy import select
from datetime import datetime, timedelta

# Create subscription
subscription = Subscription(
    user_id=user_id,
    plan_id=2,  # hourly plan
    is_active=True,
    expires_at=datetime.utcnow() + timedelta(hours=1)
)
session.add(subscription)

# Get active subscriptions
result = await session.execute(
    select(Subscription)
    .where((Subscription.user_id == user_id) & (Subscription.is_active == True))
)
active_subs = result.scalars().all()

# Get subscription with plan details
result = await session.execute(
    select(Subscription).join(Plan).where(Subscription.user_id == user_id)
)
sub = result.scalar_one_or_none()
plan_info = sub.plan  # Lazy load or pre-joined
```

---

### Session

User authentication session.

**Columns:**
- `id` (UUID, PK): Unique identifier
- `user_id` (UUID, FK): Reference to User
- `token` (String, unique): Authentication token
- `user_agent` (String, optional): User agent string
- `ip_address` (String, optional): Client IP address
- `expires_at` (DateTime): Token expiration time
- `created_at` (DateTime): Creation timestamp

**Relationships:**
- `user`: Many-to-one with User

**Indexes:**
- `idx_sessions_user_id_expires_at`: Composite on (user_id, expires_at)
- `idx_sessions_token`: Regular index on token

**Example:**
```python
from db import Session
from sqlalchemy import select
from datetime import datetime, timedelta

# Create session
session = Session(
    user_id=user_id,
    token=generate_jwt_token(),
    expires_at=datetime.utcnow() + timedelta(days=30),
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0..."
)
db_session.add(session)

# Verify token
result = await db_session.execute(
    select(Session)
    .where((Session.token == token) & (Session.expires_at > datetime.utcnow()))
)
session = result.scalar_one_or_none()

# Get active sessions for user
result = await db_session.execute(
    select(Session)
    .where((Session.user_id == user_id) & (Session.expires_at > datetime.utcnow()))
)
active_sessions = result.scalars().all()
```

---

### Job

PDF processing job.

**Columns:**
- `id` (UUID, PK): Unique identifier
- `user_id` (UUID, FK): Reference to User
- `status` (String, default='queued'): Job status
  - `queued`: Waiting to be processed
  - `processing`: Currently processing
  - `completed`: Successfully completed
  - `failed`: Processing failed
- `job_type` (String): Type of job (convert, merge, split, etc.)
- `input_file_path` (String): Path to input file
- `output_file_path` (String, optional): Path to output file
- `error_message` (Text, optional): Error details if failed
- `created_at` (DateTime): Creation timestamp
- `started_at` (DateTime, optional): Processing start time
- `completed_at` (DateTime, optional): Completion time

**Relationships:**
- `user`: Many-to-one with User

**Indexes:**
- `idx_jobs_user_id_created_at_desc`: Composite on (user_id, created_at DESC)
- `idx_jobs_status_partial`: Partial on status WHERE status IN ('queued', 'processing')

**Example:**
```python
from db import Job
from sqlalchemy import select
from datetime import datetime

# Create job
job = Job(
    user_id=user_id,
    job_type="convert",
    input_file_path="s3://bucket/uploads/file.pdf",
    status="queued"
)
session.add(job)

# Get pending jobs
result = await session.execute(
    select(Job)
    .where(Job.status.in_(["queued", "processing"]))
    .order_by(Job.created_at)
)
pending_jobs = result.scalars().all()

# Update job status
job.status = "processing"
job.started_at = datetime.utcnow()
await session.commit()

# Complete job
job.status = "completed"
job.output_file_path = "s3://bucket/results/file_converted.pdf"
job.completed_at = datetime.utcnow()
await session.commit()

# Get user's recent jobs
result = await session.execute(
    select(Job)
    .where(Job.user_id == user_id)
    .order_by(Job.created_at.desc())
    .limit(10)
)
recent_jobs = result.scalars().all()
```

---

### Payment

Payment record.

**Columns:**
- `id` (UUID, PK): Unique identifier
- `user_id` (UUID, FK): Reference to User
- `amount_egp` (Numeric): Amount in EGP
- `status` (String, default='pending'): Payment status
  - `pending`: Awaiting processing
  - `completed`: Payment confirmed
  - `failed`: Payment failed
  - `refunded`: Payment refunded
- `gateway_ref` (String, unique, optional): Payment gateway reference
- `payment_method` (String): Method used
  - `credit_card`
  - `bank_transfer`
  - `wallet`
- `description` (Text, optional): Payment description
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- `user`: Many-to-one with User

**Indexes:**
- `uq_payments_gateway_ref`: Unique constraint on gateway_ref
- `idx_payments_user_id_created_at_desc`: Composite on (user_id, created_at DESC)

**Example:**
```python
from db import Payment
from sqlalchemy import select

# Create payment
payment = Payment(
    user_id=user_id,
    amount_egp=Decimal("69.00"),
    payment_method="credit_card",
    status="pending",
    description="Monthly subscription - March 2026"
)
session.add(payment)

# Verify duplicate payment gateway reference
result = await session.execute(
    select(Payment).where(Payment.gateway_ref == gateway_ref)
)
existing = result.scalar_one_or_none()

# Update payment status
payment.status = "completed"
payment.gateway_ref = "gw_12345678"
await session.commit()

# Get user's recent payments
result = await session.execute(
    select(Payment)
    .where(Payment.user_id == user_id)
    .order_by(Payment.created_at.desc())
    .limit(20)
)
payments = result.scalars().all()

# Get successful payments
result = await session.execute(
    select(Payment)
    .where((Payment.user_id == user_id) & (Payment.status == "completed"))
    .order_by(Payment.created_at.desc())
)
completed_payments = result.scalars().all()
```

---

## Common Patterns

### Eager Loading Relationships

```python
from sqlalchemy.orm import selectinload

# Load user with all subscriptions
result = await session.execute(
    select(User)
    .options(selectinload(User.subscriptions))
    .where(User.id == user_id)
)
user = result.unique().scalar_one_or_none()
```

### Filtering with Relationships

```python
# Get users with active subscriptions
result = await session.execute(
    select(User)
    .join(Subscription)
    .where(Subscription.is_active == True)
    .distinct()
)
users = result.scalars().all()
```

### Aggregations

```python
from sqlalchemy import func

# Count jobs by status
result = await session.execute(
    select(Job.status, func.count(Job.id))
    .where(Job.user_id == user_id)
    .group_by(Job.status)
)
status_counts = result.all()
```

### Pagination

```python
from sqlalchemy import desc

skip = 0
limit = 20

result = await session.execute(
    select(Payment)
    .where(Payment.user_id == user_id)
    .order_by(desc(Payment.created_at))
    .offset(skip)
    .limit(limit)
)
payments = result.scalars().all()
```

---

## Migration Commands

```bash
# Generate automatic migration from model changes
alembic revision --autogenerate -m "Add column to users"

# Create empty migration
alembic revision -m "Description"

# Apply migrations
alembic upgrade head

# Revert migrations
alembic downgrade -1

# Check current version
alembic current

# View history
alembic history
```

---

## Best Practices

1. ✅ Always use UUID for primary keys (except Plan which uses Integer)
2. ✅ Include timestamps (created_at, updated_at) on all models
3. ✅ Use foreign key constraints with appropriate ondelete policies
4. ✅ Use partial indexes for conditional queries
5. ✅ Use composite indexes for multi-column WHERE clauses
6. ✅ Validate data with Pydantic before database operations
7. ✅ Use async/await patterns consistently
8. ✅ Commit transactions explicitly with `await session.commit()`
9. ✅ Use connection pooling for production
10. ✅ Test migrations before deploying to production
