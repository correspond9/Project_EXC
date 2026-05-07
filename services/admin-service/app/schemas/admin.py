import uuid
from typing import Optional

from pydantic import BaseModel

from ..models.user import KYCStatus, TradingMode, UserRole


class UserSummary(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    trading_mode: TradingMode
    kyc_status: KYCStatus
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    users: list[UserSummary]


class UpdateTradingModeRequest(BaseModel):
    trading_mode: TradingMode


class UpdateUserStatusRequest(BaseModel):
    is_active: bool
