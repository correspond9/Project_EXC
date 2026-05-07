"""
WebSocket endpoints — real-time market data streaming to browser clients.

Each endpoint:
  1. Accepts the WebSocket connection
  2. Opens a Redis Pub/Sub subscription on the relevant channel
  3. Forwards every published message directly to the client
  4. Cleans up the subscription when the client disconnects

Channel naming:
  market.ticker.<SYMBOL>              → /ws/market/{symbol}/ticker
  market.orderbook.<SYMBOL>           → /ws/market/{symbol}/orderbook
  market.kline.<SYMBOL>.<INTERVAL>    → /ws/market/{symbol}/kline/{interval}
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..redis_client import get_redis_pool

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket — Market Data"])

_VALID_INTERVALS = {"1m", "5m", "1h", "1d"}


async def _stream_channel(websocket: WebSocket, channel: str) -> None:
    """
    Subscribes to a Redis Pub/Sub channel and forwards each message
    to the connected WebSocket client until the client disconnects.
    """
    redis = await get_redis_pool()
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                text = data.decode() if isinstance(data, bytes) else data
                await websocket.send_text(text)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WebSocket stream ended for channel %s: %s", channel, exc)
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:
            pass


# ── WS /ws/market/{symbol}/ticker ─────────────────────────────────────────────

@router.websocket("/ws/market/{symbol}/ticker")
async def ws_ticker(websocket: WebSocket, symbol: str) -> None:
    """Stream live 24h ticker updates for a symbol."""
    await websocket.accept()
    channel = f"market.ticker.{symbol.upper()}"
    await _stream_channel(websocket, channel)


# ── WS /ws/market/{symbol}/orderbook ─────────────────────────────────────────

@router.websocket("/ws/market/{symbol}/orderbook")
async def ws_orderbook(websocket: WebSocket, symbol: str) -> None:
    """Stream live order book (top 20 bid/ask) updates for a symbol."""
    await websocket.accept()
    channel = f"market.orderbook.{symbol.upper()}"
    await _stream_channel(websocket, channel)


# ── WS /ws/market/{symbol}/kline/{interval} ──────────────────────────────────

@router.websocket("/ws/market/{symbol}/kline/{interval}")
async def ws_kline(websocket: WebSocket, symbol: str, interval: str) -> None:
    """Stream live candle (OHLCV) updates for a symbol and interval."""
    if interval not in _VALID_INTERVALS:
        await websocket.accept()
        await websocket.send_text(
            f'{{"error": "Invalid interval \'{interval}\'. '
            f'Valid options: {sorted(_VALID_INTERVALS)}"}}'
        )
        await websocket.close(code=1008)
        return

    await websocket.accept()
    channel = f"market.kline.{symbol.upper()}.{interval}"
    await _stream_channel(websocket, channel)
