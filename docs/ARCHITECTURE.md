# XChange Platform — System Architecture
**Version:** 1.0  
**Date:** 07-May-2026  
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
        ▼
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
- **Roles:** STUDENT, TRADER, ADMIN, SUPER_ADMIN  
- **Every API endpoint** requires a valid JWT except: /register, /login, /health  
- **Role-based guards** on all admin endpoints  
- **2FA:** TOTP (Google Authenticator) — optional for students, mandatory for Admins  

---

## 7. Database Schema (Core Tables)

### users
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique, indexed |
| password_hash | VARCHAR | bcrypt |
| role | ENUM | STUDENT, TRADER, ADMIN, SUPER_ADMIN |
| trading_mode | ENUM | SIMULATION, LIVE |
| kyc_status | ENUM | PENDING, SUBMITTED, APPROVED, REJECTED |
| language_preference | ENUM | EN, AR |
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

| Order Type | Fill Rule |
|------------|-----------|
| MARKET (Spot) | Fill immediately at current `last_price` from Binance feed |
| LIMIT (Spot) | Fill when market price crosses the limit price; use limit price as fill price |
| STOP-LOSS | Trigger when price crosses stop level; then fill as MARKET |
| TAKE-PROFIT | Trigger when price crosses target level; then fill as MARKET |
| FUTURES LONG | Same as above + track margin, update unrealised P&L on each price tick |
| FUTURES SHORT | Same as above with inverse P&L direction |
| OPTIONS | Phase 3: simulate using Black-Scholes pricing model against real underlying price |

**Slippage simulation (optional for realism):** In simulation mode, a configurable slippage factor (e.g. 0.01%–0.1%) can be applied to market order fills to teach students about real execution quality.

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

*End of Architecture Document v1.0*
