# XChange Platform — Phased Execution Roadmap
**Version:** 1.2  
**Date:** 08-May-2026  
**Parent Document:** [MASTER_PLAN.md](./MASTER_PLAN.md)  
**Architecture Reference:** [ARCHITECTURE.md](./ARCHITECTURE.md)

> This document is the **day-to-day working guide** for the XChange Platform build.  
> It breaks each phase from the Master Plan into 2-week sprints with specific tasks,  
> dependencies, and a clear definition of "done" for each sprint.  
> The Master Plan remains the single source of truth for scope and decisions.  
> This Roadmap governs sequencing and execution.

---

## How to Use This Document

- Work one sprint at a time. Do not start Sprint N+1 until Sprint N is complete.
- Check off each task as it is done.
- If a task is blocked, note the blocker inline and raise it immediately — do not skip ahead.
- At the end of each sprint, review the deliverable checklist. Only mark a sprint complete when ALL deliverables are met.
- Any scope change must be recorded in `MASTER_PLAN.md` first, then reflected here.

---

## Current Execution Status (As of 08-May-2026)

| Item | Status |
|------|--------|
| Active branch | `main` |
| Latest delivery commit | `1911d17` |
| Completed sprints | Sprint 1 to Sprint 12 |
| Current sprint | Sprint 13 (in progress) |
| Parallel stream (non-phase) | RBAC expansion for PARTNER, POWER_USER, SUPER_USER — completed |

### Sprint Progress Snapshot

| Sprint | Status |
|--------|--------|
| Sprint 1 to Sprint 12 | ✅ Completed |
| Sprint 13 | 🚧 In Progress |
| Sprint 14 to Sprint 24 | ⏳ Not Started |

---

## Sprint Calendar Overview

| Phase | Sprint | Months | Focus |
|-------|--------|--------|-------|
| Phase 1 | Sprint 1 | Month 1, Week 1–2 | Project skeleton, infrastructure, CI/CD |
| Phase 1 | Sprint 2 | Month 1, Week 3–4 | User service, authentication |
| Phase 1 | Sprint 3 | Month 2, Week 1–2 | Market data service, live price feed |
| Phase 1 | Sprint 4 | Month 2, Week 3–4 | Basic trading UI, simulation wallet, admin skeleton |
| Phase 2 | Sprint 5 | Month 3, Week 1–2 | Simulation engine — Spot (Market + Limit orders) |
| Phase 2 | Sprint 6 | Month 3, Week 3–4 | Portfolio service, P&L, trade history |
| Phase 2 | Sprint 7 | Month 4, Week 1–2 | Futures simulation — long/short, leverage, margin |
| Phase 2 | Sprint 8 | Month 4, Week 3–4 | Risk service, liquidation engine, notifications |
| Phase 3 | Sprint 9 | Month 5, Week 1–2 | Options simulation, price alerts, email notifications |
| Phase 3 | Sprint 10 | Month 5, Week 3–4 | UI polish, accessibility, performance optimisation |
| Phase 3 | Sprint 11 | Month 6, Week 1–2 | Admin panel completion, student dashboard |
| Phase 3 | Sprint 12 | Month 6, Week 3–4 | Mobile app (React Native), load testing, security audit |
| Phase 4 | Sprint 13 | Month 7, Week 1–2 | VARA compliance review, KYC/AML design |
| Phase 4 | Sprint 14 | Month 7, Week 3–4 | KYC flow implementation, document upload |
| Phase 4 | Sprint 15 | Month 8, Week 1–2 | Real wallet service, crypto deposit addresses |
| Phase 4 | Sprint 16 | Month 8, Week 3–4 | CCXT Binance live order routing (Spot) |
| Phase 4 | Sprint 17 | Month 9, Week 1–2 | Real execution engine, fill reconciliation |
| Phase 4 | Sprint 18 | Month 9, Week 3–4 | Fee engine, compliance exports, penetration testing |
| Phase 5 | Sprint 19 | Month 10, Week 1–2 | VARA filing prep, legal review |
| Phase 5 | Sprint 20 | Month 10, Week 3–4 | KYC-verified beta group activation — Spot live |
| Phase 5 | Sprint 21 | Month 11, Week 1–2 | Live Futures trading rollout |
| Phase 5 | Sprint 22 | Month 11, Week 3–4 | Options routing (Deribit/Bybit) decision + integration |
| Phase 5 | Sprint 23 | Month 12, Week 1–2 | Public launch preparation, onboarding flow |
| Phase 5 | Sprint 24 | Month 12, Week 3–4 | Public launch, 24/7 monitoring runbook active |

---

---

# PHASE 1 — Foundation
**Duration:** Months 1–2 (Sprints 1–4)  
**Goal:** A working skeleton where a student can log in, see live prices, and place a simulated spot order.

---

## Sprint 1 — Project Skeleton, Infrastructure & CI/CD
**Dates:** Month 1, Week 1–2  
**Depends on:** Nothing (first sprint)

### Tasks

#### Repository & Version Control
- [ ] Create private GitHub repository: `xchange-platform`
- [ ] Establish branch strategy: `main` (production), `dev` (integration), `feature/*` (work branches)
- [ ] Add `.gitignore` (Python, Node, Docker, `.env` files excluded)
- [ ] Add `README.md` with project overview and local setup instructions
- [ ] Add `docs/` folder — copy MASTER_PLAN.md, ARCHITECTURE.md, ROADMAP.md into repo

#### Monorepo Structure
Create the following folder structure in the repository:
```
xchange-platform/
├── services/
│   ├── user-service/
│   ├── market-data-service/
│   ├── order-service/
│   ├── simulation-engine/
│   ├── execution-service/       ← empty placeholder (Phase 4)
│   ├── portfolio-service/
│   ├── wallet-service/
│   ├── risk-service/
│   ├── notification-service/
│   └── admin-service/
├── frontend/
│   └── web/
├── mobile/
├── infrastructure/
│   ├── nginx/
│   └── docker/
├── docs/
└── docker-compose.yml
```

#### Docker Compose (Local Development)
- [ ] `docker-compose.yml` defining all services (stubbed with placeholder images initially)
- [ ] PostgreSQL 16 container — with named volume for data persistence
- [ ] Redis 7 container — with AOF persistence enabled
- [ ] Nginx container — basic reverse proxy config (routes to be filled as services come up)
- [ ] `.env.example` file listing all required environment variables (no real values)
- [ ] `Makefile` or `scripts/start.sh` for one-command local startup

#### CI/CD Pipeline
- [ ] GitHub Actions workflow: `ci.yml`
  - Trigger: push to `dev` or any `feature/*` branch
  - Steps: checkout → lint (flake8/ruff for Python, ESLint for JS) → run tests → build Docker image
- [ ] GitHub Actions workflow: `deploy.yml`
  - Trigger: push to `main` branch only
  - Steps: build → push image to registry → trigger Coolify webhook deploy
- [ ] Connect Coolify on VPS to GitHub repository (webhook set up)
- [ ] Verify: push a dummy change to `main`, confirm Coolify receives the webhook

#### VPS Setup
- [ ] Confirm VPS is accessible (SSH key-based access only, password login disabled)
- [ ] Docker Engine installed and running on VPS
- [ ] Coolify installed and control panel accessible
- [ ] PostgreSQL and Redis deployed on VPS via Coolify (persistent volumes configured)
- [ ] Test DB connection from local machine via SSH tunnel
- [ ] Domain name decided and DNS pointed to VPS IP
- [ ] SSL certificate issued via Let's Encrypt (Coolify handles this)

### Sprint 1 Deliverable Checklist
- [ ] GitHub repository is live with agreed folder structure
- [ ] `docker-compose up` starts all containers locally without errors
- [ ] PostgreSQL and Redis are running and accessible on VPS
- [ ] A push to `main` triggers a deploy via Coolify — confirmed working
- [ ] Domain resolves to VPS and SSL is active

---

## Sprint 2 — User Service & Authentication
**Dates:** Month 1, Week 3–4  
**Depends on:** Sprint 1 (VPS, DB, Docker running)

### Tasks

#### User Service — FastAPI App Setup
- [ ] Create FastAPI app skeleton inside `services/user-service/`
- [ ] `requirements.txt`: FastAPI, Uvicorn, SQLAlchemy, Alembic, psycopg2, passlib[bcrypt], python-jose[cryptography], pydantic
- [ ] `Dockerfile` for user-service
- [ ] Connect to PostgreSQL using SQLAlchemy async engine
- [ ] Alembic configured for database migrations
- [ ] Health check endpoint: `GET /health` → returns `{ "status": "ok" }`

#### Database — Users Schema
- [ ] Alembic migration: create `users` table
  - id (UUID, PK), email (unique), password_hash, role (ENUM), trading_mode (ENUM),
    kyc_status (ENUM), language_preference (ENUM), is_active (BOOLEAN),
    created_at, updated_at
- [ ] Alembic migration: create `user_profiles` table
  - id, user_id (FK), full_name, phone_number, country, date_of_birth, updated_at
- [ ] Alembic migration: create `audit_logs` table
  - id, user_id (nullable), action, entity_type, entity_id, ip_address, created_at

#### Authentication Endpoints
- [ ] `POST /auth/register` — create account (email + password), role defaults to STUDENT
- [ ] `POST /auth/login` — validate credentials, return JWT access token + set refresh token in HttpOnly cookie
- [ ] `POST /auth/refresh` — exchange refresh token for new access token
- [ ] `POST /auth/logout` — invalidate refresh token (blacklist in Redis)
- [ ] `GET /users/me` — return current user's profile (JWT required)
- [ ] `PUT /users/me` — update profile fields (JWT required)

#### Security Implementation
- [ ] Passwords hashed with bcrypt (passlib)
- [ ] JWT access token: 15-minute expiry, signed with RS256 or HS256 secret
- [ ] Refresh token: 7-day expiry, stored in Redis (token → user_id mapping)
- [ ] Refresh token set in HttpOnly, Secure, SameSite=Strict cookie
- [ ] Rate limiting on `/auth/login`: max 5 attempts per IP per minute (via Nginx config)
- [ ] Input validation: all request bodies validated via Pydantic models
- [ ] Email format and password strength validation on registration
- [ ] All audit-worthy actions written to `audit_logs` table

#### Role-Based Access Control
- [ ] Dependency: `get_current_user` — extracts and validates JWT, returns user object
- [ ] Dependency: `require_role(roles: list)` — rejects request if user role not in list
- [ ] Roles defined as Python Enum: STUDENT, TRADER, ADMIN, SUPER_ADMIN

#### Nginx Routing
- [ ] Add `/api/users/*` and `/api/auth/*` routes in Nginx config → proxied to user-service

### Sprint 2 Deliverable Checklist
- [ ] A user can register via API
- [ ] A user can log in and receive a valid JWT
- [ ] Protected endpoints reject requests without a valid JWT
- [ ] Admin-only endpoints reject requests from non-admin users
- [ ] All auth actions are recorded in `audit_logs`
- [ ] Refresh token works correctly and logout invalidates it

---

## Sprint 3 — Market Data Service & Live Price Feed
**Dates:** Month 2, Week 1–2  
**Depends on:** Sprint 1 (Redis running), Sprint 2 (JWT auth for WebSocket auth)

### Tasks

#### Market Data Service — App Setup
- [ ] FastAPI app skeleton inside `services/market-data-service/`
- [ ] `requirements.txt`: FastAPI, Uvicorn, python-binance (or websockets), SQLAlchemy, aioredis, pydantic
- [ ] `Dockerfile` for market-data-service

#### Database — Market Schema
- [ ] Alembic migration: create `trading_pairs` table
  - id, symbol (e.g. BTC/USDT), base_asset, quote_asset, market_type (SPOT/FUTURES/OPTIONS),
    is_active (BOOLEAN), min_quantity, max_quantity, price_tick_size, quantity_step, created_at
- [ ] Alembic migration: create `price_history` (OHLCV) table
  - id, symbol, interval (1m/5m/1h/1d), open, high, low, close, volume, timestamp

#### Binance WebSocket Connection
- [ ] Connect to Binance WebSocket for selected spot pairs (BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, XRP/USDT, ADA/USDT, DOGE/USDT, AVAX/USDT, DOT/USDT, MATIC/USDT — 10 pairs minimum)
- [ ] Subscribe to: `<symbol>@ticker` (24h price stats + last price)
- [ ] Subscribe to: `<symbol>@depth20` (order book top 20 levels)
- [ ] Subscribe to: `<symbol>@kline_1m`, `@kline_5m`, `@kline_1h`, `@kline_1d`
- [ ] On each message: publish to Redis Pub/Sub channel `market.ticker.<symbol>`
- [ ] On each kline close: persist OHLCV record to `price_history` table
- [ ] Reconnect logic: automatic reconnect on WebSocket disconnect (exponential backoff)

#### REST Endpoints (Market Data)
- [ ] `GET /market/pairs` — list all active trading pairs
- [ ] `GET /market/ticker/{symbol}` — latest ticker (last price, 24h change, volume)
- [ ] `GET /market/orderbook/{symbol}` — current order book snapshot (top 20)
- [ ] `GET /market/klines/{symbol}?interval=1h&limit=200` — OHLCV history

#### WebSocket Endpoints (Market Data — Real-Time)
- [ ] `WS /ws/market/{symbol}/ticker` — stream live price updates to connected clients
- [ ] `WS /ws/market/{symbol}/orderbook` — stream order book updates to connected clients
- [ ] `WS /ws/market/{symbol}/kline/{interval}` — stream latest candle updates

#### Seed Data
- [ ] Seed script to insert the 10 initial trading pairs into `trading_pairs` table
- [ ] Seed script to load 30 days of historical OHLCV data for all pairs from Binance REST API (one-time historical backfill)

#### Nginx Routing
- [ ] Add `/api/market/*` routes → market-data-service
- [ ] Add `/ws/*` routes → market-data-service (WebSocket upgrade headers configured)

### Sprint 3 Deliverable Checklist
- [ ] Service connects to Binance and receives live price data without disconnecting
- [ ] Live prices are publishing to Redis Pub/Sub
- [ ] REST endpoint returns current ticker for BTC/USDT
- [ ] REST endpoint returns 200 candles of OHLCV history
- [ ] WebSocket connection from browser receives live price updates in real-time
- [ ] Historical OHLCV data loaded into DB for all 10 pairs

---

## Sprint 4 — Basic Trading UI, Simulation Wallet, Admin Skeleton
**Dates:** Month 2, Week 3–4  
**Depends on:** Sprint 2 (auth), Sprint 3 (market data WebSocket)

### Tasks

#### Web Frontend — Project Setup
- [ ] Create Next.js + TypeScript project inside `frontend/web/`
- [ ] Install: shadcn/ui, Zustand, TradingView Lightweight Charts, axios
- [ ] Configure Nginx to serve the Next.js app
- [ ] Environment variables: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_BASE_URL`
- [ ] Routing structure:
  - `/login`, `/register` — auth pages
  - `/dashboard` — main trading interface
  - `/portfolio` — holdings and P&L
  - `/history` — trade history
  - `/admin` — admin panel (role-gated)

#### Authentication UI
- [ ] Login page — email/password form, calls `POST /auth/login`, stores JWT in memory (not localStorage)
- [ ] Register page — email/password/name form, calls `POST /auth/register`
- [ ] Protected route wrapper — redirects to `/login` if no valid JWT
- [ ] Logout button — calls `POST /auth/logout`, clears token state

#### Trading Dashboard UI
- [ ] Market selector — dropdown of all active trading pairs
- [ ] TradingView Lightweight Chart — candlestick chart (OHLCV), connects to WebSocket for live candle updates
- [ ] Live price ticker — updates in real time from WebSocket
- [ ] Order book display — shows top 10 bid/ask levels, updates in real time
- [ ] Order entry form:
  - Market/Limit toggle
  - Buy/Sell toggle
  - Quantity input
  - Price input (visible only for Limit orders)
  - Submit button (wired to order-service endpoint — stub response for now)
- [ ] Available balance display (simulation wallet balance)

#### Wallet Service — Simulation Wallet
- [ ] FastAPI app skeleton inside `services/wallet-service/`
- [ ] Database: `simulation_wallets` table already defined in ARCHITECTURE.md — run migration
- [ ] `GET /wallet/simulation` — return user's simulation wallet balances (JWT required)
- [ ] Admin endpoint: `POST /admin/wallet/topup` — assign virtual balance to a student (Admin role required)
- [ ] On user registration: automatically create a simulation wallet for the user with zero balance

#### Order Service — Skeleton
- [ ] FastAPI app skeleton inside `services/order-service/`
- [ ] Database migration: create `orders` and `order_fills` tables (schema from ARCHITECTURE.md)
- [ ] `POST /orders` — accept order submission, validate fields, return `order_id` with status PENDING (full execution logic in Sprint 5)
- [ ] `GET /orders` — return user's open and recent orders (JWT required)
- [ ] `DELETE /orders/{order_id}` — cancel an open order

#### Admin Service — Skeleton
- [ ] FastAPI app skeleton inside `services/admin-service/`
- [ ] `GET /admin/users` — list all users with pagination (ADMIN role required)
- [ ] `GET /admin/users/{user_id}` — view single user detail
- [ ] `PUT /admin/users/{user_id}/mode` — switch user's `trading_mode` (SIMULATION ↔ LIVE)
- [ ] `PUT /admin/users/{user_id}/status` — activate/suspend user account
- [ ] Basic Admin UI page at `/admin/users` in the frontend — table view of all users

### Sprint 4 Deliverable Checklist
- [ ] A student can log in, see a live candlestick chart for BTC/USDT updating in real time
- [ ] A student can see the live order book
- [ ] A student can submit an order via the UI — it reaches order-service and returns an order ID
- [ ] A student's simulation wallet balance is visible on the dashboard
- [ ] An admin can log into `/admin`, see the user list, and assign a simulation wallet balance to a student
- [ ] An admin can toggle a user's trading mode

---
---

# PHASE 2 — Full Simulation Trading Engine
**Duration:** Months 3–4 (Sprints 5–8)  
**Goal:** Students can simulate full Spot and Futures trading. Admin can monitor all students.

---

## Sprint 5 — Simulation Engine: Spot Trading (Market + Limit Orders)
**Dates:** Month 3, Week 1–2  
**Depends on:** Sprint 4 (order-service skeleton, simulation wallet, Redis running)

### Tasks

#### Simulation Engine — App Setup
- [ ] FastAPI app skeleton inside `services/simulation-engine/`
- [ ] Redis subscriber: listen on channel `orders.simulation`
- [ ] On order received: route to correct fill handler based on `order_type`
- [ ] At startup: fetch and cache the live order book snapshot for each active symbol from market-data-service
- [ ] Maintain a live order book mirror per symbol by subscribing to `market.orderbook.{symbol}` Redis channel; update cache on each message

#### Market Order Fill Handler
- [ ] Fetch the current order book snapshot from the in-memory cache (ask side for BUY, bid side for SELL)
- [ ] Walk the depth ladder level by level in price-priority order:
  - BUY: consume ask[0] fully, then ask[1], then ask[2] … until order quantity is fully satisfied
  - SELL: consume bid[0] fully, then bid[1], then bid[2] … until order quantity is fully satisfied
  - For each level consumed: create an `order_fills` record (price = that level's price, quantity = quantity taken from that level)
- [ ] If the snapshot is exhausted before the order is fully filled:
  - Record all fills obtained so far; set order status to `PARTIALLY_FILLED`
  - Register a "book refresh watcher" for the symbol: monitor the live order book stream and detect when **at least one of the top 3 levels changes** (price or quantity)
  - On book refresh: re-fetch the new snapshot and resume the depth-walk with the remaining unfilled quantity
  - Repeat until the order is fully filled (`FILLED`)
- [ ] After each partial or full fill: update `simulation_wallets.locked_balance` and add acquired asset (or USDT for SELL)
- [ ] Publish fill event to Redis: `fills.{user_id}` after every individual level fill (not just on completion)

#### Limit Order Fill Handler
- [ ] On LIMIT order received: set order status to `OPEN`, store in Redis open-orders set keyed by symbol
- [ ] Subscribe to live order book updates (`market.orderbook.{symbol}`)
- [ ] On each book update, evaluate fill condition:
  - BUY limit: fill condition met when `asks[0].price ≤ limit_price`
  - SELL limit: fill condition met when `bids[0].price ≥ limit_price`
- [ ] When condition is met: run the same depth-walk fill algorithm as Market orders, but **only consume levels at or better than the limit price**
  - BUY: consume only ask levels where `ask_price ≤ limit_price`
  - SELL: consume only bid levels where `bid_price ≥ limit_price`
- [ ] If the book moves away from the limit price mid-fill: stop consuming, remain `PARTIALLY_FILLED`, resume on the next book update when eligible levels reappear
- [ ] Fill price for each level = the actual level price (not the limit price); all fills are at or better than limit
- [ ] Same wallet, fill record, and publish logic as Market handler

#### Order-Service Integration
- [ ] When `POST /orders` is called:
  - Validate: symbol exists in `trading_pairs` and is active
  - Validate: user has sufficient simulation balance (for BUY: USDT balance ≥ quantity × price; for SELL: asset balance ≥ quantity)
  - Reserve funds: move required amount from `balance` to `locked_balance`
  - Set order status to PENDING
  - Publish to Redis: `orders.simulation`
  - Return `order_id` to client immediately
- [ ] `DELETE /orders/{order_id}`: cancel OPEN limit order → release locked balance back to available

#### WebSocket — User Order Updates
- [ ] market-data-service (or a dedicated user-event service): subscribe to `fills.{user_id}` on Redis
- [ ] Push fill event to connected frontend client via `WS /ws/user/orders`
- [ ] Frontend updates order status and wallet balance in real-time without page refresh

#### Stop-Loss Order Handler
- [ ] On STOP_LOSS order: set status `OPEN`, monitor `market.ticker.{symbol}` subscription
  - SELL stop-loss: trigger when `last_price <= stop_price`
  - BUY stop-loss (short cover): trigger when `last_price >= stop_price`
- [ ] On trigger: convert to MARKET order and apply the full depth-walk fill algorithm

### Sprint 5 Deliverable Checklist
- [ ] A student places a Market BUY for BTC/USDT — it fills level by level through the live ask ladder; average fill price reflects real market depth
- [ ] A large Market order that exceeds available depth partially fills, waits for the book to refresh, then completes — student sees status update from PENDING → PARTIALLY_FILLED → FILLED in real time
- [ ] A student places a Limit BUY below current price — order stays OPEN, fills automatically only through eligible ask levels when price comes down
- [ ] A student places a Stop-Loss — it triggers and fills via depth-walk when price crosses the stop level
- [ ] A student cancels an open Limit order — locked balance is returned
- [ ] All fills (including each partial) are visible on the frontend in real-time without page refresh

---

## Sprint 6 — Portfolio Service, P&L & Trade History
**Dates:** Month 3, Week 3–4  
**Depends on:** Sprint 5 (simulation engine producing fills)

### Tasks

#### Portfolio Service — App Setup
- [ ] FastAPI app skeleton inside `services/portfolio-service/`
- [ ] Subscribe to Redis: `fills.{user_id}` to keep portfolio updated in real-time
- [ ] Also reconcile from DB on service startup (in case of restarts)

#### Database — Portfolio Schema
- [ ] Alembic migration: create `portfolio_holdings` table
  - id, user_id, asset (e.g. BTC), quantity, average_entry_price, execution_mode, updated_at
- [ ] Alembic migration: create `pnl_snapshots` table
  - id, user_id, snapshot_date, total_realised_pnl, total_unrealised_pnl, total_portfolio_value, execution_mode

#### Portfolio Calculation Logic
- [ ] On fill received: update `portfolio_holdings` (add/subtract quantity, recalculate average entry price)
- [ ] Realised P&L: on SELL fill → `(fill_price − average_entry_price) × quantity − fees`
- [ ] Unrealised P&L: recalculate on each price tick from `market.ticker.*`
- [ ] Total portfolio value: sum of all holdings × current price + USDT balance
- [ ] Daily P&L snapshot: Celery task runs at midnight, writes to `pnl_snapshots`

#### Portfolio Endpoints
- [ ] `GET /portfolio/holdings` — current holdings with unrealised P&L per asset
- [ ] `GET /portfolio/summary` — total value, total realised P&L, total unrealised P&L, today's P&L
- [ ] `GET /portfolio/pnl/history?days=30` — daily P&L snapshot chart data

#### Trade History Endpoints
- [ ] `GET /orders/history` — all filled orders, paginated, filterable by symbol and date range
- [ ] `GET /orders/fills` — all individual fill records

#### WebSocket — Live Portfolio Updates
- [ ] `WS /ws/user/portfolio` — stream live portfolio value and unrealised P&L on each price tick
- [ ] Frontend portfolio page: live total value, P&L, holdings table with real-time unrealised P&L column

#### Frontend — Portfolio & History Pages
- [ ] Portfolio page: holdings table, total value, realised P&L, unrealised P&L, mini P&L chart (last 30 days)
- [ ] Trade history page: table of filled orders with symbol, side, quantity, fill price, P&L, date

### Sprint 6 Deliverable Checklist
- [ ] After a trade fills, portfolio page reflects updated holdings immediately
- [ ] Unrealised P&L on open holdings updates in real-time as price moves
- [ ] Realised P&L is correctly calculated and shown after a position is closed
- [ ] Trade history page shows all past trades with correct data
- [ ] Daily P&L snapshots are being written to DB by Celery task

---

## Sprint 7 — Futures Simulation: Long/Short, Leverage, Margin
**Dates:** Month 4, Week 1–2  
**Depends on:** Sprint 5 (simulation engine), Sprint 6 (portfolio service)

### Tasks

#### Database — Futures Schema
- [ ] Alembic migration: create `positions` table (schema from ARCHITECTURE.md)
- [ ] Alembic migration: create `margin_accounts` table
  - id, user_id, execution_mode, total_margin_balance, available_margin, used_margin, updated_at

#### Futures Instrument Configuration
- [ ] Add futures trading pairs to `trading_pairs` table: BTC/USDT (FUTURES), ETH/USDT (FUTURES) to start
- [ ] Admin setting: default max leverage per pair (configurable per pair, default 20x)
- [ ] Admin setting: user-specific max leverage override

#### Simulation Engine — Futures Fill Handler
- [ ] On FUTURES order (LONG or SHORT):
  - Calculate margin required: `(quantity × entry_price) / leverage`
  - Validate: available margin balance ≥ required margin
  - Reserve margin: deduct from `available_margin`, add to `used_margin`
  - Create position record in `positions` table (status: OPEN)
  - Calculate liquidation price:
    - LONG: `entry_price × (1 − 1/leverage + maintenance_margin_rate)`
    - SHORT: `entry_price × (1 + 1/leverage − maintenance_margin_rate)`
  - Store liquidation price in position record

#### Real-Time Position Monitoring
- [ ] Subscribe to `market.ticker.{symbol}` for each open futures position
- [ ] On each price tick:
  - Recalculate unrealised P&L:
    - LONG: `(current_price − entry_price) × quantity`
    - SHORT: `(entry_price − current_price) × quantity`
  - Publish updated unrealised P&L to `fills.{user_id}` Redis channel

#### Closing a Futures Position
- [ ] `POST /orders` with `reduce_only: true` closes an open position (fully or partially)
- [ ] On fill: calculate realised P&L, release margin, update `positions.status` to CLOSED
- [ ] Add realised P&L to user's margin balance

#### Frontend — Futures Trading UI
- [ ] Add "Futures" tab to the trading interface
- [ ] Order entry form: adds leverage slider (1x–max), displays required margin, estimated liquidation price
- [ ] Open positions table: symbol, side, size, entry price, mark price, unrealised P&L, liquidation price, close button
- [ ] Margin summary widget: total balance, available margin, margin usage %

### Sprint 7 Deliverable Checklist
- [ ] A student opens a LONG BTC/USDT futures position with 10x leverage
- [ ] Unrealised P&L updates in real-time as BTC price moves
- [ ] Student closes the position — realised P&L is correctly calculated and margin is returned
- [ ] Liquidation price is displayed and is mathematically correct for the leverage used
- [ ] A SHORT position shows inverse P&L (goes positive when price falls)

---

## Sprint 8 — Risk Service, Liquidation Engine & In-App Notifications
**Dates:** Month 4, Week 3–4  
**Depends on:** Sprint 7 (futures positions with liquidation prices)

### Tasks

#### Risk Service — App Setup
- [ ] FastAPI app skeleton inside `services/risk-service/`
- [ ] Continuously monitor all OPEN futures positions
- [ ] On each `market.ticker.{symbol}` event: check all open positions for that symbol

#### Margin Call Logic
- [ ] Calculate margin ratio: `(margin_balance + unrealised_pnl) / used_margin × 100`
- [ ] Margin call threshold: 20% (configurable in platform_settings)
- [ ] When margin ratio falls below threshold: publish margin call event to `risk.margin_call.{user_id}`
- [ ] Do NOT liquidate immediately on margin call — give user a warning first

#### Liquidation Logic
- [ ] Liquidation threshold: when `last_price` crosses `liquidation_price` stored in position
- [ ] On liquidation trigger:
  - Close position immediately at market price (no user action required)
  - Set position status to LIQUIDATED
  - Set remaining margin to zero (or maintenance margin, whichever is lower)
  - Record liquidation event in `liquidations` table
  - Publish liquidation event to `risk.liquidation.{user_id}`

#### Database — Risk Schema
- [ ] Alembic migration: create `margin_calls` table
  - id, user_id, position_id, margin_ratio_at_call, price_at_call, created_at, resolved_at
- [ ] Alembic migration: create `liquidations` table
  - id, user_id, position_id, liquidation_price, realised_pnl, created_at

#### Notification Service — In-App Notifications
- [ ] FastAPI app skeleton inside `services/notification-service/`
- [ ] Subscribe to Redis channels: `fills.{user_id}`, `risk.margin_call.{user_id}`, `risk.liquidation.{user_id}`
- [ ] On each event: write record to `notifications` table
- [ ] Database migration: create `notifications` table
  - id, user_id, type (FILL / MARGIN_CALL / LIQUIDATION / PRICE_ALERT / SYSTEM), title, body, is_read, created_at
- [ ] `GET /notifications` — return user's unread notifications (JWT required)
- [ ] `PUT /notifications/{id}/read` — mark as read
- [ ] `WS /ws/user/notifications` — push new notifications to connected client in real-time
- [ ] Frontend: notification bell icon with unread count badge, dropdown list of recent notifications

#### Position Size Limits
- [ ] Admin setting: `max_position_value_usdt` per user (configurable)
- [ ] order-service validation: reject order if it would push total open position value above user limit
- [ ] Admin panel: view and edit per-user position limits

### Sprint 8 Deliverable Checklist
- [ ] A student with an open leveraged position receives an in-app margin call warning before liquidation
- [ ] If price crosses liquidation level, position is auto-liquidated and student receives an in-app notification
- [ ] Notification bell shows unread count and list of recent events
- [ ] Admin can set a maximum position value per student
- [ ] An order that would exceed the student's position limit is rejected with a clear error message

---
---

# PHASE 3 — Academy-Ready Platform
**Duration:** Months 5–6 (Sprints 9–12)  
**Goal:** Platform polished for daily academy use. Mobile apps live. Security audited.

---

## Sprint 9 — Options Simulation, Price Alerts, Email Notifications
**Dates:** Month 5, Week 1–2  
**Depends on:** Sprint 8 (notification service, risk service complete)

### Tasks

#### Options Simulation (European Style — Simulation Only in Phase 1–3)
- [ ] Add options instruments to `trading_pairs`: BTC/USDT-C (Call), BTC/USDT-P (Put) — European style, weekly expiry
- [ ] Database migration: add `options_contracts` table
  - id, underlying_symbol, option_type (CALL/PUT), strike_price, expiry_date, is_active
- [ ] Simulation engine — options pricing:
  - Use Black-Scholes model to calculate theoretical option price in real-time
  - Inputs: current underlying price (from Binance), strike price, time to expiry, implied volatility (fixed default, e.g. 60% — admin configurable)
  - Display: option premium, delta, gamma, theta (Greeks — display only, no position Greeks tracking yet)
- [ ] On options BUY: deduct premium × quantity from simulation wallet
- [ ] On options expiry: run Celery task at expiry timestamp
  - CALL: if `settlement_price > strike_price` → pay `(settlement_price − strike_price) × quantity`
  - PUT: if `settlement_price < strike_price` → pay `(strike_price − settlement_price) × quantity`
  - Otherwise: option expires worthless, premium is lost
- [ ] Frontend: basic options trading interface (select expiry, strike, call/put, quantity)

#### Price Alerts
- [ ] Database migration: create `price_alerts` table
  - id, user_id, symbol, condition (ABOVE / BELOW), target_price, is_triggered, created_at, triggered_at
- [ ] `POST /alerts` — create a price alert
- [ ] `GET /alerts` — list user's active alerts
- [ ] `DELETE /alerts/{id}` — remove an alert
- [ ] risk-service (or market-data-service): monitor `market.ticker.*`, check all active alerts for the symbol
- [ ] On trigger: mark alert as triggered, publish event to notification-service → in-app + email notification

#### Email Notifications
- [ ] Add email provider: SMTP (use SendGrid free tier or AWS SES)
- [ ] Environment variable: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL`
- [ ] notification-service: on fill, margin call, liquidation, price alert trigger → send email
- [ ] Email templates (plain HTML):
  - Order filled template
  - Margin call warning template
  - Liquidation notice template
  - Price alert triggered template
- [ ] User preference: `notification_preferences` table — allow user to disable email notifications

### Sprint 9 Deliverable Checklist
- [ ] A student buys a Call option — premium is deducted from their wallet
- [ ] At expiry, in-the-money options pay out correctly; out-of-the-money options expire worthless
- [ ] A student sets a price alert at a specific level — receives in-app and email notification when price crosses it
- [ ] Emails are received correctly for order fills, margin calls, and liquidations

---

## Sprint 10 — UI Polish, Accessibility & Performance
**Dates:** Month 5, Week 3–4  
**Depends on:** Sprints 1–9 (all features built)

### Tasks

#### UI Consistency & Polish
- [ ] Audit all pages for visual consistency — spacing, typography, colour tokens
- [ ] Standardise loading states (skeleton loaders) across all data tables and charts
- [ ] Standardise empty states (no data messages) across all pages
- [ ] Error boundary components on all major page sections
- [ ] Responsive layout audit — test on 1280px, 1440px, 1920px widths

#### Accessibility
- [ ] All interactive elements have `aria-label` or visible text label
- [ ] Keyboard navigation works for all forms, modals, and dropdowns
- [ ] Colour contrast passes WCAG AA for all text on background combinations
- [ ] Focus ring visible on all focusable elements

#### Frontend Performance
- [ ] Lighthouse audit on dashboard, portfolio, and history pages — target score ≥ 85
- [ ] Code-split heavy components (charts, order book) using dynamic imports
- [ ] WebSocket reconnection logic hardened — exponential back-off on all WS connections
- [ ] API response caching for market data endpoints (SWR or React Query)

#### Error Handling Hardening
- [ ] All API errors surface a user-readable toast/message — no silent failures
- [ ] Session expiry handled gracefully — user redirected to login with message
- [ ] Network offline state detected and communicated to user

### Sprint 10 Deliverable Checklist
- [ ] All pages pass visual consistency audit
- [ ] Lighthouse score ≥ 85 on key pages
- [ ] Keyboard navigation works end-to-end
- [ ] All error and empty states handled visibly

---

## Sprint 11 — Admin Panel Completion & Student Performance Dashboard
**Dates:** Month 6, Week 1–2  
**Depends on:** Sprints 5–8 (all trading data available), Sprint 2 (user management)

### Tasks

#### Admin Panel — Full User Management
- [ ] User list page: search, filter by role/status/mode, sortable columns
- [ ] User detail page: full profile, KYC status, wallet balances, trading statistics
- [ ] Bulk actions: suspend multiple users, assign simulation balance to a group
- [ ] Create admin user endpoint: `POST /admin/users` (SUPER_ADMIN only)
- [ ] Activity log per user: show recent audit log entries for a specific user

#### Admin Panel — Market Configuration
- [ ] Trading pairs management: enable/disable a pair, edit min/max quantity, price tick size
- [ ] Add new trading pair: form to add a new symbol (validates against Binance available symbols)
- [ ] Leverage limits per pair: set default and maximum leverage for each futures pair
- [ ] Platform-wide trading hours: option to pause all trading (emergency control)

#### Admin Panel — Fee Configuration
- [ ] Platform settings: set default maker fee %, taker fee % (applied at order fill)
- [ ] Per-user fee override: set a different fee rate for a specific user
- [ ] Fee ledger: view all fees collected (by user, by pair, by date range)
- [ ] Note: fees apply to simulation trades for realism (students see fee deducted in P&L)

#### Student Performance Dashboard
- [ ] Per-student view: total trades, win rate, average P&L per trade, best trade, worst trade, current simulation balance
- [ ] Class-wide leaderboard: rank all students by total P&L (simulation mode)
- [ ] Time-range filter: today / this week / this month / all time
- [ ] Export: download student performance report as CSV

#### Platform Settings Page (Admin)
- [ ] Simulation slippage factor (default 0.05%, range 0%–1%)
- [ ] Default simulation wallet balance for new students
- [ ] Margin call threshold %
- [ ] Platform maintenance mode toggle (shows maintenance page to all users)
- [ ] Allowed IP ranges for admin panel access (optional security hardening)

### Sprint 11 Deliverable Checklist
- [ ] Admin can search for a student, view their full trading history and P&L
- [ ] Admin can disable a trading pair platform-wide — students can no longer open new orders on it
- [ ] Fees are being deducted correctly from simulation trades
- [ ] Student leaderboard is visible with correct P&L rankings
- [ ] Admin can export a CSV report of all students' performance

---

## Sprint 12 — Mobile App, Load Testing & Security Audit
**Dates:** Month 6, Week 3–4  
**Depends on:** All Sprints 1–11 (full platform functional)

### Tasks

#### Mobile App (React Native)
- [ ] Create React Native project inside `mobile/`
- [ ] Install: React Navigation, React Native WebSocket, Zustand, React Native Chart Kit
- [ ] Core screens:
  - Login / Register
  - Dashboard: live price chart, order book, order entry form
  - Portfolio: holdings, P&L summary
  - Trade History
  - Notifications list
  - Profile / settings
- [ ] Shared API layer: extract all API calls into a shared `api/` module reused by both web and mobile
- [ ] WebSocket connections: live prices, order updates, notifications — same as web
- [ ] Push notifications: integrate Firebase Cloud Messaging (FCM) for iOS + Android
- [ ] Build: generate APK (Android) and IPA (iOS) — internal distribution only (TestFlight + internal APK)

#### Load Testing
- [ ] Install k6 or Locust for load testing
- [ ] Test scenarios:
  - 500 concurrent users viewing live price charts (WebSocket connections)
  - 200 concurrent users placing orders simultaneously
  - 100 concurrent users on the portfolio page with live P&L updates
- [ ] Measure: API response time (target < 200ms p95), WebSocket latency, DB query time
- [ ] Identify and fix any bottlenecks found
- [ ] Document results in `docs/LOAD_TEST_RESULTS.md`

#### Security Audit (OWASP Top 10 Review)
- [ ] A1 — Broken Access Control: verify all endpoints have correct role checks; test with wrong-role JWT
- [ ] A2 — Cryptographic Failures: confirm all passwords bcrypt-hashed, no plaintext secrets in code or logs
- [ ] A3 — Injection: confirm all DB queries use SQLAlchemy ORM, no raw string queries with user input
- [ ] A4 — Insecure Design: review order submission flow for manipulation (e.g. can a user submit a negative quantity?)
- [ ] A5 — Security Misconfiguration: review Docker container permissions, Nginx headers (HSTS, CSP, X-Frame-Options)
- [ ] A6 — Vulnerable Components: run `pip-audit` on all Python requirements, `npm audit` on frontend
- [ ] A7 — Authentication Failures: test brute-force protection on login endpoint
- [ ] A8 — Data Integrity: verify order data cannot be tampered with between submission and execution
- [ ] A9 — Logging & Monitoring: confirm all security events are in `audit_logs`, Grafana alerts configured
- [ ] A10 — SSRF: confirm market-data-service only connects to Binance — no user-controlled URLs
- [ ] Document all findings and fixes in `docs/SECURITY_AUDIT.md`

#### Phase 3 Final Checklist
- [ ] Mobile apps distributed to academy staff for testing (TestFlight + APK)
- [ ] Platform handles 500 concurrent users without degradation
- [ ] No critical or high OWASP findings remain unresolved
- [ ] All Phase 3 sprints marked complete

**MILESTONE: Platform is ready for daily use in the offline academy.**  
Students can trade simulation Spot, Futures, and Options on web and mobile.

---
---

# PHASE 4 — Live Trading Readiness
**Duration:** Months 7–9 (Sprints 13–18)  
**Goal:** System technically ready for real money. Regulatory review underway.

> ⚠️ Note: Phase 4 involves real money infrastructure. Every task here must be reviewed and tested more rigorously than previous phases. Nothing goes to production without explicit sign-off.
> 
> Clarification: the RBAC expansion (PARTNER, POWER_USER, SUPER_USER) was delivered as a separate platform access-control stream and does not replace or redefine Phase 4 scope.

---

## Sprint 13 — VARA Compliance Review & KYC/AML Design
**Dates:** Month 7, Week 1–2

### Tasks
- [ ] Engage UAE legal counsel specialising in VARA (Virtual Assets Regulatory Authority)
- [ ] Obtain list of VARA requirements for the intended licence type (VASP vs full exchange)
- [x] Document all compliance requirements in `docs/COMPLIANCE_REQUIREMENTS.md`
- [ ] Select KYC/AML provider — evaluate: Sumsub, Jumio, Onfido (refer to Open Question #3 in MASTER_PLAN.md)
  - Sprint 13 progress: initial provider comparison drafted in `docs/KYC_AML_PROVIDER_EVALUATION.md`
- [x] Design KYC flow: document upload → liveness check → AML screening → admin review → approval
- [x] Design compliance data schema: what data must be stored, for how long, in what format
- [x] Define VARA report format (transaction reports, suspicious activity reports)
- [ ] Update `docs/MASTER_PLAN.md` Open Questions #3 and #4 with decisions made

### Sprint 13 Deliverable Checklist
- [ ] Legal counsel engaged and first meeting completed
- [ ] `COMPLIANCE_REQUIREMENTS.md` written and reviewed with legal counsel
- [ ] KYC/AML provider selected
- [x] KYC flow design document complete

---

## Sprint 14 — KYC Flow Implementation
**Dates:** Month 7, Week 3–4

### Tasks
- [x] user-service: `POST /kyc/submit` — accept document reference submissions (passport / Emirates ID + selfie)
- [ ] Integrate selected KYC provider SDK — submit documents for verification
- [x] Webhook endpoint scaffold from KYC provider: update `users.kyc_status` on verification result
- [x] AML screening call scaffold: configurable provider API call on user registration and on KYC approval
- [x] Admin backend: KYC review queue API — view pending submissions, approve/reject with reason
- [x] On KYC approval: admin can then activate `trading_mode = LIVE` for the user (backend gate enforced)
- [x] Frontend: KYC submission page scaffold (document-reference submission flow)
- [ ] Email notifications: KYC submitted, KYC approved, KYC rejected (with reason)

### Sprint 14 Deliverable Checklist
- [x] A user can submit KYC document references through API
- [ ] KYC provider processes the submission and result is reflected in the platform
- [x] Admin API sees KYC queue and can manually review
- [x] A user's live mode cannot be activated until KYC is APPROVED

---

## Sprint 15 — Real Wallet Service & Crypto Deposit Addresses
**Dates:** Month 8, Week 1–2

### Tasks
- [ ] wallet-service: extend to support real wallets
- [ ] Database: create `real_wallets` table (same structure as simulation_wallets, separate records)
- [ ] Generate unique deposit addresses per user per currency (use HD wallet derivation or exchange-assigned address)
  - Phase 4 approach: use Binance sub-account deposit addresses (simpler, no custody risk)
- [ ] `GET /wallet/real` — return user's real wallet balances (KYC-approved + LIVE mode users only)
- [ ] Blockchain monitoring: webhook or polling to detect incoming deposits, update real wallet balance
- [ ] Withdrawal flow: `POST /wallet/withdraw` — create withdrawal request (admin approval required for Phase 4)
- [ ] Admin: approve/reject withdrawal requests
- [ ] All real wallet transactions recorded in `balance_ledger` table (immutable append-only log)

### Sprint 15 Deliverable Checklist
- [ ] A KYC-approved user can see their real wallet deposit address
- [ ] A test deposit is detected and reflected in the user's real wallet balance
- [ ] All wallet transactions are recorded in the immutable ledger

---

## Sprint 16 — CCXT Binance Live Order Routing (Spot)
**Dates:** Month 8, Week 3–4

### Tasks
- [ ] execution-service: build full implementation (was placeholder since Sprint 1)
- [ ] Install CCXT Python; configure Binance API key + secret from environment variables
- [ ] Subscribe to Redis: `orders.live`
- [ ] On order received:
  - Call `ccxt.binance.create_order(symbol, type, side, amount, price)`
  - Store Binance order ID in `orders.external_order_id`
- [ ] Subscribe to Binance User Data Stream for fill updates
- [ ] On fill from Binance: create `order_fills` record, publish to `fills.{user_id}`
- [ ] Order cancellation: `DELETE /orders/{id}` → call `ccxt.binance.cancel_order()`
- [ ] Error handling: Binance API errors (insufficient balance, invalid symbol, rate limits) → set order status REJECTED, notify user
- [ ] Reconciliation: Celery task every 5 minutes — compare open orders in DB vs Binance, resolve any discrepancies

### Sprint 16 Deliverable Checklist
- [ ] A test order (small amount) is placed via the platform in LIVE mode and appears on Binance
- [ ] When Binance fills the order, the fill is reflected in the platform within 2 seconds
- [ ] A cancelled order on the platform is also cancelled on Binance
- [ ] Reconciliation task detects and resolves any out-of-sync orders

---

## Sprint 17 — Real Execution Engine & Fill Reconciliation
**Dates:** Month 9, Week 1–2

### Tasks
- [ ] Extend execution-service to handle all order types via CCXT: Market, Limit, Stop-Loss, Take-Profit
- [ ] Futures live routing: connect to Binance Futures API (separate endpoint from Spot in CCXT)
- [ ] Position tracking for live futures: sync open positions from Binance API periodically
- [ ] Real-time margin monitoring: fetch margin account status from Binance, update risk-service
- [ ] Binance liquidation events: subscribe to Binance User Data Stream for FORCE_ORDER events, record in `liquidations` table
- [ ] Real wallet balance sync: after each fill, sync actual balance from Binance to `real_wallets` table

### Sprint 17 Deliverable Checklist
- [ ] All Spot order types (Market, Limit, Stop-Loss) work end-to-end in LIVE mode
- [ ] Futures orders can be placed and managed in LIVE mode
- [ ] Binance-initiated liquidations are detected and recorded
- [ ] Real wallet balance always matches Binance account balance

---

## Sprint 18 — Fee Engine, Compliance Exports & Penetration Testing
**Dates:** Month 9, Week 3–4

### Tasks

#### Fee Engine (Live Mode)
- [ ] Platform fee charged on top of (or absorbed from) Binance fill price in live mode
- [ ] Fee calculation: `fill_quantity × fill_price × fee_rate`
- [ ] Fee recorded in `fee_ledger` table per fill
- [ ] Fee deducted from user's real wallet balance on fill
- [ ] Admin: fee revenue dashboard (total fees collected, by user, by pair, by date)

#### Compliance Exports (VARA)
- [ ] Celery task: generate monthly transaction report (all deposits, withdrawals, trades for all users)
- [ ] Export format: CSV matching VARA reporting template (defined in Sprint 13 compliance review)
- [ ] Suspicious Activity Report (SAR) flag: admin can manually flag a user/transaction for SAR reporting
- [ ] Admin: download compliance report for any date range

#### Penetration Testing
- [ ] Engage third-party penetration testing firm
- [ ] Scope: all public API endpoints, WebSocket connections, admin panel, authentication flow
- [ ] Remediate all critical and high findings before Phase 5
- [ ] Document results in `docs/PENTEST_REPORT.md`

#### Disaster Recovery Test
- [ ] Run a full DR drill: drop the PostgreSQL container, restore from latest backup, verify data integrity
- [ ] Document RTO achieved (target < 2 hours)
- [ ] Document RPO achieved (target < 24 hours)

**MILESTONE: System is technically ready for live trading. Awaiting VARA regulatory approval.**

---
---

# PHASE 5 — Gradual Go-Live
**Duration:** Months 10–12 (Sprints 19–24)  
**Goal:** Controlled, regulated rollout of real trading to verified users. Public launch.

> Note: Phase 5 timing is entirely dependent on VARA regulatory approval. If approval is delayed, Phase 5 sprints are paused — the simulation platform continues operating and generating value for the academy.

---

## Sprint 19 — VARA Filing Preparation & Legal Review
**Dates:** Month 10, Week 1–2

### Tasks
- [ ] Work with legal counsel to prepare VARA licence application documents
- [ ] Prepare technical documentation package for VARA: system architecture, security controls, data flow diagrams, compliance procedures
- [ ] Conduct internal AML policy review and document AML/CFT programme
- [ ] Submit VARA application (or registration, depending on licence type decided in Sprint 13)
- [ ] Legal review of Terms of Service, Privacy Policy, and Risk Disclosure documents
- [ ] Publish Terms of Service and Privacy Policy on the platform (required before any live trading)

---

## Sprint 20 — Beta Group Live Trading: Spot Only
**Dates:** Month 10, Week 3–4  
**Condition:** VARA approval received (or specific regulatory exemption confirmed)

### Tasks
- [ ] Select beta group: 5–10 KYC-approved users (trusted, known individuals — academy graduates)
- [ ] Activate LIVE mode for beta group only — all other users remain in SIMULATION
- [ ] Monitor 24/7 for first 2 weeks: every live order, every fill, every wallet transaction manually reviewed
- [ ] Escalation runbook: defined steps if a bug is found affecting real money (immediate order halt procedure)
- [ ] Spot trading only in beta: Futures and Options remain simulation for all users in this sprint

---

## Sprint 21 — Live Futures Trading Rollout
**Dates:** Month 11, Week 1–2  
**Condition:** Beta Spot trading has been stable for minimum 2 weeks

### Tasks
- [ ] Enable live Futures trading for KYC-approved LIVE mode users
- [ ] Start with reduced leverage cap: max 5x during rollout phase
- [ ] Monitor margin calls and liquidations on real accounts carefully
- [ ] Expand beta group to 20–50 users

---

## Sprint 22 — Options Routing Decision & Integration
**Dates:** Month 11, Week 3–4  
**Condition:** Resolve Open Question #1 from MASTER_PLAN.md (Deribit vs Bybit)

### Tasks
- [ ] Evaluate Deribit and Bybit Options APIs (CCXT support, UAE availability, API reliability)
- [ ] Select provider and update `docs/MASTER_PLAN.md` Open Question #1 with decision and rationale
- [ ] Integrate selected provider via CCXT for live options order routing
- [ ] Test end-to-end: options order placed on platform → routed to provider → fill reflected in platform
- [ ] Enable live Options trading for KYC-approved LIVE mode users

---

## Sprint 23 — Public Launch Preparation
**Dates:** Month 12, Week 1–2

### Tasks
- [ ] Public onboarding flow: self-service registration → email verification → KYC submission → KYC approval → live trading activated
- [ ] Marketing pages: landing page, features page, pricing/fee page
- [ ] Help centre: FAQ, how-to guides, video walkthroughs (for academy students migrating to live)
- [ ] Submit mobile apps to App Store (iOS) and Google Play Store (Android)
- [ ] Final load test: simulate 2,000 concurrent users
- [ ] Final security review: confirm all pentest findings from Sprint 18 are resolved
- [ ] 24/7 monitoring runbook: documented escalation procedures, on-call schedule, incident response steps
- [ ] Grafana dashboards finalised: uptime, order throughput, error rates, wallet balances

---

## Sprint 24 — Public Launch
**Dates:** Month 12, Week 3–4

### Tasks
- [ ] Flip the switch: open public registration
- [ ] Monitor platform health every hour for the first week
- [ ] Announce to academy students and their networks
- [ ] Record first week metrics: registrations, KYC completions, first live trades
- [ ] Post-launch retrospective: document what worked, what needed emergency fixes
- [ ] Update `MASTER_PLAN.md` change log with v2.0 scope (Phase 2+ features: fiat on-ramp, referral programme, etc.)

**MILESTONE: XChange Platform is a live, regulated, operating crypto exchange.**

---
---

# Appendix A — Definition of Done (All Sprints)

A task is "done" when:
1. Code is written and committed to a `feature/*` branch
2. It passes all automated tests (unit + integration) in the CI pipeline
3. It has been merged to `dev` via a pull request
4. The feature works correctly in the local Docker environment
5. It has been deployed to the VPS staging environment (same as production) and verified there

A sprint is "done" when:
1. All tasks in the sprint are individually done (as above)
2. All sprint deliverable checklist items are confirmed ✓
3. No critical or high bugs are open against this sprint's work
4. Changes are merged to `main` and deployed to production

---

# Appendix B — Blocked Task Protocol

If a task is blocked:
1. Note the blocker inline next to the task: `BLOCKED: <reason> — <date>`
2. Do not skip to the next sprint's tasks
3. If the blocker is external (legal, third-party), continue with non-dependent tasks within the same sprint
4. If the blocker cannot be resolved within 3 days, escalate and document in `MASTER_PLAN.md` open questions

---

# Appendix C — Document Change Log

| Version | Date | Change | By |
|---------|------|--------|----|
| 1.0 | 07-May-2026 | Initial roadmap created | Sufyan Ansari |
| 1.1 | 08-May-2026 | Updated execution status: Sprint 1–12 complete, Sprint 13 active | GitHub Copilot |
| 1.2 | 08-May-2026 | Clarified RBAC role-expansion stream vs Phase 4 scope; updated delivery commit and Sprint 14 KYC submit status | GitHub Copilot |

---

*End of Roadmap v1.2*
