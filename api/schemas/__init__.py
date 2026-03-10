"""Pydantic v2 schemas for all database models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """User creation request schema."""
    
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")


class UserUpdate(BaseModel):
    """User update request schema."""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """User response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Plan Schemas
# ============================================================================

class PlanBase(BaseModel):
    """Base plan schema."""
    
    name: str = Field(..., max_length=50)
    description: Optional[str] = None
    price_egp: Decimal = Field(..., decimal_places=2, max_digits=10)
    max_files_per_month: int = Field(..., description="-1 for unlimited")
    max_file_size_mb: int
    rate_limit_per_hour: Optional[int] = Field(None, description="-1 for unlimited")


class PlanCreate(PlanBase):
    """Plan creation request schema."""
    pass


class PlanResponse(PlanBase):
    """Plan response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    
    plan_id: int
    is_active: bool = True


class SubscriptionCreate(SubscriptionBase):
    """Subscription creation request schema."""
    pass


class SubscriptionUpdate(BaseModel):
    """Subscription update request schema."""
    
    is_active: Optional[bool] = None
    plan_id: Optional[int] = None


class SubscriptionResponse(SubscriptionBase):
    """Subscription response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class SubscriptionWithPlan(SubscriptionResponse):
    """Subscription response with nested plan data."""
    
    plan: PlanResponse


# ============================================================================
# Session Schemas
# ============================================================================

class SessionBase(BaseModel):
    """Base session schema."""
    
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class SessionCreate(BaseModel):
    """Session creation request schema."""
    
    token: str
    expires_at: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class SessionResponse(SessionBase):
    """Session response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    token: str = Field(..., description="Authentication token")
    expires_at: datetime
    created_at: datetime


class SessionPublicResponse(BaseModel):
    """Session response without sensitive token data (for lists)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_agent: Optional[str]
    ip_address: Optional[str]
    expires_at: datetime
    created_at: datetime


# ============================================================================
# Job Schemas
# ============================================================================

class JobBase(BaseModel):
    """Base job schema."""
    
    job_type: str = Field(..., max_length=50)
    input_file_path: str
    status: str = Field(default="queued", description="queued, processing, completed, failed")


class JobCreate(BaseModel):
    """Job creation request schema."""
    
    job_type: str = Field(..., max_length=50)
    input_file_path: str


class JobUpdate(BaseModel):
    """Job update request schema."""
    
    status: Optional[str] = None
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobResponse(JobBase):
    """Job response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    output_file_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


# ============================================================================
# Payment Schemas
# ============================================================================

class PaymentBase(BaseModel):
    """Base payment schema."""
    
    amount_egp: Decimal = Field(..., decimal_places=2, max_digits=10)
    payment_method: str = Field(..., description="credit_card, bank_transfer, wallet")
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Payment creation request schema."""
    pass


class PaymentUpdate(BaseModel):
    """Payment update request schema."""
    
    status: Optional[str] = None
    gateway_ref: Optional[str] = None


class PaymentResponse(PaymentBase):
    """Payment response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    status: str = Field(default="pending", description="pending, completed, failed, refunded")
    gateway_ref: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Complex/Nested Schemas
# ============================================================================

class UserWithSubscriptions(UserResponse):
    """User response with subscription details."""
    
    subscriptions: list[SubscriptionWithPlan] = []


class UserWithSessions(UserResponse):
    """User response with session details."""
    
    sessions: list[SessionPublicResponse] = []


class UserWithJobs(UserResponse):
    """User response with job details."""
    
    jobs: list[JobResponse] = []


class UserWithPayments(UserResponse):
    """User response with payment details."""
    
    payments: list[PaymentResponse] = []

# ============================================================================
# Upload/File Schemas
# ============================================================================

class UploadRequest(BaseModel):
    """File upload request schema."""
    
    # File will be sent as multipart FormData, not in JSON


class UploadResponse(BaseModel):
    """File upload response with job details."""
    
    job_id: UUID
    status: str = Field(default="queued", description="Job status")
    message: str = Field(default="File queued for processing", description="Status message")
    
    model_config = ConfigDict(from_attributes=True)


class JobStatusResponse(BaseModel):
    """Job status response with progress and download URL."""
    
    job_id: UUID
    status: str = Field(description="Job status: queued, processing, completed, failed")
    progress: int = Field(default=0, description="Progress percentage (0-100)")
    error_message: Optional[str] = None
    input_file_path: Optional[str] = None
    output_file_path: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class FileValidationError(BaseModel):
    """File validation error response."""
    
    error: str
    detail: str
    code: str