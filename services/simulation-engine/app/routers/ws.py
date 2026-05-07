"""
WebSocket endpoint: /ws/user/orders

Streams real-time fill events to the authenticated user by subscribing to
the Redis Pub/Sub channel `fills.{user_id}`.

Authentication: Bearer token passed as query parameter `token=<jwt>` because
the browser WebSocket API cannot set custom headers.
"""
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from ..config import settings
from ..redis_client import get_redis_pool

log = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/user/orders")
async def user_order_fills(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    # ── Authenticate ──────────────────────────────────────────────────────────
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    log.info("ws/user/orders: user %s connected", user_id)

    redis_client = get_redis_pool()
    pubsub = redis_client.pubsub()
    channel = f"fills.{user_id}"
    await pubsub.subscribe(channel)

    try:
        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            data_bytes: bytes = raw["data"]
            try:
                payload_json = json.loads(data_bytes)
                await websocket.send_json(payload_json)
            except Exception:
                # If client disconnected, the send will raise — exit gracefully
                break
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        log.info("ws/user/orders: user %s disconnected", user_id)
