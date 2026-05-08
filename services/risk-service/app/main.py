import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .redis_client import close_redis_pool, get_redis_pool
from .services.risk_monitor import RiskMonitor

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_monitor_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _monitor_task
    redis = get_redis_pool()
    monitor = RiskMonitor()
    _monitor_task = asyncio.create_task(monitor.start(redis))
    log.info("Risk service started")
    yield
    if _monitor_task:
        _monitor_task.cancel()
    await close_redis_pool()


app = FastAPI(title="XChange Risk Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
