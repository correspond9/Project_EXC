"""CCXT Binance client wrapper supporting both Spot and Futures markets."""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Any

import ccxt.async_support as ccxt

from ..config import settings

logger = logging.getLogger(__name__)


class BinanceClient:
    """Async CCXT wrapper for Binance Spot and Futures."""

    def __init__(self) -> None:
        common = {
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_API_SECRET,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
        futures_common = {**common, "options": {"defaultType": "future"}}

        if settings.BINANCE_TESTNET:
            common["options"]["adjustForTimeDifference"] = True
            futures_common["options"]["adjustForTimeDifference"] = True
            self._spot = ccxt.binance({**common, "sandbox": True})
            self._futures = ccxt.binance({**futures_common, "sandbox": True})
        else:
            self._spot = ccxt.binance(common)
            self._futures = ccxt.binance(futures_common)

    async def close(self) -> None:
        await self._spot.close()
        await self._futures.close()

    # ── Spot ──────────────────────────────────────────────────────────────────

    async def place_spot_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Decimal | None = None,
    ) -> dict[str, Any]:
        """Place a spot order. Returns the raw CCXT order dict."""
        ccxt_type = self._map_order_type(order_type)
        params: dict[str, Any] = {}
        price_arg = float(price) if price and ccxt_type != "market" else None
        try:
            return await self._spot.create_order(
                symbol=self._fmt_symbol(symbol),
                type=ccxt_type,
                side=side.lower(),
                amount=float(quantity),
                price=price_arg,
                params=params,
            )
        except ccxt.BaseError as exc:
            logger.error("Binance spot order error: %s", exc)
            raise

    async def fetch_spot_order(self, external_id: str, symbol: str) -> dict[str, Any]:
        return await self._spot.fetch_order(external_id, self._fmt_symbol(symbol))

    async def cancel_spot_order(self, external_id: str, symbol: str) -> dict[str, Any]:
        return await self._spot.cancel_order(external_id, self._fmt_symbol(symbol))

    async def fetch_spot_balance(self) -> dict[str, Any]:
        return await self._spot.fetch_balance()

    # ── Futures ───────────────────────────────────────────────────────────────

    async def place_futures_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Decimal | None = None,
        leverage: int = 1,
        reduce_only: bool = False,
    ) -> dict[str, Any]:
        """Place a futures (perpetual) order."""
        ccxt_type = self._map_order_type(order_type)
        price_arg = float(price) if price and ccxt_type != "market" else None
        params: dict[str, Any] = {"reduceOnly": reduce_only}
        try:
            await self._futures.set_leverage(leverage, self._fmt_symbol(symbol))
        except ccxt.BaseError:
            pass  # Leverage may already be set; non-fatal
        try:
            return await self._futures.create_order(
                symbol=self._fmt_symbol(symbol),
                type=ccxt_type,
                side=side.lower(),
                amount=float(quantity),
                price=price_arg,
                params=params,
            )
        except ccxt.BaseError as exc:
            logger.error("Binance futures order error: %s", exc)
            raise

    async def fetch_futures_order(self, external_id: str, symbol: str) -> dict[str, Any]:
        return await self._futures.fetch_order(external_id, self._fmt_symbol(symbol))

    async def cancel_futures_order(self, external_id: str, symbol: str) -> dict[str, Any]:
        return await self._futures.cancel_order(external_id, self._fmt_symbol(symbol))

    async def fetch_futures_balance(self) -> dict[str, Any]:
        return await self._futures.fetch_balance()

    async def fetch_open_futures_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        sym = self._fmt_symbol(symbol) if symbol else None
        return await self._futures.fetch_open_orders(sym)

    async def fetch_open_spot_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        sym = self._fmt_symbol(symbol) if symbol else None
        return await self._spot.fetch_open_orders(sym)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt_symbol(symbol: str) -> str:
        """Convert BTCUSDT → BTC/USDT for CCXT."""
        if "/" in symbol:
            return symbol
        # Assume last 4 chars are quote currency (USDT, BUSD) unless 3 char (BTC, ETH)
        for quote in ("USDT", "BUSD", "USDC", "BNB", "BTC", "ETH"):
            if symbol.endswith(quote):
                base = symbol[: -len(quote)]
                return f"{base}/{quote}"
        return symbol

    @staticmethod
    def _map_order_type(order_type: str) -> str:
        mapping = {
            "MARKET": "market",
            "LIMIT": "limit",
            "STOP_LOSS": "stop_market",
            "TAKE_PROFIT": "take_profit_market",
        }
        return mapping.get(order_type.upper(), "market")
