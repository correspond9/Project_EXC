"""Real wallet endpoints: user balance, deposits, withdrawals; admin management."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user_id, require_admin
from ..models.real_wallet import (
    BalanceLedger,
    DepositAddress,
    LedgerTxType,
    RealWallet,
    WithdrawalRequest,
    WithdrawalStatus,
)
from ..schemas.real_wallet import (
    AdminWithdrawalResponse,
    AssignDepositAddressRequest,
    ConfirmDepositRequest,
    DepositAddressResponse,
    LedgerEntryResponse,
    RejectWithdrawalRequest,
    RealWalletResponse,
    WithdrawRequest,
    WithdrawalResponse,
)

router = APIRouter(prefix="/api/wallet", tags=["Real Wallet"])
admin_router = APIRouter(prefix="/api/admin/wallet", tags=["Admin Real Wallet"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _require_live_kyc(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Raise 403 unless user has trading_mode=LIVE and kyc_status=APPROVED."""
    row = await db.execute(
        text("SELECT trading_mode, kyc_status FROM users WHERE id = :uid"),
        {"uid": str(user_id)},
    )
    user = row.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.kyc_status != "APPROVED":
        raise HTTPException(status_code=403, detail="KYC approval required for real wallet access")
    if user.trading_mode != "LIVE":
        raise HTTPException(status_code=403, detail="Switch to LIVE trading mode to access real wallet")


async def _get_or_create_wallet(
    db: AsyncSession, user_id: uuid.UUID, currency: str
) -> RealWallet:
    result = await db.execute(
        select(RealWallet).where(
            RealWallet.user_id == user_id, RealWallet.currency == currency
        )
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = RealWallet(user_id=user_id, currency=currency, balance=Decimal("0"), locked_balance=Decimal("0"))
        db.add(wallet)
        await db.flush()
    return wallet


# ── User endpoints ────────────────────────────────────────────────────────────

@router.get("/real", response_model=List[RealWalletResponse])
async def get_real_wallets(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return all real wallet balances. Requires LIVE mode + KYC approved."""
    await _require_live_kyc(user_id, db)
    result = await db.execute(
        select(RealWallet).where(RealWallet.user_id == user_id)
    )
    return result.scalars().all()


@router.get("/real/ledger", response_model=List[LedgerEntryResponse])
async def get_ledger(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return real wallet transaction history."""
    await _require_live_kyc(user_id, db)
    result = await db.execute(
        select(BalanceLedger)
        .where(BalanceLedger.user_id == user_id)
        .order_by(BalanceLedger.created_at.desc())
        .limit(200)
    )
    return result.scalars().all()


@router.get("/real/deposit-address/{currency}", response_model=List[DepositAddressResponse])
async def get_deposit_addresses(
    currency: str,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return deposit addresses assigned to the user for a currency."""
    await _require_live_kyc(user_id, db)
    result = await db.execute(
        select(DepositAddress).where(
            DepositAddress.user_id == user_id,
            DepositAddress.currency == currency.upper(),
        )
    )
    return result.scalars().all()


@router.post("/withdraw", response_model=WithdrawalResponse, status_code=status.HTTP_201_CREATED)
async def request_withdrawal(
    body: WithdrawRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit a withdrawal request. Funds are locked until admin approves/rejects."""
    await _require_live_kyc(user_id, db)
    currency = body.currency.upper()
    wallet = await _get_or_create_wallet(db, user_id, currency)
    available = Decimal(str(wallet.balance))
    if available < body.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Available: {available:.8f} {currency}",
        )
    # Lock funds
    wallet.balance = available - body.amount
    wallet.locked_balance = Decimal(str(wallet.locked_balance)) + body.amount

    wr = WithdrawalRequest(
        user_id=user_id,
        currency=currency,
        amount=body.amount,
        destination_address=body.destination_address,
        network=body.network.upper(),
        status=WithdrawalStatus.PENDING,
    )
    db.add(wr)
    await db.commit()
    await db.refresh(wr)
    return wr


@router.get("/withdraw", response_model=List[WithdrawalResponse])
async def list_withdrawals(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List the user's withdrawal requests."""
    await _require_live_kyc(user_id, db)
    result = await db.execute(
        select(WithdrawalRequest)
        .where(WithdrawalRequest.user_id == user_id)
        .order_by(WithdrawalRequest.created_at.desc())
    )
    return result.scalars().all()


# ── Admin endpoints ───────────────────────────────────────────────────────────

@admin_router.get("/withdrawals", response_model=List[AdminWithdrawalResponse])
async def admin_list_withdrawals(
    _admin: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str = "PENDING",
):
    """List withdrawal requests by status (default: PENDING)."""
    try:
        status_enum = WithdrawalStatus(status_filter.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    result = await db.execute(
        select(WithdrawalRequest)
        .where(WithdrawalRequest.status == status_enum)
        .order_by(WithdrawalRequest.created_at.asc())
    )
    return result.scalars().all()


@admin_router.post("/withdrawals/{withdrawal_id}/approve", response_model=AdminWithdrawalResponse)
async def approve_withdrawal(
    withdrawal_id: uuid.UUID,
    admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Approve a withdrawal. Releases locked funds as a debit and marks APPROVED."""
    result = await db.execute(
        select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id)
    )
    wr = result.scalar_one_or_none()
    if not wr:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")
    if wr.status != WithdrawalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot approve a {wr.status.value} request")

    wallet = await _get_or_create_wallet(db, wr.user_id, wr.currency)
    locked = Decimal(str(wallet.locked_balance))
    if locked < wr.amount:
        raise HTTPException(status_code=400, detail="Locked balance inconsistency — cannot approve")

    wallet.locked_balance = locked - wr.amount
    balance_after = Decimal(str(wallet.balance))

    # Append-only ledger entry
    entry = BalanceLedger(
        user_id=wr.user_id,
        currency=wr.currency,
        amount=-wr.amount,
        balance_after=balance_after,
        tx_type=LedgerTxType.WITHDRAWAL,
        reference_id=str(wr.id),
        note=f"Withdrawal to {wr.destination_address} ({wr.network}) approved by admin",
    )
    db.add(entry)
    wr.status = WithdrawalStatus.APPROVED
    wr.admin_user_id = admin_id
    await db.commit()
    await db.refresh(wr)
    return wr


@admin_router.post("/withdrawals/{withdrawal_id}/reject", response_model=AdminWithdrawalResponse)
async def reject_withdrawal(
    withdrawal_id: uuid.UUID,
    body: RejectWithdrawalRequest,
    admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reject a withdrawal. Returns locked funds to available balance."""
    result = await db.execute(
        select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id)
    )
    wr = result.scalar_one_or_none()
    if not wr:
        raise HTTPException(status_code=404, detail="Withdrawal request not found")
    if wr.status != WithdrawalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot reject a {wr.status.value} request")

    wallet = await _get_or_create_wallet(db, wr.user_id, wr.currency)
    wallet.locked_balance = Decimal(str(wallet.locked_balance)) - wr.amount
    wallet.balance = Decimal(str(wallet.balance)) + wr.amount

    wr.status = WithdrawalStatus.REJECTED
    wr.admin_user_id = admin_id
    wr.rejection_reason = body.reason
    await db.commit()
    await db.refresh(wr)
    return wr


@admin_router.post("/deposit-address", response_model=DepositAddressResponse, status_code=status.HTTP_201_CREATED)
async def assign_deposit_address(
    body: AssignDepositAddressRequest,
    admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Assign a deposit address to a user for a given currency/network."""
    currency = body.currency.upper()
    network = body.network.upper()
    # Check for existing
    existing = await db.execute(
        select(DepositAddress).where(
            DepositAddress.user_id == body.user_id,
            DepositAddress.currency == currency,
            DepositAddress.network == network,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail=f"Deposit address for {currency}/{network} already assigned"
        )
    addr = DepositAddress(
        user_id=body.user_id,
        currency=currency,
        network=network,
        address=body.address,
        assigned_by=admin_id,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


@admin_router.post("/confirm-deposit", status_code=status.HTTP_201_CREATED)
async def confirm_deposit(
    body: ConfirmDepositRequest,
    admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Record an incoming deposit from the blockchain. Credits user's real wallet."""
    currency = body.currency.upper()
    wallet = await _get_or_create_wallet(db, body.user_id, currency)
    wallet.balance = Decimal(str(wallet.balance)) + body.amount
    balance_after = Decimal(str(wallet.balance))

    entry = BalanceLedger(
        user_id=body.user_id,
        currency=currency,
        amount=body.amount,
        balance_after=balance_after,
        tx_type=LedgerTxType.DEPOSIT,
        reference_id=body.reference_id,
        note=body.note or f"Deposit confirmed by admin {admin_id}",
    )
    db.add(entry)
    await db.commit()
    return {"status": "credited", "balance_after": float(balance_after)}
