"""
In-memory mirror of the Binance order book and last ticker price for each symbol.

Subscribes to Redis Pub/Sub channels:
  - market.orderbook.{symbol}  → updates self._books[symbol]
  - market.ticker.{symbol}     → updates self._tickers[symbol]

Consumers register per-symbol queues to receive updates.  When the book/ticker
changes the mirror puts the new snapshot into every registered queue.
"""
import asyncio
import json
import logging
from typing import Any

import redis.asyncio as aioredis

log = logging.getLogger(__name__)


class OrderBookMirror:
    def __init__(self) -> None:
        self._books: dict[str, dict] = {}
        self._tickers: dict[str, dict] = {}

        # Per-symbol queues registered by fill handlers / watchers
        self._book_subs: dict[str, list[asyncio.Queue]] = {}
        self._ticker_subs: dict[str, list[asyncio.Queue]] = {}

        self._lock = asyncio.Lock()

    # ── public read API ────────────────────────────────────────────────────────

    def get_book(self, symbol: str) -> dict | None:
        """Return the latest order book snapshot for a Binance-style symbol."""
        return self._books.get(symbol)

    def get_ticker(self, symbol: str) -> dict | None:
        """Return the latest ticker snapshot (contains 'c' = last price)."""
        return self._tickers.get(symbol)

    # ── subscription API ───────────────────────────────────────────────────────

    def subscribe_book(self, symbol: str) -> asyncio.Queue:
        """Return a Queue that receives every order-book snapshot for *symbol*."""
        q: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._book_subs.setdefault(symbol, []).append(q)
        return q

    def unsubscribe_book(self, symbol: str, q: asyncio.Queue) -> None:
        subs = self._book_subs.get(symbol, [])
        try:
            subs.remove(q)
        except ValueError:
            pass

    def subscribe_ticker(self, symbol: str) -> asyncio.Queue:
        """Return a Queue that receives every ticker snapshot for *symbol*."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._ticker_subs.setdefault(symbol, []).append(q)
        return q

    def unsubscribe_ticker(self, symbol: str, q: asyncio.Queue) -> None:
        subs = self._ticker_subs.get(symbol, [])
        try:
            subs.remove(q)
        except ValueError:
            pass

    # ── background task ────────────────────────────────────────────────────────

    async def start(self, redis_client: aioredis.Redis, symbols: list[str]) -> None:
        """Subscribe to Redis Pub/Sub and feed the in-memory mirror forever."""
        channels = (
            [f"market.orderbook.{s}" for s in symbols]
            + [f"market.ticker.{s}" for s in symbols]
        )
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(*channels)
        log.info("OrderBookMirror subscribed to %d channels", len(channels))

        async for raw in pubsub.listen():
            if raw["type"] != "message":
                continue
            channel: str = (
                raw["channel"].decode() if isinstance(raw["channel"], bytes) else raw["channel"]
            )
            data_bytes: bytes = raw["data"]
            try:
                snapshot: dict[str, Any] = json.loads(data_bytes)
            except Exception:
                continue

            if channel.startswith("market.orderbook."):
                sym = channel[len("market.orderbook."):]
                self._books[sym] = snapshot
                await self._notify(self._book_subs.get(sym, []), snapshot)

            elif channel.startswith("market.ticker."):
                sym = channel[len("market.ticker."):]
                self._tickers[sym] = snapshot
                await self._notify(self._ticker_subs.get(sym, []), snapshot)

    # ── helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    async def _notify(queues: list[asyncio.Queue], snapshot: dict) -> None:
        for q in list(queues):
            try:
                q.put_nowait(snapshot)
            except asyncio.QueueFull:
                # Drop the oldest entry to make room for the fresh one
                try:
                    q.get_nowait()
                    q.put_nowait(snapshot)
                except Exception:
                    pass
