import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .redis_client import close_redis_pool, get_redis_pool
from .routers import alerts, notifications, ws
from .services.event_listener import EventListener

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_listener_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _listener_task
    redis = get_redis_pool()
    listener = EventListener()
    _listener_task = asyncio.create_task(listener.start(redis))
    log.info("Notification service started")
    yield
    if _listener_task:
        _listener_task.cancel()
    await close_redis_pool()


app = FastAPI(title="XChange Notification Service", lifespan=lifespan, redirect_slashes=False)

app.include_router(notifications.router)
app.include_router(alerts.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
