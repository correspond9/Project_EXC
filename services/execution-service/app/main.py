"""Execution Service — live order routing to Binance via CCXT."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .services.binance_client import BinanceClient
from .services.order_router import LiveOrderRouter
from .services.reconciliation import reconciliation_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Execution service starting — TESTNET=%s, API_KEY=%s",
        settings.BINANCE_TESTNET,
        "***" if settings.BINANCE_API_KEY else "NOT SET",
    )
    client = BinanceClient()
    router = LiveOrderRouter(client)

    tasks = [
        asyncio.create_task(router.run(), name="order-router"),
        asyncio.create_task(reconciliation_loop(router, client), name="reconciliation"),
    ]
    yield
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await client.close()
    logger.info("Execution service shut down")


app = FastAPI(
    title="Execution Service",
    description="Routes live orders to Binance via CCXT.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "execution-service",
        "testnet": settings.BINANCE_TESTNET,
        "exchange_configured": bool(settings.BINANCE_API_KEY),
    }
