"""
Portfolio Service — main entry point.
Manages portfolio holdings, P&L calculation, and trade history.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .redis_client import close_redis_pool
from .routers.history import router as history_router
from .routers.portfolio import router as portfolio_router
from .routers.ws import router as ws_router
from .services.fill_listener import run_fill_listener
from .services.pnl_scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_fill_listener_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _fill_listener_task
    log.info("portfolio-service: starting up")

    # Start background fill listener
    _fill_listener_task = asyncio.create_task(run_fill_listener())

    # Start daily P&L snapshot scheduler
    start_scheduler()

    yield

    # Graceful shutdown
    log.info("portfolio-service: shutting down")
    stop_scheduler()
    if _fill_listener_task and not _fill_listener_task.done():
        _fill_listener_task.cancel()
        try:
            await _fill_listener_task
        except asyncio.CancelledError:
            pass
    await close_redis_pool()


app = FastAPI(
    title="Portfolio Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(portfolio_router)
app.include_router(history_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "portfolio-service"}
