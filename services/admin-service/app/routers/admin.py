import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, condecimal
from sqlalchemy import func, select, text, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import AdminContext, require_admin, require_admin_context
from ..models.position_limit import UserPositionLimit
from ..models.user import KYCStatus, TradingMode, User
from ..schemas.admin import (
    UpdateTradingModeRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserSummary,
)

router = APIRouter(prefix="/api/admin/users", tags=["Admin — Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, le=100),
    search: str | None = Query(default=None, description="Search by email (partial match)"),
    role: str | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
):
    """Return a paginated, searchable, filterable list of all users.
    SUPER_USER accounts are hidden from all callers except SUPER_ADMIN.
    """
    offset = (page - 1) * per_page

    filters = []
    # SUPER_USER accounts are invisible to everyone except SUPER_ADMIN
    if not ctx.is_super_admin:
        filters.append(User.role != "SUPER_USER")
    if search:
        filters.append(User.email.ilike(f"%{search}%"))
    if role:
        filters.append(User.role == role.upper())
    if is_active is not None:
        filters.append(User.is_active == is_active)

    base_query = select(User)
    if filters:
        base_query = base_query.where(*filters)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
    )
    users = result.scalars().all()

    return UserListResponse(
        total=total,
        page=page,
        per_page=per_page,
        users=[UserSummary.model_validate(u) for u in users],
    )


@router.get("/{user_id}", response_model=UserSummary)
async def get_user(
    user_id: uuid.UUID,
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return a single user's detail. SUPER_USER accounts are only visible to SUPER_ADMIN."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Block non-super-admins from resolving a SUPER_USER account
    if str(user.role) == "SUPER_USER" and not ctx.is_super_admin:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSummary.model_validate(user)


@router.put("/{user_id}/mode", response_model=UserSummary)
async def update_trading_mode(
    user_id: uuid.UUID,
    body: UpdateTradingModeRequest,
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Switch a user's trading mode between SIMULATION and LIVE."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or (str(user.role) == "SUPER_USER" and not ctx.is_super_admin):
        raise HTTPException(status_code=404, detail="User not found")

    if body.trading_mode == TradingMode.LIVE and user.kyc_status != KYCStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="KYC must be APPROVED before enabling LIVE mode.",
        )

    user.trading_mode = body.trading_mode
    await db.commit()
    await db.refresh(user)
    return UserSummary.model_validate(user)


@router.put("/{user_id}/status", response_model=UserSummary)
async def update_user_status(
    user_id: uuid.UUID,
    body: UpdateUserStatusRequest,
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Activate or suspend a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or (str(user.role) == "SUPER_USER" and not ctx.is_super_admin):
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = body.is_active
    await db.commit()
    await db.refresh(user)
    return UserSummary.model_validate(user)


# ── Position limits ────────────────────────────────────────────────────────────

class SetPositionLimitRequest(BaseModel):
    max_position_value_usdt: Decimal


@router.put("/{user_id}/position-limit", status_code=status.HTTP_200_OK)
async def set_position_limit(
    user_id: uuid.UUID,
    body: SetPositionLimitRequest,
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Set or update the maximum total open futures position value (USDT) for a user."""
    if body.max_position_value_usdt <= Decimal("0"):
        raise HTTPException(status_code=400, detail="max_position_value_usdt must be > 0")

    # Check user exists and is visible to this caller
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None or (str(user.role) == "SUPER_USER" and not ctx.is_super_admin):
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(UserPositionLimit).where(UserPositionLimit.user_id == user_id)
    )
    limit_row = result.scalar_one_or_none()

    if limit_row is None:
        limit_row = UserPositionLimit(
            user_id=user_id,
            max_position_value_usdt=body.max_position_value_usdt,
        )
        db.add(limit_row)
    else:
        limit_row.max_position_value_usdt = body.max_position_value_usdt
        limit_row.updated_at = text("now()")

    await db.commit()
    return {
        "user_id": str(user_id),
        "max_position_value_usdt": str(body.max_position_value_usdt),
    }
