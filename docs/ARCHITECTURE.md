# XChange Platform — System Architecture
**Version:** 1.1  
**Date:** 08-May-2026  
**Parent Document:** [MASTER_PLAN.md](./MASTER_PLAN.md)

---

## 1. Architecture Principles

1. **Execution Mode is the ONLY difference** between Simulation and Live. Every other service is mode-agnostic.
2. **Mode is account-level, Admin-controlled.** An account has a `trading_mode` flag. Only Admin can change it.
3. **All services are containerised** from day 1 (Docker). No service runs directly on the host OS.
4. **Stateless API layer.** All state lives in PostgreSQL or Redis. Any API container can be restarted without data loss.
5. **Real prices always.** Market data always comes from Binance WebSocket — in both simulation and live mode.
6. **Security first.** Authentication, authorisation, input validation, and rate limiting are not optional.

---

## 2. Service Map

| Service | Language | Purpose |
|---------|----------|---------|
| `api-gateway` | Nginx | Reverse proxy, SSL, rate limiting, routing |
| `user-service` | FastAPI (Python) | Registration, login, JWT, profile, KYC |
| `market-data-service` | FastAPI (Python) | Binance WebSocket feed, OHLCV storage, price broadcast |
| `order-service` | FastAPI (Python) | Order creation, validation, routing to execution engine |
| `simulation-engine` | FastAPI (Python) | Paper trading — fills orders at real market price |
| `execution-service` | FastAPI (Python) | Routes live orders to Binance via CCXT |
| `portfolio-service` | FastAPI (Python) | Positions, P&L, balance calculations |
| `wallet-service` | FastAPI (Python) | Simulation balance management; real wallet in Phase 4 |
| `risk-service` | FastAPI (Python) | Margin monitoring, liquidation triggers |
| `notification-service` | FastAPI (Python) | Email, in-app, push notifications |
| `admin-service` | FastAPI (Python) | Admin panel API — user management, platform settings |
| `web-frontend` | Next.js (React/TS) | Web trading interface |
| `mobile-app` | React Native | iOS and Android trading app |
| `postgres` | PostgreSQL 16 | Primary relational database |
| `redis` | Redis 7 | Cache, pub/sub, Celery broker |
| `worker` | Celery (Python) | Background tasks (notifications, reports, reconciliation) |

---

## 3. Service Communication

```
Frontend (Web/Mobile)
        │
        │ REST + WebSocket (HTTPS/WSS)
        ▼
┌──────────────────┐
│   Nginx Gateway  │  ◄── SSL termination, rate limiting
└────────┬─────────┘
         │
         ├──► /api/users/*         → user-service
         ├──► /api/orders/*        → order-service
         ├──► /api/market/*        → market-data-service
         ├──► /api/portfolio/*     → portfolio-service
         ├──► /api/wallet/*        → wallet-service
         ├──► /api/notifications/* → notification-service
         ├──► /api/admin/*         → admin-service
         └──► /ws/*                → market-data-service (WebSocket)
```

### Inter-Service Communication
- Services communicate via **REST over internal Docker network** (not exposed publicly)
- Real-time events (order fills, price updates) broadcast via **Redis Pub/Sub**
- Background jobs dispatched via **Celery + Redis**

---

## 4. Order Lifecycle

### 4.1 Simulation Mode Order Flow

```
User submits order
        │
        ▼
order-service
  ├── Validate (symbol, side, type, quantity, price)
  ├── Check simulation wallet balance
  ├── Reserve funds (lock)
  ├── Publish order to Redis: channel = orders.simulation
        │
        ▼
simulation-engine (subscriber)
  ├── Fetch current market price from market-data-service
  ├── For MARKET order: fill immediately at current price
  ├── For LIMIT order: queue, check price continuously, fill when condition met
  ├── Create fill record in DB
  ├── Publish fill event: channel = fills.{user_id}
        │
        ▼
portfolio-service (subscriber)
  ├── Update position
  ├── Update simulation wallet balance
  ├── Recalculate P&L
        │
        ▼
notification-service (subscriber)
  └── Send "Order Filled" notification to user
```

### 4.2 Live Mode Order Flow (Phase 4+)

```
User submits order
        │
        ▼
order-service
  ├── Validate
  ├── Check real wallet balance
  ├── Reserve funds
  ├── Publish order to Redis: channel = orders.live
        │
| Users | users, user_profiles, kyc_documents, user_roles, partner_permissions, commission_ledger |
execution-service (subscriber)
  ├── Call Binance API via CCXT: create_order()
  ├── Receive Binance order ID and status
  ├── Stream fill updates from Binance User Data Stream
  ├── Create fill record in DB
  ├── Publish fill event: channel = fills.{user_id}
        │
        ▼
portfolio-service + notification-service (same as simulation)
```

---

## 5. Market Data Flow

```
Binance WebSocket (external)
        │
        ▼
market-data-service
  ├── Subscribe to ticker streams (all active pairs)
  ├── Subscribe to order book streams (top 20 levels)
  ├── Subscribe to kline/OHLCV streams (1m, 5m, 1h, 1d)
  ├── Publish to Redis Pub/Sub: channel = market.ticker.{symbol}
  ├── Store OHLCV in PostgreSQL (price_history table)
        │
        ▼
Frontend clients (via WebSocket /ws/market/{symbol})
  └── Receive live price updates, update chart and order book in UI
```

---

## 6. Authentication & Authorisation

- **Method:** JWT (JSON Web Tokens)  
- **Access Token:** Short-lived (15 minutes)  
- **Refresh Token:** Long-lived (7 days), stored in HttpOnly cookie  
- **Roles:** STUDENT, TRADER, PARTNER, POWER_USER, SUPER_USER, ADMIN, SUPER_ADMIN  
- **Every API endpoint** requires a valid JWT except: /register, /login, /health  
- **Role-based guards** on all admin endpoints  
- **2FA:** TOTP (Google Authenticator) — optional for students, mandatory for Admins  
- **Visibility rule:** SUPER_USER accounts are not visible to non-SUPER_ADMIN callers in admin and reporting flows.

---

## 7. Database Schema (Core Tables)

### users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique, indexed |
| password_hash | VARCHAR | bcrypt |
| role | ENUM | STUDENT, TRADER, PARTNER, POWER_USER, SUPER_USER, ADMIN, SUPER_ADMIN |
| trading_mode | ENUM | SIMULATION, LIVE |
| kyc_status | ENUM | PENDING, SUBMITTED, APPROVED, REJECTED |
| language_preference | ENUM | EN, AR |
| referred_by | UUID (nullable) | FK -> users.id (Partner referral link) |
| is_active | BOOLEAN | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### simulation_wallets
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | |
| user_id | UUID | FK → users |
| currency | VARCHAR(10) | e.g. USDT |
| balance | NUMERIC(28,8) | Available balance |
| locked_balance | NUMERIC(28,8) | Reserved for open orders |
| updated_at | TIMESTAMP | |

### orders
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | |
| user_id | UUID | FK → users |
| symbol | VARCHAR(20) | e.g. BTC/USDT |
| side | ENUM | BUY, SELL |
| order_type | ENUM | MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT |
| market_type | ENUM | SPOT, FUTURES, OPTIONS |
| quantity | NUMERIC(28,8) | |
| price | NUMERIC(28,8) | NULL for MARKET orders |
| status | ENUM | PENDING, OPEN, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED |
| execution_mode | ENUM | SIMULATION, LIVE |
| external_order_id | VARCHAR | Binance order ID (live mode only) |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### order_fills
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | |
| order_id | UUID | FK → orders |
| fill_price | NUMERIC(28,8) | |
| fill_quantity | NUMERIC(28,8) | |
| fee | NUMERIC(28,8) | |
| fee_currency | VARCHAR(10) | |
| execution_mode | ENUM | SIMULATION, LIVE |
| filled_at | TIMESTAMP | |

### positions (Futures / Options)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | |
| user_id | UUID | FK → users |
| symbol | VARCHAR(20) | |
| market_type | ENUM | FUTURES, OPTIONS |
| side | ENUM | LONG, SHORT |
| entry_price | NUMERIC(28,8) | |
| quantity | NUMERIC(28,8) | |
| leverage | INTEGER | 1–100 |
| liquidation_price | NUMERIC(28,8) | Calculated |
| unrealised_pnl | NUMERIC(28,8) | Updated in real-time |
| execution_mode | ENUM | SIMULATION, LIVE |
| status | ENUM | OPEN, CLOSED, LIQUIDATED |
| opened_at | TIMESTAMP | |
| closed_at | TIMESTAMP | |

---

## 8. Real-Time Architecture (WebSocket)

| Channel | Direction | Data |
|---------|-----------|------|
| `/ws/market/{symbol}/ticker` | Server → Client | Live bid/ask/last price |
| `/ws/market/{symbol}/orderbook` | Server → Client | Top 20 order book levels |
| `/ws/market/{symbol}/kline/{interval}` | Server → Client | Latest candle (OHLCV) |
| `/ws/user/orders` | Server → Client | Order status updates |
| `/ws/user/fills` | Server → Client | Fill confirmations |
| `/ws/user/portfolio` | Server → Client | Live P&L updates |
| `/ws/user/notifications` | Server → Client | Alert messages |

---

## 9. Simulation Engine — Fill Logic

### 9.1 Core Principle — Order Book Depth Fills

All fills in the simulation engine are executed by **walking the live Binance order book depth ladder**, not by using a single `last_price`. This mirrors real exchange behaviour and teaches students how large orders interact with actual market liquidity.

- **BUY orders** consume the **ask** side of the order book (lowest ask first, walking up).
- **SELL orders** consume the **bid** side of the order book (highest bid first, walking down).

The live order book is sourced from market-data-service, which maintains the latest depth snapshot from the Binance WebSocket stream.

---

### 9.2 Market Order Fill Algorithm

When a Market order is received:

1. **Fetch the current order book** for the symbol from market-data-service (top N levels of asks for BUY, bids for SELL).
2. **Walk the depth ladder** level by level, consuming quantity in price-priority order:
   - Take all available quantity at level 0 (best price).
   - If the order is not yet fully filled, continue to level 1, level 2, etc.
   - At each level, record a separate `order_fills` record with that level's price and quantity consumed.
3. **If the entire order book depth snapshot does not contain enough quantity** to fill the remaining order:
   - Record all fills obtained so far.
   - Update order status to `PARTIALLY_FILLED`.
   - Wait for the **top 3 levels of the real Binance order book to refresh** (i.e., the engine monitors the WebSocket feed and detects that those levels have changed — quantities updated or new price levels appear).
   - Once the book refreshes, re-fetch the new depth snapshot and resume filling from Step 1 with the remaining unfilled quantity.
   - Repeat this cycle until the order is fully filled (`FILLED`).
4. Throughout the fill cycle, publish a fill event to Redis (`fills.{user_id}`) after each partial fill so the frontend can show real-time progress.

```
MARKET BUY — Example

Order: Buy 5 BTC

Ask ladder (from Binance):
  Ask[0]: 65,100 USDT × 1.5 BTC   → Fill 1.5 BTC @ 65,100
  Ask[1]: 65,120 USDT × 2.0 BTC   → Fill 2.0 BTC @ 65,120
  Ask[2]: 65,150 USDT × 0.8 BTC   → Fill 0.8 BTC @ 65,150
  — Total filled so far: 4.3 BTC. Remaining: 0.7 BTC —
  Ask[3]: 65,200 USDT × 0.3 BTC   → Partially fills, still 0.4 BTC remaining
  — Book exhausted at snapshot. Set status: PARTIALLY_FILLED —
  — Wait for top 3 ask levels to refresh on Binance WebSocket —
  — New snapshot fetched. Resume filling remaining 0.4 BTC —
  Ask[0]: 65,210 USDT × 2.0 BTC   → Fill 0.4 BTC @ 65,210
  — Order FILLED —
```

---

### 9.3 Limit Order Fill Algorithm

When a Limit order is received:

1. Set order status to `OPEN`. Store in Redis open-orders set for the symbol.
2. Subscribe to the live order book WebSocket updates for that symbol.
3. On each book update, check whether the limit price condition is met:
   - **BUY Limit**: The best ask (`asks[0].price`) must be ≤ limit price.
   - **SELL Limit**: The best bid (`bids[0].price`) must be ≥ limit price.
4. When the condition is met, apply the **same depth-walk fill algorithm** as Market orders (Section 9.2), but **only consume levels at or better than the limit price**:
   - BUY: consume asks where `ask_price ≤ limit_price` only.
   - SELL: consume bids where `bid_price ≥ limit_price` only.
5. If mid-fill the book moves away from the limit price before the order is fully filled, stop consuming, remain `PARTIALLY_FILLED`, and resume when the condition is met again on the next book update.
6. Fill price for each level is the actual level price (not the limit price) — this is the realistic maker/taker model. Students see their limit order may fill at multiple price levels, all at or better than their specified price.

---

### 9.4 Order Type Summary

| Order Type | Trigger | Fill Price Source | Partial Fill Behaviour |
|------------|---------|-------------------|------------------------|
| MARKET (BUY) | Immediate | Walk ask depth ladder (best ask first) | Wait for top 3 ask levels to refresh, then continue |
| MARKET (SELL) | Immediate | Walk bid depth ladder (best bid first) | Wait for top 3 bid levels to refresh, then continue |
| LIMIT (BUY) | When best ask ≤ limit price | Walk ask ladder, levels ≤ limit price only | Pause if book moves above limit; resume when eligible asks return |
| LIMIT (SELL) | When best bid ≥ limit price | Walk bid ladder, levels ≥ limit price only | Pause if book moves below limit; resume when eligible bids return |
| STOP-LOSS | When market price crosses stop level | Convert to MARKET, apply Market fill algorithm | Same as MARKET |
| TAKE-PROFIT | When market price crosses target level | Convert to MARKET, apply Market fill algorithm | Same as MARKET |
| FUTURES LONG | Same as above | Same as above | Same as above + track margin, update unrealised P&L on each price tick |
| FUTURES SHORT | Same as above | Same as above (bid side) | Same as above with inverse P&L direction |
| OPTIONS | Phase 3 | Black-Scholes pricing against real underlying price | — |

---

### 9.5 Order Book Refresh Detection

To determine that the "top 3 levels have refreshed" the simulation engine monitors the live order book WebSocket stream from market-data-service. A refresh is considered to have occurred when **at least one of the top 3 levels shows a change in price or quantity** compared to the snapshot that was used for the previous fill attempt. The engine then re-attempts filling with the new snapshot.

This ensures the engine never spins in a tight loop hitting a stale order book, and that each fill attempt uses genuinely new market data.

---

## 10. Security Architecture

| Layer | Control |
|-------|---------|
| Network | Nginx rate limiting; all services on internal Docker network (not public) |
| Authentication | JWT with short expiry; refresh token in HttpOnly cookie |
| Authorisation | Role-based guards on every endpoint |
| Input Validation | Pydantic models on all API inputs (FastAPI) |
| SQL Injection | SQLAlchemy ORM only; no raw SQL strings with user input |
| XSS | React escapes output by default; Content-Security-Policy headers set |
| CSRF | SameSite cookie attribute; double-submit cookie pattern |
| Secrets | All secrets in environment variables; never in source code; `.env` excluded from git |
| Dependency Scanning | GitHub Dependabot enabled on repository |
| Audit Logging | Every admin action and all order events logged to `audit_logs` table |

---

## 11. Infrastructure Layout (VPS — Coolify)

```
VPS (Ubuntu 24.04)
├── Coolify Control Panel
├── Docker Engine
│   ├── nginx (api-gateway) — port 80/443
│   ├── user-service — internal only
│   ├── market-data-service — internal + ws
│   ├── order-service — internal only
│   ├── simulation-engine — internal only
│   ├── execution-service — internal only (Phase 4)
│   ├── portfolio-service — internal only
│   ├── wallet-service — internal only
│   ├── risk-service — internal only
│   ├── notification-service — internal only
│   ├── admin-service — internal only
│   ├── worker (Celery) — internal only
│   ├── postgres — internal only (persisted volume)
│   ├── redis — internal only (persisted volume)
│   └── web-frontend (Next.js) — port served via nginx
└── Let's Encrypt SSL (managed by Coolify)
```

### Storage Allocation (Estimated)
| Data | Storage |
|------|---------|
| PostgreSQL (6 months) | ~20–40 GB |
| Redis (cache only) | ~2 GB |
| Application logs | ~10 GB |
| Backups | ~50 GB |

Available: 200 GB NVMe + 400 GB SSD — adequate for Phase 1–3.

---

## 12. Backup & Recovery

| Item | Policy |
|------|--------|
| PostgreSQL | Daily full dump + continuous WAL archiving; retained 30 days |
| Redis | AOF persistence enabled |
| Backup location | Off-VPS object storage (e.g. Backblaze B2 or Wasabi) |
| Recovery Time Objective (RTO) | < 2 hours |
| Recovery Point Objective (RPO) | < 24 hours (Phase 1–3); < 1 hour (Phase 4–5 live trading) |

---

## 13. Monitoring

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics collection (API latency, error rates, queue depth) |
| Grafana | Dashboard visualisation |
| Loki | Log aggregation |
| Grafana Alerting | PagerDuty-style alerts for downtime, high error rates |
| Uptime monitoring | Simple HTTP checks on /health endpoints |

---

*End of Architecture Document v1.1*
