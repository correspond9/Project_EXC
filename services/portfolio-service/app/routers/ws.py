"""
ws.py — WebSocket /ws/user/portfolio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pushes live unrealised P&L + total portfolio value to the browser.
Subscribes to Redis pattern ``market.ticker.*`` so it can react to
every price tick and re-compute unrealised P&L for the user's holdings.

Connection:  WS /ws/user/portfolio?token=<jwt>
Push format:
{
  "type": "portfolio_update",
  "holdings": [
      {"asset": "BTC", "quantity": "0.5", "average_entry_price": "60000", ...},
      ...
  ],
  "summary": {
      "total_portfolio_value": "...",
      "total_unrealised_pnl": "...",
      "total_realised_pnl": "...",
      "usdt_balance": "..."
  }
}
"""
import asyncio
import json
import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy import select

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.portfolio import PortfolioHolding
from ..models.wallet import SimulationWallet
from ..redis_client import get_redis_pool

router = APIRouter()
log = logging.getLogger(__name__)

_EXECUTION_MODE = "SIMULATION"


def _decode_token(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        return uuid.UUID(sub) if sub else None
    except (JWTError, ValueError):
        return None


async def _get_price_from_redis(asset: str) -> Decimal:
    redis = get_redis_pool()
    raw = await redis.hget(f"ticker:{asset}USDT", "c")
    if raw:
        try:
            return Decimal(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
        except Exception:  # noqa: BLE001
            pass
    return Decimal("0")


async def _build_snapshot(user_id: uuid.UUID) -> dict:
    async with AsyncSessionLocal() as session:
        h_result = await session.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.user_id == user_id,
                PortfolioHolding.execution_mode == _EXECUTION_MODE,
                PortfolioHolding.quantity > 0,
            )
        )
        holdings = h_result.scalars().all()

        w_result = await session.execute(
            select(SimulationWallet.balance).where(
                SimulationWallet.user_id == user_id,
                SimulationWallet.currency == "USDT",
            )
        )
        usdt_balance = Decimal(str(w_result.scalar_one_or_none() or "0"))

    total_unrealised = Decimal("0")
    total_realised = Decimal("0")
    total_value = Decimal("0")
    holdings_out = []

    for h in holdings:
        qty = Decimal(str(h.quantity))
        avg = Decimal(str(h.average_entry_price))
        price = await _get_price_from_redis(h.asset)
        unrealised = (price - avg) * qty if qty > 0 and avg > 0 else Decimal("0")
        value = qty * price

        total_unrealised += unrealised
        total_realised += Decimal(str(h.total_realised_pnl))
        total_value += value

        holdings_out.append(
            {
                "asset": h.asset,
                "quantity": str(qty),
                "average_entry_price": str(avg),
                "current_price": str(price),
                "value_usdt": str(value),
                "unrealised_pnl": str(unrealised),
                "total_realised_pnl": str(h.total_realised_pnl),
            }
        )

    total_value += usdt_balance
    return {
        "type": "portfolio_update",
        "holdings": holdings_out,
        "summary": {
            "total_portfolio_value": str(total_value),
            "holdings_value": str(total_value - usdt_balance),
            "usdt_balance": str(usdt_balance),
            "total_unrealised_pnl": str(total_unrealised),
            "total_realised_pnl": str(total_realised),
            "todays_pnl_delta": "0",
        },
    }


@router.websocket("/ws/user/portfolio")
async def portfolio_ws(websocket: WebSocket, token: str = ""):
    user_id = _decode_token(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    log.info("portfolio_ws: user %s connected", user_id)

    redis = get_redis_pool()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("market.ticker.*")

    try:
        # Send initial snapshot immediately
        snapshot = await _build_snapshot(user_id)
        await websocket.send_text(json.dumps(snapshot))

        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            # Re-compute portfolio on every ticker update
            try:
                snapshot = await _build_snapshot(user_id)
                await websocket.send_text(json.dumps(snapshot))
            except Exception as exc:  # noqa: BLE001
                log.error("portfolio_ws: error building snapshot — %s", exc)
                break

    except WebSocketDisconnect:
        log.info("portfolio_ws: user %s disconnected", user_id)
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.punsubscribe("market.ticker.*")
        try:
            await websocket.close()
        except Exception:  # noqa: BLE001
            pass
