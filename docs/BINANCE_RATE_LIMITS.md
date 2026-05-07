# Binance API Rate Limit Reference

**Source:** [Binance Spot API Docs](https://developers.binance.com/docs/binance-spot-api-docs)
**Last verified:** May 2026

This document is the single source of truth for all Binance rate-limit rules
relevant to the XChange platform. Every team member or automated agent building
code that touches Binance **must** consult this file first.

---

## 1. REST API Limits

### 1.1 How the Limit System Works

Binance does not count raw requests equally. Each endpoint has a **weight** —
heavier endpoints cost more. The system tracks three independent counters per IP:

| Counter name | Resets every | What it counts |
|---|---|---|
| `REQUEST_WEIGHT` | 1 minute | Sum of weights of all requests |
| `RAW_REQUESTS` | 5 minutes | Total number of requests, regardless of weight |
| `ORDERS` | 10 seconds / 24 hours | Order placement requests only |

> **Live values:** Always call `GET /api/v3/exchangeInfo` on startup to read the
> current limits from the `rateLimits` array. Do **not** hardcode the numbers
> below — Binance can change them without notice.

### 1.2 Known Current Limits (as of May 2026)

| Counter | Limit | Interval |
|---|---|---|
| `REQUEST_WEIGHT` | **6,000** | Per minute |
| `RAW_REQUESTS` | **61,000** | Per 5 minutes |
| `ORDERS` | **100** | Per 10 seconds |
| `ORDERS` | **200,000** | Per 24 hours |

> **Our safe working target:** Stay under **1,200 weight per minute** in all
> automated scripts. This is 20% of the current 6,000 limit, giving a 5× safety
> margin and protecting us even if Binance reverts to the old 1,200 limit.

### 1.3 How to Read Your Current Usage

Every REST response includes this header:

```
X-MBX-USED-WEIGHT-1M: 42
```

That tells you how much weight has been used in the current minute window.
Phase 4 code must read this header and slow down automatically if it gets
close to the limit.

### 1.4 Endpoint Weights We Use

| Endpoint | Method | Weight | Notes |
|---|---|---|---|
| `/api/v3/klines` | GET | **2** | Used by backfill script. Max 1000 candles per call. |
| `/api/v3/exchangeInfo` | GET | 20 | Called once on startup to read live limits. |
| `/api/v3/depth` | GET | 5–250 | Weight depends on `limit` param. We use limit=20 → weight 5. |
| `/api/v3/ticker/24hr` (single symbol) | GET | 2 | Ticker for one pair. |
| `/api/v3/order` (POST) | POST | 1 | Live order placement — Phase 4 only. |
| `/api/v3/order` (GET) | GET | 4 | Order status check — Phase 4 only. |
| `/api/v3/openOrders` | GET | 6 | All open orders for one symbol — Phase 4. |
| `/api/v3/account` | GET | 20 | Account balance — Phase 4 only. |

> **Backfill maths:** 10 symbols × 4 intervals × ~55 pages average = ~2,200 calls
> × weight 2 = ~4,400 weight total. Spread at our 20 weight/sec target
> (1,200/min), the full backfill takes roughly **4 minutes**. Without a limiter
> it would finish in seconds but risk a 429 ban.

---

## 2. REST Error Codes and Ban Rules

| HTTP Code | Meaning | What to do |
|---|---|---|
| **429** | Weight limit exceeded | Stop immediately. Read `Retry-After` header. Wait that many seconds before retrying. |
| **418** | IP temporarily banned | IP ban is in effect. Read `Retry-After` header. Do NOT retry until the ban lifts. Log a critical alert. |

**Ban escalation schedule:**
- First offence: 2-minute ban
- Repeat offences: escalates to 5 min → 30 min → 1 hour → 6 hours → 1 day → 3 days

> A 429 that is not respected (i.e. you keep sending requests) will immediately
> trigger an 418 ban. Never ignore a 429.

**Our mandatory response to 429/418:**
1. Log a critical-level error with the `Retry-After` value.
2. Sleep for exactly `Retry-After` seconds before the next request.
3. Reset the token-bucket to zero tokens after waking up (assume the whole
   minute window was poisoned).

---

## 3. WebSocket Stream Limits

These apply to connections to `wss://stream.binance.com:9443`.

| Rule | Limit |
|---|---|
| Max streams per connection | **1,024** |
| Incoming control messages per second | **5** (PING / PONG / subscribe / unsubscribe) |
| New connections per 5 minutes per IP | **300** |
| Maximum connection lifetime | **24 hours** (Binance disconnects after this) |

**Ping/Pong rules:**
- Binance sends a PING frame every **20 seconds**.
- Our code must send a PONG back. The `websockets` library does this
  automatically by default.
- If no PONG is received within **1 minute**, Binance closes the connection.

**24-hour disconnect:**
- Binance sends a `serverShutdown` event **10 minutes before** the 24-hour
  forced disconnect.
- Our `binance_feed.py` reconnection loop already handles this — any disconnect
  triggers an exponential-backoff reconnect.

**Our current usage:**
- 1 connection (well within the 300 new-connections/5min limit on restarts)
- 10 symbols × 5 stream types (ticker + depth20 + kline_1m + kline_5m + kline_1h
  + kline_1d) = **50 streams** (well within the 1,024 limit)
- We send zero incoming control messages during normal operation (no dynamic
  subscribe/unsubscribe), so the 5 msg/sec rule is never at risk

---

## 4. Rate Limiter Implementation — Token Bucket

### 4.1 Concept

A **token bucket** is a counter that:
- Starts full (at its `capacity`).
- Drains by the `cost` of each request when a request is made.
- Refills automatically over time at a fixed `rate` (tokens per second).
- If the bucket doesn't have enough tokens, the caller **waits** until it does.

This naturally enforces a long-run average rate while allowing short bursts up
to the bucket capacity.

### 4.2 Parameters We Use

| Scenario | Capacity | Rate | Cost per call | Effect |
|---|---|---|---|---|
| **Backfill script (now)** | 1,200 weight | 20 weight/sec | 2 (klines) | ≤1,200 weight/min on average, bursts up to 1,200 |
| **Phase 4 market data REST** | 1,200 weight | 20 weight/sec | varies | Same conservative budget |
| **Phase 4 order placement** | 100 orders | 10 orders/sec | 1 | ≤100 orders/10 sec |

> The capacity of 1,200 is intentionally conservative. Even though the current
> Binance limit is 6,000, we target 1,200 so that:
> (a) a future Binance limit rollback cannot surprise us, and
> (b) Phase 4 code from different services shares the same headroom.

### 4.3 Reference Python Implementation

This is the canonical `TokenBucket` class. Any future service that calls Binance
REST **must** use this pattern (or the Phase 4 Redis-backed version described
in Section 5).

```python
import asyncio
import time


class TokenBucket:
    """
    Async token-bucket rate limiter.

    capacity : float  — maximum tokens the bucket can hold (burst ceiling)
    rate     : float  — tokens added per second (long-run average rate)

    Usage:
        limiter = TokenBucket(capacity=1200, rate=20)
        await limiter.acquire(tokens=2)   # costs 2 weight (e.g. /api/v3/klines)
        response = await client.get(...)
    """

    def __init__(self, capacity: float, rate: float) -> None:
        self.capacity = float(capacity)
        self.rate = float(rate)
        self._tokens: float = float(capacity)
        self._last_refill: float = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        """Block until `tokens` are available, then consume them."""
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(
                    self.capacity, self._tokens + elapsed * self.rate
                )
                self._last_refill = now

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                deficit = tokens - self._tokens
                wait = deficit / self.rate

            # Sleep outside the lock so other coroutines are not blocked
            await asyncio.sleep(wait)
```

### 4.4 Handling 429 / 418 in Code

```python
async def safe_get(client, url, params, limiter, cost=1):
    """Wrapper that respects 429/418 responses."""
    await limiter.acquire(tokens=cost)
    resp = await client.get(url, params=params, timeout=30)

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        logger.critical("Binance 429 — backing off %ds", retry_after)
        await asyncio.sleep(retry_after)
        raise RuntimeError("Rate limit hit — caller should retry")

    if resp.status_code == 418:
        retry_after = int(resp.headers.get("Retry-After", 300))
        logger.critical("Binance 418 IP BAN — waiting %ds", retry_after)
        await asyncio.sleep(retry_after)
        raise RuntimeError("IP banned — caller should retry")

    resp.raise_for_status()
    return resp
```

---

## 5. Phase 4 Upgrade — Redis-Backed Shared Limiter

In Phase 4, the **execution service** will also call Binance REST (for live order
routing via CCXT). At that point two Docker services share the same IP, so their
weight usage is **combined** from Binance's perspective.

A single in-process `TokenBucket` is not enough — each service only knows its
own usage. The solution is a Redis Lua script that implements the token bucket
atomically in Redis, shared by all services.

**Planned design:**
- Redis key: `binance:rate_limiter:weight` (sorted set or string with TTL)
- Lua script atomically refills and deducts tokens on each acquire call
- If tokens are insufficient, the script returns the wait time; Python sleeps
  and retries
- All services import a shared `redis_token_bucket.py` utility from a common
  `libs/` folder

This work is tracked in Sprint 16 (Execution Service). Do not build it until
then.

---

## 6. What NOT to Do

- ❌ Do not call `time.sleep()` (blocking) — always use `await asyncio.sleep()`
- ❌ Do not hardcode weight limits — read from `exchangeInfo` or use the 1,200
  conservative target
- ❌ Do not ignore a 429 response and keep sending requests
- ❌ Do not open multiple WebSocket connections to the same stream
- ❌ Do not subscribe/unsubscribe rapidly (5 msg/sec connection-level limit)
- ❌ Do not add a Binance REST call to any service outside `market-data-service`
  until Phase 4 is planned and this document is updated

---

## 7. Quick Reference Card

```
REST weight budget  :  stay ≤ 1,200 weight/min (target), hard limit 6,000/min
klines call cost    :  2 weight
Token bucket params :  capacity=1200, rate=20 weight/sec
429 action          :  stop + sleep Retry-After seconds
418 action          :  stop + sleep Retry-After seconds + alert

WebSocket streams   :  max 1,024 per connection (we use 50)
WS control msgs     :  max 5/sec per connection (we send 0 during normal run)
WS new connections  :  max 300 per 5 min per IP
WS lifetime         :  24 hours — reconnect on serverShutdown event
```
