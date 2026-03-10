# Quick Start: Database Setup

## Files Created

### Database Models & Configuration
- `api/db/__init__.py` - Database package exports
- `api/db/models.py` - SQLAlchemy ORM models (6 tables)
- `api/db/engine.py` - Async engine and session configuration

### Alembic Migrations
- `api/alembic.ini` - Alembic configuration
- `api/alembic/env.py` - Alembic environment setup
- `api/alembic/script.py.mako` - Alembic migration template
- `api/alembic/__init__.py` - Package marker
- `api/alembic/versions/__init__.py` - Versions package marker
- `api/alembic/versions/001_create_tables.py` - Initial schema migration
- `api/alembic/versions/002_seed_plans.py` - Seed data migration

### Pydantic Schemas
- `api/schemas/__init__.py` - All request/response DTOs

### Updated Files
- `api/main.py` - Integrated database lifespan

### Documentation
- `DATABASE_SETUP.md` - Complete database setup guide
- `MODELS_REFERENCE.md` - SQLAlchemy models reference
- `SCHEMAS_REFERENCE.md` - Pydantic schemas reference
- `QUICK_START_DB.md` - This file

## Database Schema Summary

### Tables (6)
1. **users** - User accounts with UUID PK
2. **plans** - Subscription plans (3 default)
3. **subscriptions** - User subscriptions
4. **sessions** - authentication tokens
5. **jobs** - PDF processing jobs
6. **payments** - Payment records

### Indexes (9)
- 2 Unique indexes: users.email, payments.gateway_ref
- 4 Composite indexes
- 2 Partial indexes

## Setup Steps

### 1. Database URL Configuration

Set `POSTGRES_DSN` in `.env`:
```bash
POSTGRES_DSN=postgresql+asyncpg://postgres:password@localhost:5432/pdf_platform
```

Or use default for local development:
```bash
# Default: postgresql+asyncpg://postgres:postgres@localhost:5432/pdf_platform
```

### 2. Run Migrations

```bash
cd api

# Apply all migrations (creates tables + seeds plans)
alembic upgrade head
```

### 3. Verify Setup

```bash
# Check current migration
alembic current

# Start server
python3 main.py
```

## Using Database in Code

### Example: Create User

```python
from sqlalchemy import select
from db import AsyncSessionLocal, User
from schemas import UserCreate

async def create_user(user_data: UserCreate):
    async with AsyncSessionLocal() as session:
        db_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user
```

### Example: FastAPI Endpoint

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db
from schemas import UserResponse

app = FastAPI()

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.model_dump(exclude={'password'}))
    session.add(db_user)
    await session.commit()
    return db_user
```

## Migrations

### Apply Latest
```bash
cd api
alembic upgrade head
```

### Rollback One
```bash
alembic downgrade -1
```

### Create New Migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

## Key Features

✅ **UUID Primary Keys** - All tables use UUID PK (except Plan)  
✅ **Foreign Keys** - Proper relationships with CASCADE deletes  
✅ **Composite Indexes** - Optimized for multi-column queries  
✅ **Partial Indexes** - Efficient filtered queries  
✅ **Async Support** - Using asyncpg driver  
✅ **Connection Pooling** - Production-ready configuration  
✅ **Seed Data** - 3 default plans pre-loaded  
✅ **Type Safety** - Full Pydantic validation  

## Default Plans

| Plan | Price | Files | Size | Rate Limit |
|------|-------|-------|------|-----------|
| Free | 0 EGP | 1 | 2 MB | - |
| Hourly | 7.50 EGP | 3 | 5 MB | 60/hr |
| Monthly | 69 EGP | ∞ | 5 MB | - |

## Troubleshooting

### Connection Error
```bash
# Verify PostgreSQL is running
psql postgresql://user:password@localhost:5432/pdf_platform

# Check environment variable
echo $POSTGRES_DSN
```

### Migration Issues
```bash
# Check current status
alembic current

# Reset (careful!)
alembic downgrade base
alembic upgrade head
```

### Import Errors
```bash
# Install required packages
pip install -r requirements.txt

# Verify SQLAlchemy
python3 -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

## Files by Category

### Models
- Models: `api/db/models.py`
- Engine: `api/db/engine.py`
- Schemas: `api/schemas/__init__.py`

### Migrations
- Config: `api/alembic.ini`
- Environment: `api/alembic/env.py`
- Versions: `api/alembic/versions/`

### Documentation
- Full setup: `DATABASE_SETUP.md`
- Models reference: `MODELS_REFERENCE.md`
- Schemas reference: `SCHEMAS_REFERENCE.md`

## Next Steps

1. ✅ Database schema created
2. ✅ Migrations configured
3. ✅ Schemas defined
4. → Create API endpoints using models
5. → Add business logic and validation
6. → Set up authentication
7. → Implement PDF processing jobs

## Support

For detailed information:
- **Setup & Configuration**: See `DATABASE_SETUP.md`
- **Models & Relationships**: See `MODELS_REFERENCE.md`
- **Request/Response formats**: See `SCHEMAS_REFERENCE.md`
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Pydantic v2**: https://docs.pydantic.dev/
