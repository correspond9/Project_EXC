"""
EventListener — subscribes to:
  fills.*             → FILL notifications (order fills)
  risk.margin_call.*  → MARGIN_CALL notifications
  risk.liquidation.*  → LIQUIDATION notifications
  market.ticker.*     → Price alert monitoring

For each event:
  1. Write Notification record to DB
  2. Broadcast to active WS connections for that user
  3. Send email if user preferences allow (SMTP configured)
"""
import asyncio
import json
import logging
import uuid
from decimal import Decimal

import redis.asyncio as aioredis
import sqlalchemy as sa

from ..database import AsyncSessionLocal
from ..models.alerts import AlertCondition, PriceAlert
from ..models.notification import Notification, NotificationType
from ..routers.ws import broadcast
from ..services.email_service import (
    send_fill_email,
    send_kyc_approved_email,
    send_kyc_rejected_email,
    send_kyc_submitted_email,
    send_liquidation_email,
    send_margin_call_email,
    send_price_alert_email,
)

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


async def _get_user_email(user_id: uuid.UUID) -> str | None:
    """Return the user's email from notification_preferences table (may be None)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            sa.text(
                "SELECT user_email FROM notification_preferences WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.fetchone()
        return row[0] if row else None


async def _get_email_pref(user_id: uuid.UUID, pref_column: str) -> bool:
    """Return an email preference boolean (True = send email). Default True if no row."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            sa.text(
                f"SELECT {pref_column} FROM notification_preferences WHERE user_id = :uid"  # noqa: S608
            ),
            {"uid": user_id},
        )
        row = result.fetchone()
        return bool(row[0]) if row else True


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
            self._run(redis_client, "kyc.*", self._handle_kyc),
            self._run_ticker_monitor(redis_client),
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
        user_id = uuid.UUID(user_id_str)
        await _save_and_broadcast(user_id, NotificationType.FILL, title, body)

        # Email
        if await _get_email_pref(user_id, "email_on_fill"):
            email = await _get_user_email(user_id)
            if email:
                await send_fill_email(
                    to_email=email,
                    symbol=msg.get("symbol", ""),
                    side=msg.get("side", ""),
                    quantity=msg.get("quantity", ""),
                    price=msg.get("price", ""),
                )

    async def _handle_margin_call(self, msg: dict) -> None:
        user_id_str = msg.get("user_id", "")
        if not user_id_str:
            return
        title, body = _build_margin_call_notification(msg)
        user_id = uuid.UUID(user_id_str)
        await _save_and_broadcast(user_id, NotificationType.MARGIN_CALL, title, body)

        if await _get_email_pref(user_id, "email_on_margin_call"):
            email = await _get_user_email(user_id)
            if email:
                await send_margin_call_email(
                    to_email=email,
                    symbol=msg.get("symbol", ""),
                    margin_ratio=str(msg.get("margin_ratio_pct", "")),
                )

    async def _handle_liquidation(self, msg: dict) -> None:
        user_id_str = msg.get("user_id", "")
        if not user_id_str:
            return
        title, body = _build_liquidation_notification(msg)
        user_id = uuid.UUID(user_id_str)
        await _save_and_broadcast(user_id, NotificationType.LIQUIDATION, title, body)

        if await _get_email_pref(user_id, "email_on_liquidation"):
            email = await _get_user_email(user_id)
            if email:
                await send_liquidation_email(
                    to_email=email,
                    symbol=msg.get("symbol", ""),
                    side=msg.get("side", ""),
                    liquidation_price=str(msg.get("liquidation_price", "")),
                    realised_pnl=str(msg.get("realised_pnl", "0")),
                )

    async def _handle_kyc(self, msg: dict) -> None:
        """Handle kyc.submitted.*, kyc.approved.*, kyc.rejected.* events."""
        event = msg.get("event", "")
        user_id_str = msg.get("user_id", "")
        email = msg.get("email", "")
        if not user_id_str:
            return
        user_id = uuid.UUID(user_id_str)

        if event == "KYC_SUBMITTED":
            await _save_and_broadcast(
                user_id,
                NotificationType.KYC_SUBMITTED,
                "KYC Submitted",
                "Your KYC documents have been received and are under review.",
            )
            if email:
                await send_kyc_submitted_email(to_email=email)

        elif event == "KYC_APPROVED":
            await _save_and_broadcast(
                user_id,
                NotificationType.KYC_APPROVED,
                "KYC Approved",
                "Your KYC verification has been approved. You are now eligible for Live trading.",
            )
            if email:
                await send_kyc_approved_email(to_email=email)

        elif event == "KYC_REJECTED":
            reason = msg.get("reason", "")
            await _save_and_broadcast(
                user_id,
                NotificationType.KYC_REJECTED,
                "KYC Rejected",
                f"Your KYC submission was rejected. {reason}".strip(),
            )
            if email:
                await send_kyc_rejected_email(to_email=email, reason=reason)

    # ──────────────────────────────────────────────────────────────────────────
    # Price alert monitor — subscribes to market.ticker.*
    # ──────────────────────────────────────────────────────────────────────────

    async def _run_ticker_monitor(self, redis_client: aioredis.Redis) -> None:
        """Monitor live ticker events and check active price alerts."""
        while True:
            try:
                pubsub = redis_client.pubsub()
                await pubsub.psubscribe("market.ticker.*")
                log.info("EventListener: subscribed to market.ticker.* for price alerts")
                async for raw in pubsub.listen():
                    if raw["type"] != "pmessage":
                        continue
                    try:
                        msg = json.loads(raw["data"])
                        await self._check_price_alerts(msg)
                    except Exception as exc:
                        log.debug("EventListener ticker handler error: %s", exc)
            except asyncio.CancelledError:
                return
            except Exception as exc:
                log.exception("EventListener ticker reconnect — %s", exc)
                await asyncio.sleep(5)

    async def _check_price_alerts(self, ticker: dict) -> None:
        """
        On each ticker event, check all active (un-triggered) price alerts
        for the given symbol. Trigger any that have crossed their target.
        """
        symbol = ticker.get("s") or ticker.get("symbol")
        price_raw = ticker.get("c") or ticker.get("price")
        if not symbol or not price_raw:
            return

        try:
            current_price = Decimal(str(price_raw))
        except Exception:
            return

        # Fetch active alerts for this symbol
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                sa.select(PriceAlert).where(
                    PriceAlert.symbol == symbol.upper(),
                    PriceAlert.is_triggered == False,  # noqa: E712
                )
            )
            alerts = result.scalars().all()

        for alert in alerts:
            triggered = False
            if alert.condition == AlertCondition.ABOVE and current_price >= alert.target_price:
                triggered = True
            elif alert.condition == AlertCondition.BELOW and current_price <= alert.target_price:
                triggered = True

            if not triggered:
                continue

            # Mark triggered
            async with AsyncSessionLocal() as db:
                await db.execute(
                    sa.text(
                        """
                        UPDATE price_alerts
                           SET is_triggered = true,
                               triggered_at = now()
                         WHERE id = :aid AND is_triggered = false
                        """
                    ),
                    {"aid": alert.id},
                )
                await db.commit()

            # In-app notification
            title = f"Price Alert — {symbol}"
            body = (
                f"{symbol} price is now {current_price} USDT "
                f"({'above' if alert.condition == AlertCondition.ABOVE else 'below'} "
                f"your target of {alert.target_price} USDT)."
            )
            await _save_and_broadcast(alert.user_id, NotificationType.PRICE_ALERT, title, body)

            # Email
            if await _get_email_pref(alert.user_id, "email_on_price_alert"):
                email = await _get_user_email(alert.user_id)
                if email:
                    await send_price_alert_email(
                        to_email=email,
                        symbol=symbol,
                        condition=alert.condition.value,
                        target_price=str(alert.target_price),
                        current_price=str(current_price),
                    )



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
