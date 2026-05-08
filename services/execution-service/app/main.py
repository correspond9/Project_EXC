"""Execution Service — live order routing to Binance via CCXT."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import settings
from .services.binance_client import BinanceClient
from .services.deribit_client import DeribitClient
from .services.options_router import OptionsOrderRouter
from .services.order_router import LiveOrderRouter
from .services.reconciliation import reconciliation_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Execution service starting — BINANCE TESTNET=%s, DERIBIT TESTNET=%s",
        settings.BINANCE_TESTNET,
        settings.DERIBIT_TESTNET,
    )
    binance_client = BinanceClient()
    deribit_client = DeribitClient()
    router = LiveOrderRouter(binance_client)
    options_router = OptionsOrderRouter(deribit_client)

    tasks = [
        asyncio.create_task(router.run(), name="order-router"),
        asyncio.create_task(reconciliation_loop(router, binance_client), name="reconciliation"),
        asyncio.create_task(options_router.run(), name="options-router"),
    ]
    yield
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await binance_client.close()
    await deribit_client.close()
    logger.info("Execution service shut down")


app = FastAPI(
    title="Execution Service",
    description="Routes live orders to Binance (spot/futures) and Deribit (options) via CCXT.",
    version="1.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "execution-service",
        "version": "1.1.0",
        "binance_testnet": settings.BINANCE_TESTNET,
        "deribit_testnet": settings.DERIBIT_TESTNET,
        "binance_configured": bool(settings.BINANCE_API_KEY),
        "deribit_configured": bool(settings.DERIBIT_API_KEY),
    }
