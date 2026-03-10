# Database Schema Reference Card

## Complete Schema Overview

### Table: users
```
Column              | Type              | Nullable | Constraints
--------------------|-------------------|----------|------------------
id                  | UUID              | NO       | PK, DEFAULT gen_random_uuid()
email              | VARCHAR(255)      | NO       | UNIQUE (uq_users_email)
phone_number       | VARCHAR(20)       | YES      | 
password_hash      | VARCHAR(255)      | NO       | 
full_name          | VARCHAR(255)      | YES      | 
is_active          | BOOLEAN           | NO       | DEFAULT true
is_verified        | BOOLEAN           | NO       | DEFAULT false
created_at         | TIMESTAMP TZ      | NO       | DEFAULT now()
updated_at         | TIMESTAMP TZ      | NO       | DEFAULT now()

Indexes:
- PK: id
- UNIQUE: email (uq_users_email)
- BTREE: email (idx_users_email)

Foreign Keys: None (parent table)
```

### Table: plans
```
Column              | Type              | Nullable | Constraints
--------------------|-------------------|----------|------------------
id                  | INTEGER           | NO       | PK
name               | VARCHAR(50)       | NO       | UNIQUE
description        | TEXT              | YES      | 
price_egp          | NUMERIC(10,2)     | NO       | 
max_files_per_month| INTEGER           | NO       | -1 = unlimited
max_file_size_mb   | INTEGER           | NO       | 
rate_limit_per_hour| INTEGER           | YES      | -1 = unlimited
created_at         | TIMESTAMP TZ      | NO       | DEFAULT now()

Indexes:
- PK: id
- UNIQUE: name

Foreign Keys: None (parent table)

Default Data:
- ID 1: free, 0 EGP, 1 file/month, 2 MB
- ID 2: hourly, 7.50 EGP, 3 files/month, 5 MB, 60 req/hr
- ID 3: monthly, 69 EGP, unlimited files, 5 MB
```

### Table: subscriptions
```
Column              | Type              | Nullable | Constraints
--------------------|-------------------|----------|------------------
id                  | UUID              | NO       | PK, DEFAULT gen_random_uuid()
user_id            | UUID              | NO       | FK → users.id (CASCADE)
plan_id            | INTEGER           | NO       | FK → plans.id (RESTRICT)
is_active          | BOOLEAN           | NO       | DEFAULT true
expires_at         | TIMESTAMP TZ      | YES      | 
created_at         | TIMESTAMP TZ      | NO       | DEFAULT now()
updated_at         | TIMESTAMP TZ      | NO       | DEFAULT now()

Indexes:
- PK: id
- COMPOSITE: (user_id, is_active) idx_subscriptions_user_id_is_active
- PARTIAL: expires_at WHERE is_active=true (idx_subscriptions_expires_at_partial)

Foreign Keys:
- user_id → users.id (ON DELETE CASCADE)
- plan_id → plans.id (ON DELETE RESTRICT)
```

### Table: sessions
```
Column              | Type              | Nullable | Constraints
--------------------|-------------------|----------|------------------
id                  | UUID              | NO       | PK, DEFAULT gen_random_uuid()
user_id            | UUID              | NO       | FK → users.id (CASCADE)
token              | VARCHAR(500)      | NO       | UNIQUE
user_agent         | VARCHAR(255)      | YES      | 
ip_address         | VARCHAR(45)       | YES      | IPv4 or IPv6
expires_at         | TIMESTAMP TZ      | NO       | 
created_at         | TIMESTAMP TZ      | NO       | DEFAULT now()

Indexes:
- PK: id
- UNIQUE: token
- COMPOSITE: (user_id, expires_at) idx_sessions_user_id_expires_at
- BTREE: token (idx_sessions_token)

Foreign Keys:
- user_id → users.id (ON DELETE CASCADE)
```

### Table: jobs
```
Column              | Type              | Nullable | Constraints
--------------------|-------------------|----------|------------------
id                  | UUID              | NO       | PK, DEFAULT gen_random_uuid()
user_id            | UUID              | NO       | FK → users.id (CASCADE)
status             | VARCHAR(20)       | NO       | DEFAULT 'queued'
job_type           | VARCHAR(50)       | NO       | convert, merge, split, etc.
input_file_path    | VARCHAR(500)      | NO       | S3 or local path
output_file_path   | VARCHAR(500)      | YES      | S3 or local path
error_message      | TEXT              | YES      | 
created_at         | TIMESTAMP TZ      | NO       | DEFAULT now()
started_at         | TIMESTAMP TZ      | YES      | 
completed_at       | TIMESTAMP TZ      | YES      | 

Indexes:
- PK: id
- COMPOSITE: (user_id, created_at DESC) idx_jobs_user_id_created_at_desc
- PARTIAL: status WHERE status IN ('queued','processing') idx_jobs_status_partial

Foreign Keys:
- user_id → users.id (ON DELETE CASCADE)

Status values: queued, processing, completed, failed
```

### Table: payments
```
Column              | Type              | Nullable | Constraints
--------------------|-------------------|----------|------------------
id                  | UUID              | NO       | PK, DEFAULT gen_random_uuid()
user_id            | UUID              | NO       | FK → users.id (CASCADE)
amount_egp         | NUMERIC(10,2)     | NO       | 
status             | VARCHAR(20)       | NO       | DEFAULT 'pending'
gateway_ref        | VARCHAR(255)      | YES      | UNIQUE (uq_payments_gateway_ref)
payment_method     | VARCHAR(50)       | NO       | credit_card, bank_transfer, wallet
description        | TEXT              | YES      | 
created_at         | TIMESTAMP TZ      | NO       | DEFAULT now()
updated_at         | TIMESTAMP TZ      | NO       | DEFAULT now()

Indexes:
- PK: id
- UNIQUE: gateway_ref (uq_payments_gateway_ref)
- COMPOSITE: (user_id, created_at DESC) idx_payments_user_id_created_at_desc

Foreign Keys:
- user_id → users.id (ON DELETE CASCADE)

Status values: pending, completed, failed, refunded
```

## Index Summary

### Unique Indexes (2)
1. `uq_users_email` on `users(email)`
2. `uq_payments_gateway_ref` on `payments(gateway_ref)`

### Composite Indexes (4)
1. `idx_subscriptions_user_id_is_active` on `subscriptions(user_id, is_active)`
2. `idx_sessions_user_id_expires_at` on `sessions(user_id, expires_at)`
3. `idx_jobs_user_id_created_at_desc` on `jobs(user_id, created_at DESC)`
4. `idx_payments_user_id_created_at_desc` on `payments(user_id, created_at DESC)`

### Partial Indexes (2)
1. `idx_subscriptions_expires_at_partial` on `subscriptions(expires_at)` WHERE `is_active = true`
2. `idx_jobs_status_partial` on `jobs(status)` WHERE `status IN ('queued', 'processing')`

### Other Indexes (1)
1. `idx_sessions_token` on `sessions(token)` - For token lookups

## Data Types Used

| Type | Usage | Example |
|------|-------|---------|
| UUID | Primary keys, relationships | id, user_id |
| INTEGER | Plan IDs, limits | max_files_per_month |
| VARCHAR(n) | Short text | email, phone_number, names |
| TEXT | Long text | description, error_message |
| NUMERIC(10,2) | Prices | 69.00, 7.50 |
| BOOLEAN | Flags | is_active, is_verified |
| TIMESTAMP TZ | Events | created_at, expires_at |

## Constraints

### Primary Key Constraints
- `users.id`, `plans.id`, `subscriptions.id`, `sessions.id`, `jobs.id`, `payments.id`

### Unique Constraints
- `users.email` (uq_users_email)
- `plans.name`
- `sessions.token`
- `payments.gateway_ref` (uq_payments_gateway_ref)

### Foreign Key Constraints
- `subscriptions.user_id` → `users.id` (ON DELETE CASCADE)
- `subscriptions.plan_id` → `plans.id` (ON DELETE RESTRICT)
- `sessions.user_id` → `users.id` (ON DELETE CASCADE)
- `jobs.user_id` → `users.id` (ON DELETE CASCADE)
- `payments.user_id` → `users.id` (ON DELETE CASCADE)

### NOT NULL Constraints
- See column definitions above

### DEFAULT Constraints
- See column definitions above

## Relationships

```
User (1) ──────M──── Subscription ──────N── Plan
  │
  ├─────M─────→ Session
  ├─────M─────→ Job
  └─────M─────→ Payment
```

## Query Optimization Tips

1. **Active subscriptions**: Use index `idx_subscriptions_user_id_is_active`
2. **User's recent jobs**: Use index `idx_jobs_user_id_created_at_desc`
3. **Pending jobs**: Use partial index `idx_jobs_status_partial`
4. **User payments**: Use index `idx_payments_user_id_created_at_desc`
5. **Active sessions**: Use index `idx_sessions_user_id_expires_at`
6. **Email lookup**: Use unique index `uq_users_email`
7. **Payment verification**: Use unique index `uq_payments_gateway_ref`

## Migration Timeline

- **v1** (001_create_tables.py): Create all 6 tables with 9 indexes
- **v2** (002_seed_plans.py): Insert 3 default plans

## Environment Variables

```bash
# Required
POSTGRES_DSN=postgresql+asyncpg://user:password@host:port/database

# Optional
SQL_ECHO=false  # Set to 'true' to log SQL queries
```

## Connection Pool Settings

```python
pool_size=10           # Base connections
max_overflow=20        # Additional connections
pool_pre_ping=True     # Test connections
pool_recycle=3600      # Recycle after 1 hour
```
