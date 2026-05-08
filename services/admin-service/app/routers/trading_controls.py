"""
Sprint 20 — Emergency trading halt controls.

Endpoints:
  GET  /api/admin/trading/status  — check if halt flag is set (any admin)
  POST /api/admin/trading/halt    — set the halt flag (SUPER_ADMIN only)
  POST /api/admin/trading/resume  — clear the halt flag (SUPER_ADMIN only)

The halt flag is stored in Redis under the key  platform:trading_halted
(no TTL — persists until explicitly cleared).
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies.auth import AdminContext, require_admin_context
from ..redis_client import get_redis

HALT_KEY = "platform:trading_halted"

router = APIRouter(prefix="/api/admin/trading", tags=["Admin — Trading Controls"])


@router.get("/status")
async def trading_status(
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
) -> dict:
    """Return whether the platform trading halt is currently active."""
    redis = get_redis()
    halted = await redis.exists(HALT_KEY)
    return {"halted": bool(halted)}


@router.post("/halt", status_code=status.HTTP_200_OK)
async def halt_trading(
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
) -> dict:
    """
    Immediately halt all live order placement across the platform.
    SUPER_ADMIN only.
    """
    if not ctx.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SUPER_ADMIN can halt trading.",
        )
    redis = get_redis()
    await redis.set(HALT_KEY, "1")
    return {"halted": True, "message": "Platform trading has been halted."}


@router.post("/resume", status_code=status.HTTP_200_OK)
async def resume_trading(
    ctx: Annotated[AdminContext, Depends(require_admin_context)],
) -> dict:
    """
    Resume live order placement after a halt.
    SUPER_ADMIN only.
    """
    if not ctx.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SUPER_ADMIN can resume trading.",
        )
    redis = get_redis()
    await redis.delete(HALT_KEY)
    return {"halted": False, "message": "Platform trading has been resumed."}
