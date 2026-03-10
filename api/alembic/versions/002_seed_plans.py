"""Seed migration: Insert default subscription plans

Revision ID: 002_seed_plans
Revises: 001_create_tables
Create Date: 2026-03-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002_seed_plans"
down_revision = "001_create_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Insert the 3 default subscription plans."""
    plans_table = sa.table(
        "plans",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("price_egp", sa.Numeric),
        sa.column("max_files_per_month", sa.Integer),
        sa.column("max_file_size_mb", sa.Integer),
        sa.column("rate_limit_per_hour", sa.Integer),
    )
    
    op.bulk_insert(
        plans_table,
        [
            {
                "id": 1,
                "name": "free",
                "description": "Free plan with basic features",
                "price_egp": 0.00,
                "max_files_per_month": 1,
                "max_file_size_mb": 2,
                "rate_limit_per_hour": None,
            },
            {
                "id": 2,
                "name": "hourly",
                "description": "Hourly subscription plan (expires after 1 hour)",
                "price_egp": 7.50,
                "max_files_per_month": 3,
                "max_file_size_mb": 5,
                "rate_limit_per_hour": 60,
            },
            {
                "id": 3,
                "name": "monthly",
                "description": "Monthly subscription plan (expires after 30 days)",
                "price_egp": 69.00,
                "max_files_per_month": -1,  # unlimited
                "max_file_size_mb": 5,
                "rate_limit_per_hour": None,
            },
        ],
    )


def downgrade() -> None:
    """Remove the default subscription plans."""
    op.execute(sa.text("DELETE FROM plans WHERE id IN (1, 2, 3)"))
