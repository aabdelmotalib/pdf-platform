# Database Setup Guide

## Overview

This guide covers the PostgreSQL database setup, SQLAlchemy ORM models, Alembic migrations, and Pydantic schemas for the PDF Platform.

## Architecture

### Table Structure

The database includes 6 main tables:

1. **users** - User accounts and authentication
2. **plans** - Subscription plan definitions
3. **subscriptions** - User subscription records
4. **sessions** - User session tokens
5. **jobs** - PDF processing jobs
6. **payments** - Payment records

### Database Schema

```
users (UUID PK)
├── email (unique)
├── phone_number
├── password_hash
├── full_name
├── is_active
├── is_verified
└── timestamps

plans (Integer PK)
├── name (unique)
├── description
├── price_egp
├── max_files_per_month
├── max_file_size_mb
└── rate_limit_per_hour

subscriptions (UUID PK)
├── user_id (FK) → users.id
├── plan_id (FK) → plans.id
├── is_active
├── expires_at
└── timestamps

sessions (UUID PK)
├── user_id (FK) → users.id
├── token (unique)
├── user_agent
├── ip_address
├── expires_at
└── created_at

jobs (UUID PK)
├── user_id (FK) → users.id
├── status
├── job_type
├── input_file_path
├── output_file_path
├── error_message
└── timestamps

payments (UUID PK)
├── user_id (FK) → users.id
├── amount_egp
├── status
├── gateway_ref (unique)
├── payment_method
├── description
└── timestamps
```

## Indexes

### Unique Indexes
- `uq_users_email` - On users.email
- `uq_payments_gateway_ref` - On payments.gateway_ref

### Composite Indexes
- `idx_subscriptions_user_id_is_active` - On subscriptions(user_id, is_active)
- `idx_sessions_user_id_expires_at` - On sessions(user_id, expires_at)
- `idx_jobs_user_id_created_at_desc` - On jobs(user_id, created_at DESC)
- `idx_payments_user_id_created_at_desc` - On payments(user_id, created_at DESC)

### Partial Indexes
- `idx_subscriptions_expires_at_partial` - On subscriptions(expires_at) WHERE is_active = true
- `idx_jobs_status_partial` - On jobs(status) WHERE status IN ('queued', 'processing')

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# PostgreSQL connection (default for local development)
POSTGRES_DSN=postgresql+asyncpg://postgres:password@localhost:5432/pdf_platform

# Enable SQL query logging (optional)
SQL_ECHO=false
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Ensure these key packages are installed:
- `sqlalchemy>=2.0.23` - ORM
- `alembic>=1.13.0` - Migrations
- `asyncpg` - PostgreSQL async driver
- `pydantic>=2.5.0` - Data validation

### 3. Initialize Database

```bash
# Create database (if not exists)
createdb pdf_platform

# Run all migrations (including seed data)
alembic upgrade head
```

### 4. Verify Setup

```bash
# Check migration status
alembic current

# List all applied migrations
alembic history
```

## Working with Migrations

### Running Migrations

```bash
# Upgrade to latest version
cd api
alembic upgrade head

# Upgrade by specific steps
alembic upgrade +2

# Downgrade to previous version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade 001_create_tables
```

### Creating New Migrations

#### Auto-generate migration from model changes

```bash
cd api
alembic revision --autogenerate -m "Description of changes"
```

#### Manual migration

```bash
cd api
alembic revision -m "Description of changes"
```

Then edit the generated file in `alembic/versions/` with your SQL.

### Migration Files

- `001_create_tables.py` - Initial schema with all tables and indexes
- `002_seed_plans.py` - Seed default subscription plans

## Database Models

### Location
- **Models**: `api/db/models.py`
- **Engine**: `api/db/engine.py`

### Using Models in Code

```python
from sqlalchemy import select
from db import AsyncSessionLocal, User

async def get_user(user_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

### Async Session Usage

```python
from fastapi import Depends
from db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def endpoint(db: AsyncSession = Depends(get_db)):
    # Use db session
    result = await db.execute(select(User))
    users = result.scalars().all()
```

## Pydantic Schemas

### Location
- **Schemas**: `api/schemas/__init__.py`

### Schema Types

Each model has corresponding schemas:

- **Base**: Common fields (e.g., `UserBase`)
- **Create**: For POST requests (e.g., `UserCreate`)
- **Update**: For PATCH/PUT requests (e.g., `UserUpdate`)
- **Response**: For API responses (e.g., `UserResponse`)
- **Complex**: Nested data (e.g., `UserWithSubscriptions`)

### Example Usage

```python
from fastapi import FastAPI
from schemas import UserCreate, UserResponse

app = FastAPI()

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

## Default Plans

Seed data includes 3 default plans:

1. **Free** (ID: 1)
   - Price: 0 EGP
   - Max files: 1/month
   - Max file size: 2 MB
   - Rate limit: None

2. **Hourly** (ID: 2)
   - Price: 7.50 EGP
   - Max files: 3/month
   - Max file size: 5 MB
   - Rate limit: 60 requests/hour
   - Expires: 1 hour from creation

3. **Monthly** (ID: 3)
   - Price: 69 EGP
   - Max files: Unlimited
   - Max file size: 5 MB
   - Rate limit: None
   - Expires: 30 days from creation

## Async Engine Configuration

The database engine is configured for async operations using asyncpg:

```python
# api/db/engine.py

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### Configuration Options

- `pool_size=10` - Number of connections to keep in pool
- `max_overflow=20` - Additional connections above pool_size
- `pool_pre_ping=True` - Test connections before using
- `pool_recycle=3600` - Recycle connections after 1 hour

## Common Queries

### Get user with active subscription

```python
from sqlalchemy import select
from db import User, Subscription

result = await session.execute(
    select(User).join(Subscription).where(
        (Subscription.is_active == True) & 
        (User.id == user_id)
    )
)
user = result.scalar_one_or_none()
```

### Get active jobs for user

```python
from db import Job

result = await session.execute(
    select(Job).where(
        (Job.user_id == user_id) & 
        (Job.status.in_(["queued", "processing"]))
    )
)
jobs = result.scalars().all()
```

### Get paginated users

```python
skip = 0
limit = 10

result = await session.execute(
    select(User).offset(skip).limit(limit)
)
users = result.scalars().all()
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
psql postgresql://user:password@localhost:5432/pdf_platform

# Check environment variable
echo $POSTGRES_DSN
```

### Migration Issues

```bash
# Check current migration state
alembic current

# Reset database (caution: destructive)
alembic downgrade base
alembic upgrade head
```

### Performance Tips

1. Use indexes on frequently queried columns
2. Use partial indexes for filtered queries
3. Batch operations when inserting many records
4. Use `select()` instead of deprecated `.query()` method
5. Set appropriate pool sizing based on application needs

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
