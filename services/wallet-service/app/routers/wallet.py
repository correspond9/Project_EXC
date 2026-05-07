import uuid
from decimal import Decimal
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user_id, require_admin
from ..models.wallet import SimulationWallet
from ..schemas.wallet import TopUpRequest, TopUpResponse, WalletResponse

router = APIRouter(prefix="/api/wallet", tags=["Wallet"])
admin_router = APIRouter(prefix="/api/admin/wallet", tags=["Admin — Wallet"])


# ── User endpoints ─────────────────────────────────────────────────────────────

@router.get("/simulation", response_model=List[WalletResponse])
async def get_simulation_wallet(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return all simulation wallet balances for the authenticated user."""
    result = await db.execute(
        select(SimulationWallet).where(SimulationWallet.user_id == user_id)
    )
    wallets = result.scalars().all()
    return [WalletResponse.from_orm_with_available(w) for w in wallets]


# ── Admin endpoints ────────────────────────────────────────────────────────────

@admin_router.post("/topup", response_model=TopUpResponse, status_code=status.HTTP_200_OK)
async def admin_topup(
    body: TopUpRequest,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Assign (or add to) a student's simulation wallet balance.
    Creates the wallet row if it does not yet exist.
    """
    result = await db.execute(
        select(SimulationWallet).where(
            SimulationWallet.user_id == body.user_id,
            SimulationWallet.currency == body.currency.upper(),
        )
    )
    wallet = result.scalar_one_or_none()

    if wallet is None:
        wallet = SimulationWallet(
            user_id=body.user_id,
            currency=body.currency.upper(),
            balance=body.amount,
            locked_balance=Decimal("0"),
        )
        db.add(wallet)
    else:
        wallet.balance = wallet.balance + body.amount

    await db.commit()
    await db.refresh(wallet)

    return TopUpResponse(
        user_id=body.user_id,
        currency=wallet.currency,
        new_balance=wallet.balance,
        message=f"Credited {body.amount} {body.currency.upper()} to simulation wallet.",
    )
