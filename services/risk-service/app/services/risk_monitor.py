"""
RiskMonitor — subscribes to market.ticker.* and evaluates:
  1. Margin call: margin_ratio < MARGIN_CALL_THRESHOLD → write margin_call record,
     publish risk.margin_call.{user_id}, resolve previous open margin call if ratio recovers.
  2. Liquidation recording: listens to fills.* for liquidation events published by
     simulation-engine, writes liquidations record, publishes risk.liquidation.{user_id}.

The actual position closing is still handled by simulation-engine's PositionMonitor.
Risk-service is the authoritative recorder and notification publisher.
"""
import asyncio
import json
import logging
import uuid
from decimal import Decimal
from datetime import datetime, timezone

import redis.asyncio as aioredis
import sqlalchemy as sa

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.futures import FuturesExecutionMode, MarginAccount, Position, PositionStatus
from ..models.risk import Liquidation, MarginCall

log = logging.getLogger(__name__)

# Track users already in margin-call state to avoid spam: {user_id_str: margin_call_id_str}
_active_margin_calls: dict[str, str] = {}


class RiskMonitor:
    """
    Two concurrent tasks:
    1. Ticker subscriber  — margin call detection per price tick
    2. Fill subscriber    — liquidation event recording
    """

    async def start(self, redis_client: aioredis.Redis) -> None:
        log.info("RiskMonitor: starting")
        await asyncio.gather(
            self._run_ticker_monitor(redis_client),
            self._run_fill_monitor(redis_client),
        )

    # ── Ticker monitor ──────────────────────────────────────────────────────────

    async def _run_ticker_monitor(self, redis_client: aioredis.Redis) -> None:
        while True:
            try:
                pubsub = redis_client.pubsub()
                await pubsub.psubscribe("market.ticker.*")
                log.info("RiskMonitor: subscribed to market.ticker.*")
                async for raw in pubsub.listen():
                    if raw["type"] != "pmessage":
                        continue
                    try:
                        data = json.loads(raw["data"])
                        channel = raw["channel"]
                        if isinstance(channel, bytes):
                            channel = channel.decode()
                        redis_sym = channel.split(".")[-1].upper()
                        symbol_slash = redis_sym[:-4] + "/" + redis_sym[-4:]
                        current_price = Decimal(
                            str(data.get("c") or data.get("last_price") or "0")
                        )
                        if current_price <= Decimal("0"):
                            continue
                        await self._check_margin_calls(symbol_slash, current_price, redis_client)
                    except Exception as exc:
                        log.debug("RiskMonitor ticker error: %s", exc)
            except asyncio.CancelledError:
                return
            except Exception as exc:
                log.exception("RiskMonitor ticker reconnect — %s", exc)
                await asyncio.sleep(5)

    async def _check_margin_calls(
        self,
        symbol_slash: str,
        current_price: Decimal,
        redis_client: aioredis.Redis,
    ) -> None:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                sa.select(Position).where(
                    Position.symbol == symbol_slash,
                    Position.status == PositionStatus.OPEN,
                    Position.execution_mode == FuturesExecutionMode.SIMULATION,
                )
            )
            positions = result.scalars().all()

            for pos in positions:
                user_id = str(pos.user_id)

                # Fetch margin account
                acct_result = await db.execute(
                    sa.select(MarginAccount).where(
                        MarginAccount.user_id == pos.user_id,
                        MarginAccount.execution_mode == FuturesExecutionMode.SIMULATION,
                    )
                )
                acct = acct_result.scalar_one_or_none()
                if acct is None:
                    continue

                total = Decimal(str(acct.total_margin_balance))
                used = Decimal(str(acct.used_margin))
                if used <= Decimal("0"):
                    continue

                # unrealised P&L from position row (kept up-to-date by sim-engine)
                upnl = Decimal(str(pos.unrealised_pnl))
                effective_balance = total + upnl
                margin_ratio = float(effective_balance / used)

                threshold = settings.margin_call_threshold

                if margin_ratio < threshold:
                    # Issue margin call if not already active for this user
                    if user_id not in _active_margin_calls:
                        mc = MarginCall(
                            user_id=pos.user_id,
                            position_id=pos.id,
                            margin_ratio_at_call=Decimal(str(round(margin_ratio * 100, 4))),
                            price_at_call=current_price,
                        )
                        db.add(mc)
                        await db.flush()
                        _active_margin_calls[user_id] = str(mc.id)

                        event = {
                            "type": "margin_call",
                            "user_id": user_id,
                            "position_id": str(pos.id),
                            "symbol": symbol_slash,
                            "margin_ratio_pct": round(margin_ratio * 100, 2),
                            "price": str(current_price),
                            "margin_call_id": str(mc.id),
                        }
                        await redis_client.publish(
                            f"risk.margin_call.{user_id}", json.dumps(event)
                        )
                        log.warning(
                            "RiskMonitor: margin call for user %s ratio=%.2f%%",
                            user_id, margin_ratio * 100,
                        )
                else:
                    # Ratio recovered — resolve outstanding margin call
                    if user_id in _active_margin_calls:
                        mc_id = _active_margin_calls.pop(user_id)
                        mc_result = await db.execute(
                            sa.select(MarginCall).where(
                                MarginCall.id == uuid.UUID(mc_id),
                                MarginCall.resolved_at.is_(None),
                            )
                        )
                        mc = mc_result.scalar_one_or_none()
                        if mc:
                            mc.resolved_at = datetime.now(timezone.utc).isoformat()
                            log.info("RiskMonitor: margin call resolved for user %s", user_id)

            await db.commit()

    # ── Fill monitor (liquidation recorder) ────────────────────────────────────

    async def _run_fill_monitor(self, redis_client: aioredis.Redis) -> None:
        """
        Subscribe to fills.* and record liquidation events published by
        simulation-engine PositionMonitor to the liquidations table,
        then re-publish on risk.liquidation.{user_id} for notification-service.
        """
        while True:
            try:
                pubsub = redis_client.pubsub()
                await pubsub.psubscribe("fills.*")
                log.info("RiskMonitor: subscribed to fills.* for liquidation recording")
                async for raw in pubsub.listen():
                    if raw["type"] != "pmessage":
                        continue
                    try:
                        msg = json.loads(raw["data"])
                        if msg.get("type") != "liquidation":
                            continue
                        await self._record_liquidation(msg, redis_client)
                    except Exception as exc:
                        log.debug("RiskMonitor fill error: %s", exc)
            except asyncio.CancelledError:
                return
            except Exception as exc:
                log.exception("RiskMonitor fill reconnect — %s", exc)
                await asyncio.sleep(5)

    async def _record_liquidation(
        self, msg: dict, redis_client: aioredis.Redis
    ) -> None:
        user_id_str = msg.get("user_id", "")
        position_id_str = msg.get("position_id", "")
        liq_price_str = msg.get("liquidation_price", "0")
        pnl_str = msg.get("realised_pnl", "0")

        try:
            user_id = uuid.UUID(user_id_str)
            position_id = uuid.UUID(position_id_str) if position_id_str else None
            liq_price = Decimal(liq_price_str)
            realised_pnl = Decimal(pnl_str)
        except Exception as exc:
            log.warning("RiskMonitor: bad liquidation event — %s", exc)
            return

        async with AsyncSessionLocal() as db:
            record = Liquidation(
                user_id=user_id,
                position_id=position_id,
                liquidation_price=liq_price,
                realised_pnl=realised_pnl,
            )
            db.add(record)
            await db.commit()

        # Re-publish with risk. prefix so notification-service picks it up
        event = {
            "type": "liquidation",
            "user_id": user_id_str,
            "position_id": position_id_str,
            "symbol": msg.get("symbol", ""),
            "side": msg.get("side", ""),
            "liquidation_price": liq_price_str,
            "realised_pnl": pnl_str,
        }
        await redis_client.publish(f"risk.liquidation.{user_id_str}", json.dumps(event))
        log.info(
            "RiskMonitor: recorded liquidation user=%s pnl=%s", user_id_str, pnl_str
        )
