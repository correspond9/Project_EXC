"""
EventListener — subscribes to:
  fills.*        → FILL notifications (order fills)
  risk.margin_call.*  → MARGIN_CALL notifications
  risk.liquidation.*  → LIQUIDATION notifications

For each event:
  1. Write Notification record to DB
  2. Broadcast to active WS connections for that user
"""
import asyncio
import json
import logging
import uuid

import redis.asyncio as aioredis
import sqlalchemy as sa

from ..database import AsyncSessionLocal
from ..models.notification import Notification, NotificationType
from ..routers.ws import broadcast

log = logging.getLogger(__name__)


def _build_fill_notification(msg: dict) -> tuple[str, str] | None:
    symbol = msg.get("symbol", "UNKNOWN")
    side = msg.get("side", "")
    qty = msg.get("quantity", "")
    price = msg.get("price", "")
    if not price:
        return None
    title = f"Order Filled — {symbol}"
    body = f"{side} {qty} {symbol} filled at {price} USDT"
    return title, body


def _build_margin_call_notification(msg: dict) -> tuple[str, str]:
    symbol = msg.get("symbol", "")
    ratio = msg.get("margin_ratio_pct", "")
    title = "Margin Call Warning"
    body = (
        f"Your margin ratio has dropped to {ratio}% on {symbol}. "
        "Please top up your margin to avoid liquidation."
    )
    return title, body


def _build_liquidation_notification(msg: dict) -> tuple[str, str]:
    symbol = msg.get("symbol", "")
    side = msg.get("side", "")
    liq_price = msg.get("liquidation_price", "")
    pnl = msg.get("realised_pnl", "0")
    title = f"Position Liquidated — {symbol}"
    body = (
        f"Your {side} {symbol} position was liquidated at {liq_price} USDT. "
        f"Realised P&L: {pnl} USDT."
    )
    return title, body


async def _save_and_broadcast(
    user_id: uuid.UUID,
    notif_type: NotificationType,
    title: str,
    body: str,
) -> None:
    async with AsyncSessionLocal() as db:
        notif = Notification(
            user_id=user_id,
            type=notif_type,
            title=title,
            body=body,
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)

    payload = {
        "id": str(notif.id),
        "type": notif.type.value,
        "title": notif.title,
        "body": notif.body,
        "is_read": False,
        "created_at": notif.created_at.isoformat() if notif.created_at else None,
    }
    await broadcast(str(user_id), payload)


class EventListener:
    async def start(self, redis_client: aioredis.Redis) -> None:
        log.info("EventListener: starting")
        await asyncio.gather(
            self._run(redis_client, "fills.*", self._handle_fill),
            self._run(redis_client, "risk.margin_call.*", self._handle_margin_call),
            self._run(redis_client, "risk.liquidation.*", self._handle_liquidation),
        )

    async def _run(self, redis_client: aioredis.Redis, pattern: str, handler) -> None:
        while True:
            try:
                pubsub = redis_client.pubsub()
                await pubsub.psubscribe(pattern)
                log.info("EventListener: subscribed to %s", pattern)
                async for raw in pubsub.listen():
                    if raw["type"] != "pmessage":
                        continue
                    try:
                        msg = json.loads(raw["data"])
                        await handler(msg)
                    except Exception as exc:
                        log.debug("EventListener handler error [%s]: %s", pattern, exc)
            except asyncio.CancelledError:
                return
            except Exception as exc:
                log.exception("EventListener reconnect [%s] — %s", pattern, exc)
                await asyncio.sleep(5)

    async def _handle_fill(self, msg: dict) -> None:
        msg_type = msg.get("type", "")
        if msg_type not in ("fill", "FILL"):
            return
        user_id_str = msg.get("user_id", "")
        if not user_id_str:
            return
        result = _build_fill_notification(msg)
        if result is None:
            return
        title, body = result
        await _save_and_broadcast(uuid.UUID(user_id_str), NotificationType.FILL, title, body)

    async def _handle_margin_call(self, msg: dict) -> None:
        user_id_str = msg.get("user_id", "")
        if not user_id_str:
            return
        title, body = _build_margin_call_notification(msg)
        await _save_and_broadcast(
            uuid.UUID(user_id_str), NotificationType.MARGIN_CALL, title, body
        )

    async def _handle_liquidation(self, msg: dict) -> None:
        user_id_str = msg.get("user_id", "")
        if not user_id_str:
            return
        title, body = _build_liquidation_notification(msg)
        await _save_and_broadcast(
            uuid.UUID(user_id_str), NotificationType.LIQUIDATION, title, body
        )
