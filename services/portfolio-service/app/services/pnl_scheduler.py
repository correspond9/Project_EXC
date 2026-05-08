"""
pnl_scheduler.py
~~~~~~~~~~~~~~~~
APScheduler job that runs at midnight (UTC) every day.
For each user with holdings, it computes and upserts a PnlSnapshot row.
"""
import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, text

from ..database import AsyncSessionLocal
from ..models.portfolio import PnlSnapshot, PortfolioHolding
from ..models.wallet import SimulationWallet
from ..redis_client import get_redis_pool

log = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

_EXECUTION_MODE = "SIMULATION"


async def _get_current_price(redis, asset: str) -> Decimal:
    """Read last price from Redis ticker:{ASSET}USDT hash field 'c'."""
    symbol_key = f"ticker:{asset}USDT"
    raw = await redis.hget(symbol_key, "c")
    if raw:
        try:
            return Decimal(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
        except Exception:  # noqa: BLE001
            pass
    return Decimal("0")


async def _take_daily_snapshot() -> None:
    """Write one PnlSnapshot row per user with open holdings."""
    today = date.today()
    redis = get_redis_pool()

    async with AsyncSessionLocal() as session:
        # Distinct user_ids that have holdings
        result = await session.execute(
            select(PortfolioHolding.user_id)
            .where(PortfolioHolding.execution_mode == _EXECUTION_MODE)
            .distinct()
        )
        user_ids: list[uuid.UUID] = [row[0] for row in result.fetchall()]

        for user_id in user_ids:
            # Holdings for this user
            h_result = await session.execute(
                select(PortfolioHolding).where(
                    PortfolioHolding.user_id == user_id,
                    PortfolioHolding.execution_mode == _EXECUTION_MODE,
                )
            )
            holdings = h_result.scalars().all()

            total_realised = Decimal("0")
            total_unrealised = Decimal("0")
            total_value = Decimal("0")

            for h in holdings:
                qty = Decimal(str(h.quantity))
                avg = Decimal(str(h.average_entry_price))
                realised = Decimal(str(h.total_realised_pnl))
                price = await _get_current_price(redis, h.asset)

                unrealised = (price - avg) * qty if qty > 0 else Decimal("0")
                total_realised += realised
                total_unrealised += unrealised
                total_value += qty * price

            # Add USDT wallet balance
            w_result = await session.execute(
                select(SimulationWallet.balance).where(
                    SimulationWallet.user_id == user_id,
                    SimulationWallet.currency == "USDT",
                )
            )
            usdt_balance = w_result.scalar_one_or_none() or Decimal("0")
            total_value += Decimal(str(usdt_balance))

            # Upsert snapshot
            snap_result = await session.execute(
                select(PnlSnapshot).where(
                    PnlSnapshot.user_id == user_id,
                    PnlSnapshot.snapshot_date == today,
                    PnlSnapshot.execution_mode == _EXECUTION_MODE,
                )
            )
            snap = snap_result.scalar_one_or_none()
            if snap is None:
                snap = PnlSnapshot(
                    user_id=user_id,
                    snapshot_date=today,
                    execution_mode=_EXECUTION_MODE,
                )
                session.add(snap)

            snap.total_realised_pnl = total_realised
            snap.total_unrealised_pnl = total_unrealised
            snap.total_portfolio_value = total_value

        await session.commit()
    log.info("pnl_scheduler: daily snapshot complete for %d users", len(user_ids))


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _take_daily_snapshot,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_pnl_snapshot",
        replace_existing=True,
    )
    _scheduler.start()
    log.info("pnl_scheduler: started — daily snapshot at UTC midnight")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("pnl_scheduler: stopped")
