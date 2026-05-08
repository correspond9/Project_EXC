"""
Admin-service — Student performance / leaderboard router.
Queries the shared database for trading stats across all users.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies.auth import require_admin
from ..models.user import User
from ..models.mirrors import Order, SimulationWallet, FuturesPosition

router = APIRouter(prefix="/api/admin/performance", tags=["Admin — Student Performance"])


@router.get("/leaderboard")
async def get_leaderboard(
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, le=200),
):
    """
    Return the student leaderboard ranked by total realised P&L
    (futures realised_pnl) + current simulation USDT balance.
    Includes: email, total_trades, realised_pnl, current_balance, rank.
    """
    # Raw SQL for efficiency across joined tables
    sql = text("""
        SELECT
            u.id::text                        AS user_id,
            u.email,
            COALESCE(stats.total_trades, 0)   AS total_trades,
            COALESCE(stats.realised_pnl, 0)   AS realised_pnl,
            COALESCE(wallet.balance, 0)        AS current_balance,
            COALESCE(stats.win_trades, 0)      AS win_trades,
            COALESCE(stats.best_trade, 0)      AS best_trade,
            COALESCE(stats.worst_trade, 0)     AS worst_trade,
            CASE
                WHEN COALESCE(stats.total_trades, 0) = 0 THEN 0
                ELSE ROUND(
                    COALESCE(stats.win_trades, 0)::numeric
                    / COALESCE(stats.total_trades, 1) * 100, 1
                )
            END AS win_rate_pct
        FROM users u
        LEFT JOIN (
            SELECT
                user_id,
                COUNT(*)                    AS total_trades,
                SUM(COALESCE(realised_pnl,0)) AS realised_pnl,
                COUNT(*) FILTER (WHERE COALESCE(realised_pnl,0) > 0) AS win_trades,
                MAX(COALESCE(realised_pnl,0)) AS best_trade,
                MIN(COALESCE(realised_pnl,0)) AS worst_trade
            FROM futures_positions
            WHERE status IN ('CLOSED', 'LIQUIDATED')
            GROUP BY user_id
        ) stats ON stats.user_id = u.id
        LEFT JOIN (
            SELECT user_id, balance
            FROM simulation_wallets
            WHERE currency = 'USDT'
        ) wallet ON wallet.user_id = u.id
        WHERE u.role = 'STUDENT'
          AND u.role != 'SUPER_USER'
        ORDER BY realised_pnl DESC
        LIMIT :limit
    """)
    result = await db.execute(sql, {"limit": limit})
    rows = result.mappings().all()

    leaderboard = []
    for rank, row in enumerate(rows, start=1):
        leaderboard.append({
            "rank": rank,
            "user_id": row["user_id"],
            "email": row["email"],
            "total_trades": int(row["total_trades"]),
            "realised_pnl": float(row["realised_pnl"]),
            "current_balance": float(row["current_balance"]),
            "win_rate_pct": float(row["win_rate_pct"]),
            "best_trade": float(row["best_trade"]),
            "worst_trade": float(row["worst_trade"]),
        })

    return {"leaderboard": leaderboard, "total": len(leaderboard)}


@router.get("/users/{user_id}")
async def get_user_performance(
    user_id: uuid.UUID,
    _admin_id: Annotated[uuid.UUID, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return detailed performance stats for a specific user."""
    sql = text("""
        SELECT
            u.id::text AS user_id,
            u.email,
            u.role,
            COALESCE(stats.total_trades, 0)  AS total_trades,
            COALESCE(stats.realised_pnl, 0)  AS realised_pnl,
            COALESCE(wallet.balance, 0)       AS current_balance,
            COALESCE(wallet.available_balance, 0) AS available_balance,
            COALESCE(stats.win_trades, 0)     AS win_trades,
            COALESCE(stats.best_trade, 0)     AS best_trade,
            COALESCE(stats.worst_trade, 0)    AS worst_trade,
            COALESCE(spot_orders.count, 0)    AS spot_orders
        FROM users u
        LEFT JOIN (
            SELECT user_id,
                COUNT(*) AS total_trades,
                SUM(COALESCE(realised_pnl,0)) AS realised_pnl,
                COUNT(*) FILTER (WHERE COALESCE(realised_pnl,0) > 0) AS win_trades,
                MAX(COALESCE(realised_pnl,0)) AS best_trade,
                MIN(COALESCE(realised_pnl,0)) AS worst_trade
            FROM futures_positions
            WHERE status IN ('CLOSED', 'LIQUIDATED') AND user_id = :uid
            GROUP BY user_id
        ) stats ON stats.user_id = u.id
        LEFT JOIN (
            SELECT user_id, balance, available_balance
            FROM simulation_wallets
            WHERE currency = 'USDT' AND user_id = :uid
        ) wallet ON wallet.user_id = u.id
        LEFT JOIN (
            SELECT user_id, COUNT(*) AS count
            FROM orders
            WHERE user_id = :uid AND market_type = 'SPOT' AND status = 'FILLED'
            GROUP BY user_id
        ) spot_orders ON spot_orders.user_id = u.id
        WHERE u.id = :uid
    """)
    result = await db.execute(sql, {"uid": user_id})
    row = result.mappings().first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "role": row["role"],
        "total_futures_trades": int(row["total_trades"]),
        "total_spot_orders": int(row["spot_orders"]),
        "realised_pnl": float(row["realised_pnl"]),
        "current_balance": float(row["current_balance"]),
        "available_balance": float(row["available_balance"]),
        "win_rate_pct": round(
            int(row["win_trades"]) / max(int(row["total_trades"]), 1) * 100, 1
        ),
        "best_trade": float(row["best_trade"]),
        "worst_trade": float(row["worst_trade"]),
    }
