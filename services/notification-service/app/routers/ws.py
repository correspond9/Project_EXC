"""
WebSocket endpoint: /ws/user/notifications?token=<JWT>

Pushes new notification JSON objects to connected clients as they arrive.
The event_listener writes Notification records AND calls broadcast()
to push to all connected sockets for that user.
"""
import asyncio
import uuid
from collections import defaultdict
from typing import DefaultDict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from ..config import settings

router = APIRouter(tags=["notifications-ws"])

# {user_id_str: set of active WebSocket connections}
_connections: DefaultDict[str, Set[WebSocket]] = defaultdict(set)


def _decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub", None)
    except JWTError:
        return None


@router.websocket("/ws/user/notifications")
async def notifications_ws(websocket: WebSocket, token: str = ""):
    user_id_str = _decode_token(token)
    if not user_id_str:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    _connections[user_id_str].add(websocket)
    try:
        # Keep alive — client may send pings; we just discard them
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        _connections[user_id_str].discard(websocket)


async def broadcast(user_id_str: str, payload: dict) -> None:
    """Push a notification payload to all active sockets for the user."""
    stale = set()
    for ws in list(_connections.get(user_id_str, set())):
        try:
            await ws.send_json(payload)
        except Exception:
            stale.add(ws)
    _connections[user_id_str] -= stale
