"""
Simulation Engine — main FastAPI application.

Lifespan:
  1. Connect to Redis pool.
  2. Start OrderBookMirror (subscribes to all market.orderbook.* / market.ticker.* channels).
  3. Start order_subscriber (subscribes to orders.simulation channel).
  4. Serve WebSocket endpoint /ws/user/orders for real-time fill push.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .redis_client import close_redis_pool, get_redis_pool
from .routers.ws import router as ws_router
from .services.futures_handler import PositionMonitor
from .services.limit_handler import LimitOrderHandler
from .services.order_book_mirror import OrderBookMirror
from .services.order_subscriber import run_order_subscriber
from .services.stop_loss_handler import StopLossHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = get_redis_pool()
    mirror = OrderBookMirror()
    limit_handler = LimitOrderHandler()
    stop_loss_handler = StopLossHandler()
    position_monitor = PositionMonitor()

    symbols = settings.symbols_list
    log.info("simulation-engine starting, symbols: %s", symbols)

    # Start background tasks
    mirror_task = asyncio.create_task(mirror.start(redis_client, symbols))
    subscriber_task = asyncio.create_task(
        run_order_subscriber(redis_client, mirror, limit_handler, stop_loss_handler)
    )
    monitor_task = asyncio.create_task(position_monitor.start(redis_client))

    # Attach to app state so routers can access them if needed
    app.state.mirror = mirror
    app.state.limit_handler = limit_handler
    app.state.stop_loss_handler = stop_loss_handler

    yield

    # Shutdown
    mirror_task.cancel()
    subscriber_task.cancel()
    monitor_task.cancel()
    for task in (mirror_task, subscriber_task, monitor_task):
        try:
            await task
        except asyncio.CancelledError:
            pass
    await close_redis_pool()
    log.info("simulation-engine stopped")


app = FastAPI(
    title="Simulation Engine",
    description="Fills simulation orders against live Binance order book depth.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(ws_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "simulation-engine"}
