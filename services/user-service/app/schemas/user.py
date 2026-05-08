import re
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from ..models.user import (
    KYCDocumentStatus,
    KYCDocumentType,
    KYCStatus,
    LanguagePreference,
    TradingMode,
    UserRole,
)


# ── Auth Schemas ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User / Profile Schemas ────────────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    date_of_birth: Optional[date] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole
    trading_mode: TradingMode
    kyc_status: KYCStatus
    language_preference: LanguagePreference
    is_active: bool
    created_at: datetime
    profile: Optional[UserProfileResponse] = None


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    date_of_birth: Optional[date] = None
    language_preference: Optional[LanguagePreference] = None


class KYCDocumentSubmitRequest(BaseModel):
    document_type: KYCDocumentType
    file_reference: str


class KYCSubmitRequest(BaseModel):
    documents: list[KYCDocumentSubmitRequest]

    @field_validator("documents")
    @classmethod
    def require_documents(cls, v: list[KYCDocumentSubmitRequest]) -> list[KYCDocumentSubmitRequest]:
        if len(v) == 0:
            raise ValueError("At least one KYC document is required.")
        return v


class KYCStatusResponse(BaseModel):
    kyc_status: KYCStatus


class KYCDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_type: KYCDocumentType
    file_reference: str
    verification_status: KYCDocumentStatus
    created_at: datetime


class KYCSubmissionResponse(BaseModel):
    message: str
    kyc_status: KYCStatus
    submitted_documents: int


# ── Partner Schemas ───────────────────────────────────────────────────────────

class ReferredUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole
    trading_mode: TradingMode
    kyc_status: KYCStatus
    is_active: bool
    created_at: datetime


class CommissionEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    referred_user_id: UUID
    trade_reference: Optional[str] = None
    commission_amount: float
    commission_rate: float
    description: Optional[str] = None
    created_at: datetime


class PartnerPermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    permission: str
    granted_at: datetime
