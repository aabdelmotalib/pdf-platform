"""
SQLAlchemy ORM models for PDF Platform.

Tables:
- users: User accounts with authentication
- plans: Subscription plans
- subscriptions: User subscription records  
- sessions: User sessions for auth tokens
- jobs: PDF processing jobs
- payments: Payment records
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship

# Base class for all models
Base = declarative_base()


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(20), server_default="user", default="user", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("idx_users_email", "email"),
    )


class Plan(Base):
    """Subscription plan model."""
    
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    price_egp = Column(Numeric(10, 2), nullable=False)
    max_files_per_month = Column(Integer, nullable=False)  # -1 for unlimited
    max_file_size_mb = Column(Integer, nullable=False)
    rate_limit_per_hour = Column(Integer, nullable=True)  # -1 for unlimited
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")


class Subscription(Base):
    """User subscription to a plan."""
    
    __tablename__ = "subscriptions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    
    # Indexes
    __table_args__ = (
        Index("idx_subscriptions_user_id_is_active", "user_id", "is_active"),
        Index(
            "idx_subscriptions_expires_at_partial",
            "expires_at",
            postgresql_where=(is_active == True),  # Partial index
        ),
    )


class Session(Base):
    """User session for authentication tokens."""
    
    __tablename__ = "sessions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index("idx_sessions_user_id_expires_at", "user_id", "expires_at"),
        Index("idx_sessions_token", "token"),
    )


class Job(Base):
    """PDF processing job."""
    
    __tablename__ = "jobs"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(
        String(20),
        default="queued",
        nullable=False,
    )  # queued, processing, completed, failed
    job_type = Column(String(50), nullable=False)  # convert, merge, split, etc.
    input_file_path = Column(String(500), nullable=False)
    output_file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    
    # Indexes
    __table_args__ = (
        Index("idx_jobs_user_id_created_at_desc", "user_id", "created_at"),
        Index(
            "idx_jobs_status_partial",
            "status",
            postgresql_where=(status.in_(["queued", "processing"])),  # Partial index
        ),
    )


class Payment(Base):
    """Payment record."""
    
    __tablename__ = "payments"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    amount_egp = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, completed, failed, refunded
    gateway_ref = Column(String(255), nullable=True)  # External payment gateway reference
    payment_method = Column(String(50), nullable=False)  # credit_card, bank_transfer, wallet
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint("gateway_ref", name="uq_payments_gateway_ref"),
        Index("idx_payments_user_id_created_at_desc", "user_id", "created_at"),
    )
