import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .redis_client import close_redis_pool, get_redis_pool
from .routers import market, ws
from .services.binance_feed import run_binance_feed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_feed_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _feed_task
    # Warm up Redis connection pool
    await get_redis_pool()
    # Start Binance WebSocket feed as a background asyncio task
    _feed_task = asyncio.create_task(run_binance_feed())
    logger.info("Binance feed task started.")
    yield
    # Graceful shutdown
    if _feed_task and not _feed_task.done():
        _feed_task.cancel()
        try:
            await _feed_task
        except asyncio.CancelledError:
            pass
    await close_redis_pool()
    logger.info("Market data service shutdown complete.")


app = FastAPI(
    title="Market Data Service",
    description=(
        "Streams real-time prices from Binance WebSocket. "
        "Publishes to Redis Pub/Sub. "
        "Exposes REST endpoints for tickers, order books, and OHLCV history. "
        "Exposes WebSocket endpoints for live streaming to browser clients."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(market.router)
app.include_router(ws.router)


@app.get("/health", tags=["Health"])
def health_check():
    feed_running = _feed_task is not None and not _feed_task.done()
    return {
        "status": "ok",
        "service": "market-data-service",
        "binance_feed": "running" if feed_running else "stopped",
    }
