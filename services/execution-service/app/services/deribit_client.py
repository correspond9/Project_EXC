"""
Sprint 22 — Deribit CCXT wrapper for options order routing.

Supports:
- Buying / selling options by Deribit instrument name (e.g. BTC-27DEC24-100000-C)
- Fetching order status
- Cancelling orders

Deribit uses different symbol conventions from Binance:
- Options are identified by full instrument name, not a base/quote pair.
- CCXT normalises these as the symbol.

Safety: DERIBIT_TESTNET defaults to True — no real Deribit calls until
explicitly set to False in the environment.
"""
from __future__ import annotations

import ccxt.async_support as ccxt

from ..config import settings


def _build_exchange() -> ccxt.deribit:
    exchange = ccxt.deribit(
        {
            "apiKey": settings.DERIBIT_API_KEY,
            "secret": settings.DERIBIT_API_SECRET,
        }
    )
    if settings.DERIBIT_TESTNET:
        exchange.set_sandbox_mode(True)
    return exchange


class DeribitClient:
    """Async Deribit CCXT wrapper. Create one instance per execution task."""

    def __init__(self) -> None:
        self._exchange = _build_exchange()

    async def close(self) -> None:
        await self._exchange.close()

    async def place_option(
        self,
        instrument: str,
        side: str,  # "buy" | "sell"
        amount: float,
        price: float | None = None,
        order_type: str = "limit",
    ) -> dict:
        """
        Place a Deribit options order.

        Args:
            instrument: Full Deribit instrument name, e.g. "BTC-27DEC24-100000-C"
            side:       "buy" or "sell"
            amount:     Contract amount (in underlying units on Deribit)
            price:      Limit price in USD. Pass None for market orders.
            order_type: "limit" | "market"

        Returns:
            Raw CCXT order dict.
        """
        # Deribit market = option instruments use instrument name directly as symbol
        if order_type == "market":
            order = await self._exchange.create_order(
                symbol=instrument,
                type="market",
                side=side,
                amount=amount,
            )
        else:
            if price is None:
                raise ValueError("price is required for limit options orders")
            order = await self._exchange.create_order(
                symbol=instrument,
                type="limit",
                side=side,
                amount=amount,
                price=price,
            )
        return order

    async def fetch_order(self, order_id: str, instrument: str) -> dict:
        """Fetch an existing order by ID."""
        return await self._exchange.fetch_order(order_id, symbol=instrument)

    async def cancel_order(self, order_id: str, instrument: str) -> dict:
        """Cancel an open order by ID."""
        return await self._exchange.cancel_order(order_id, symbol=instrument)

    async def fetch_positions(self, currency: str = "BTC") -> list[dict]:
        """Fetch all open options positions for a given underlying currency."""
        # Deribit: fetchPositions with currency filter
        return await self._exchange.fetch_positions(params={"currency": currency})
