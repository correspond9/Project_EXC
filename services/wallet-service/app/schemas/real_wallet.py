"""Pydantic schemas for real-wallet endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from ..models.real_wallet import LedgerTxType, WithdrawalStatus


# ── Real Wallet ──────────────────────────────────────────────────────────────

class RealWalletResponse(BaseModel):
    id: uuid.UUID
    currency: str
    balance: Decimal
    locked_balance: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Deposit Address ───────────────────────────────────────────────────────────

class DepositAddressResponse(BaseModel):
    id: uuid.UUID
    currency: str
    network: str
    address: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignDepositAddressRequest(BaseModel):
    user_id: uuid.UUID
    currency: str = Field(..., max_length=10)
    network: str = Field(..., max_length=20)
    address: str = Field(..., max_length=200)


# ── Withdrawal ────────────────────────────────────────────────────────────────

class WithdrawRequest(BaseModel):
    currency: str = Field(..., max_length=10)
    amount: Decimal = Field(..., gt=0)
    destination_address: str = Field(..., max_length=200)
    network: str = Field(..., max_length=20)


class WithdrawalResponse(BaseModel):
    id: uuid.UUID
    currency: str
    amount: Decimal
    destination_address: str
    network: str
    status: WithdrawalStatus
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminWithdrawalResponse(WithdrawalResponse):
    user_id: uuid.UUID


class RejectWithdrawalRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


# ── Deposit (admin records incoming deposit) ──────────────────────────────────

class ConfirmDepositRequest(BaseModel):
    user_id: uuid.UUID
    currency: str = Field(..., max_length=10)
    amount: Decimal = Field(..., gt=0)
    reference_id: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=500)


# ── Balance Ledger ────────────────────────────────────────────────────────────

class LedgerEntryResponse(BaseModel):
    id: uuid.UUID
    currency: str
    amount: Decimal
    balance_after: Decimal
    tx_type: LedgerTxType
    reference_id: str | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
