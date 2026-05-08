"""
Partner router — PARTNER role users can:
- View all users referred through their account.
- View the trade history of referred users (only if Super Admin has granted
  the VIEW_REFERRED_TRADE_HISTORY permission for this partner).
- View their commission ledger (brokerage income share entries).

All endpoints require the caller's role to be PARTNER.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import get_current_user, require_role
from ..models.user import (
    CommissionLedger,
    PartnerPermission,
    User,
    UserRole,
)
from ..schemas.user import (
    CommissionEntry,
    PartnerPermissionResponse,
    ReferredUserSummary,
)

router = APIRouter(prefix="/partner", tags=["Partner"])

_PERMISSION_VIEW_TRADES = "VIEW_REFERRED_TRADE_HISTORY"


@router.get("/referrals", response_model=list[ReferredUserSummary])
async def list_referrals(
    current_user: Annotated[User, Depends(require_role(UserRole.PARTNER))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, le=200),
) -> list[User]:
    """Return all users referred by this partner account."""
    offset = (page - 1) * per_page
    result = await db.execute(
        select(User)
        .where(User.referred_by == current_user.id)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    return list(result.scalars().all())


@router.get("/referrals/{referred_user_id}/trades")
async def get_referred_user_trades(
    referred_user_id: UUID,
    current_user: Annotated[User, Depends(require_role(UserRole.PARTNER))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Returns the trade history stub for a referred user.
    Only accessible if Super Admin has granted VIEW_REFERRED_TRADE_HISTORY to this partner.
    Full trade data lives in order-service; this endpoint verifies the permission gate
    and returns the referred user record — the frontend/client calls order-service directly
    after this authorisation check passes.
    """
    # 1 — Verify permission granted by Super Admin
    perm_result = await db.execute(
        select(PartnerPermission).where(
            PartnerPermission.partner_user_id == current_user.id,
            PartnerPermission.permission == _PERMISSION_VIEW_TRADES,
        )
    )
    if perm_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view referred users' trade history. "
                   "Contact your Super Admin to enable this access.",
        )

    # 2 — Verify the requested user is actually referred by this partner
    user_result = await db.execute(
        select(User).where(
            User.id == referred_user_id,
            User.referred_by == current_user.id,
        )
    )
    referred_user = user_result.scalar_one_or_none()
    if referred_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referred user not found under your account.",
        )

    return {
        "user_id": str(referred_user.id),
        "email": referred_user.email,
        "message": "Permission verified. Fetch trade history from order-service using this user_id.",
    }


@router.get("/commissions", response_model=list[CommissionEntry])
async def list_commissions(
    current_user: Annotated[User, Depends(require_role(UserRole.PARTNER))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, le=500),
) -> list[CommissionLedger]:
    """Return the commission ledger for this partner account."""
    offset = (page - 1) * per_page
    result = await db.execute(
        select(CommissionLedger)
        .where(CommissionLedger.partner_user_id == current_user.id)
        .order_by(CommissionLedger.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    return list(result.scalars().all())


@router.get("/permissions", response_model=list[PartnerPermissionResponse])
async def list_permissions(
    current_user: Annotated[User, Depends(require_role(UserRole.PARTNER))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PartnerPermission]:
    """Return the discretionary permissions granted to this partner by Super Admin."""
    result = await db.execute(
        select(PartnerPermission).where(
            PartnerPermission.partner_user_id == current_user.id
        )
    )
    return list(result.scalars().all())
