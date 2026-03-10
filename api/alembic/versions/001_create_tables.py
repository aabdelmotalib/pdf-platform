"""Initial migration: Create all tables with indexes

Revision ID: 001_create_tables
Revises: 
Create Date: 2026-03-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "001_create_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    
    # Create plans table
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_egp", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_files_per_month", sa.Integer(), nullable=False),
        sa.Column("max_file_size_mb", sa.Integer(), nullable=False),
        sa.Column("rate_limit_per_hour", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    
    # Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_subscriptions_user_id_is_active", "subscriptions", ["user_id", "is_active"])
    op.create_index(
        "idx_subscriptions_expires_at_partial",
        "subscriptions",
        ["expires_at"],
        postgresql_where=sa.text("is_active = true"),
    )
    
    # Create sessions table
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(500), nullable=False),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("idx_sessions_user_id_expires_at", "sessions", ["user_id", "expires_at"])
    op.create_index("idx_sessions_token", "sessions", ["token"])
    
    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="queued", nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("input_file_path", sa.String(500), nullable=False),
        sa.Column("output_file_path", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_jobs_user_id_created_at_desc", "jobs", ["user_id", "created_at"], postgresql_using="btree")
    op.create_index(
        "idx_jobs_status_partial",
        "jobs",
        ["status"],
        postgresql_where=sa.text("status IN ('queued', 'processing')"),
    )
    
    # Create payments table
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_egp", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("gateway_ref", sa.String(255), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gateway_ref", name="uq_payments_gateway_ref"),
    )
    op.create_index("idx_payments_user_id_created_at_desc", "payments", ["user_id", "created_at"])


def downgrade() -> None:
    # Drop payments table
    op.drop_index("idx_payments_user_id_created_at_desc", table_name="payments")
    op.drop_table("payments")
    
    # Drop jobs table
    op.drop_index("idx_jobs_status_partial", table_name="jobs")
    op.drop_index("idx_jobs_user_id_created_at_desc", table_name="jobs")
    op.drop_table("jobs")
    
    # Drop sessions table
    op.drop_index("idx_sessions_token", table_name="sessions")
    op.drop_index("idx_sessions_user_id_expires_at", table_name="sessions")
    op.drop_table("sessions")
    
    # Drop subscriptions table
    op.drop_index("idx_subscriptions_expires_at_partial", table_name="subscriptions")
    op.drop_index("idx_subscriptions_user_id_is_active", table_name="subscriptions")
    op.drop_table("subscriptions")
    
    # Drop plans table
    op.drop_table("plans")
    
    # Drop users table
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
