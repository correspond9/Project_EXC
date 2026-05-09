# XChange Platform — Master Plan
**Version:** 1.1  
**Date:** 08-May-2026  
**Status:** Planning  
**Owner:** Sufyan Ansari  

> This document is the **single source of truth** for the entire XChange Platform project.  
> No development decision should be made that contradicts or is not covered by this document.  
> Any change to scope, architecture, or phasing must be updated here **first**.

---

## 1. Vision Statement

Build a **full crypto trading exchange platform** that operates in two execution modes — **Simulation** and **Live** — using the exact same codebase, user interface, features, and accounts.

The only difference between Simulation and Live mode is **where the trade gets executed**:
- **Simulation Mode**: Orders are filled internally by a paper-trading engine that walks the **real live Binance order book depth ladder** — the same bid/ask levels a real trader would consume. Market orders fill level by level through the book; large orders that exhaust available depth partially fill and wait for the book to refresh before continuing. No real money moves.
- **Live Mode**: Orders are routed to a real external exchange (Binance) via an API connection. Real money is involved.

Everything else — user experience, account structure, order types, risk management, P&L, reporting, admin controls — is **100% identical** in both modes.

---

## 2. Business Model

| Item | Detail |
|------|--------|
| Business Type | Full Crypto Exchange Platform (Broker front-end, routed to external liquidity in live mode) |
| Target Users (Phase 1) | Students of an offline trading academy |
| Target Users (Phase 2+) | General public — verified traders on live accounts |
| Markets Offered | Spot, Futures, Options |
| Liquidity Source (Live) | Binance (Spot + Futures); Options exchange TBD (Deribit / Bybit shortlisted) |
| Revenue Model | Spread markup, trading fees, subscription plans (to be detailed in Phase 2 planning) |
| Registered Country | United Arab Emirates (UAE) |
| Regulatory Authority | VARA (Virtual Assets Regulatory Authority, UAE) |
| Base Currency | USDT (primary); USD display equivalent |

---

## 3. Core Principle — Dual-Mode Architecture

```
User Places Order
       |
       v
   [Order Management Service]
       |
       |---[mode = SIMULATION]---> [Simulation Engine]
       |                               Paper fill at real price
       |                               No real money movement
       |
       |---[mode = LIVE]---------> [Real Execution Engine]
                                       Routes to Binance API
                                       Real money, real fills
```

**Rule:** Every service in the system is mode-agnostic EXCEPT the Execution Engine.  
The mode is stored at the account level and can only be changed by an Admin.  
An account in Simulation mode has a **Simulation Wallet**.  
An account in Live mode has a **Real Wallet**.  
The same account can hold both wallets — the active mode determines which wallet is used for trading.

---

## 4. User Types & Roles

| Role | Description |
|------|-------------|
| **Student** | Academy student. Starts in Simulation mode. Cannot switch to Live on their own. |
| **Trader** | Standard trader profile used for users permitted to trade beyond student-only constraints. |
| **Partner** | Affiliate/commission role. Can view referred users and own commission ledger. Referred-user trade visibility is discretionary and controlled by SUPER_ADMIN permission grants. |
| **Power User** | Advanced simulation role with real wallet-affecting ledger behavior for P&L, charges, payin/payout, and admin manual entries. |
| **Super User** | Power-user capability plus strict visibility controls: hidden from non-SUPER_ADMIN users across platform access paths. |
| **Admin** | Full platform control. Can manage users, switch modes, configure markets, toggle language. |
| **Super Admin** | Platform owner. All Admin access plus billing, compliance reports, regulatory exports. |

---

## 5. Feature Set (Day 1 Scope)

### 5.1 Trading
- Spot trading (Market order, Limit order, Stop-Loss order)
- Futures trading (Long/Short, with leverage 1x–100x configurable by Admin)
- Options trading (Call/Put, European style, simulation only in Phase 1)
- Order Book (live, real-time)
- Trade History (personal)
- Market Depth chart

### 5.2 Market Data
- Live price feed from Binance WebSocket (real-time, in both modes)
- Candlestick (OHLCV) charts — TradingView Charting Library (Advanced Charts, v27.004) with UDF-compatible datafeed
- Price alerts (user-configurable)
- Market overview page (all supported pairs, 24h stats)

### 5.3 Account & Wallet
- Single user account with two wallet states: Simulation and Real
- Simulation wallet: Admin assigns virtual balance to student
- Real wallet: Funded by actual crypto deposit (Phase 2+)
- Portfolio view: holdings, unrealised P&L, realised P&L, overall performance
- Full transaction history

### 5.4 Risk Management
- Margin call alerts (Futures)
- Automatic liquidation engine (Futures — simulation mode first, real in Phase 2)
- Position size limits (configurable per user by Admin)
- Max leverage cap (platform-wide and per-user)

### 5.5 KYC / AML (UAE VARA Compliant)
- Identity verification (passport / Emirates ID upload)
- Liveness check integration
- AML screening
- KYC required before Live mode is activated on any account
- Compliance report export for VARA

### 5.6 Admin Panel
- User management (create, suspend, promote, mode switch)
- Market configuration (enable/disable trading pairs, set limits)
- Fee configuration
- Platform settings page (fee rates, trading pair controls, emergency pause)
- Student performance dashboard (for academy use)
- Simulation wallet top-up (assign virtual funds to students)
- System health dashboard (uptime, API status, DB status)

### 5.7 Notifications
- In-app notifications (order filled, margin call, liquidation, KYC approved)
- Email notifications
- Push notifications (mobile)

### 5.8 Platform Access
- Web application (browser, desktop + mobile-responsive)
- Native mobile apps: iOS and Android (React Native)

---

## 6. Technology Stack

Chosen based on: solo developer, existing VPS (Coolify), maintainability, and open-source ecosystem.

### 6.1 Backend
| Component | Technology | Reason |
|-----------|-----------|--------|
| API Framework | **FastAPI (Python)** | Fast, async, clean, familiar |
| Primary Database | **PostgreSQL** | Relational, ACID-compliant, strong for financial records |
| Cache / Queue | **Redis** | Real-time pub/sub for live prices, order state caching |
| Task Queue | **Celery + Redis** | Background jobs (notifications, reports, reconciliation) |
| Exchange Connector | **CCXT (Python)** | Industry-standard library for Binance and 100+ exchange APIs |
| WebSocket Server | **FastAPI WebSockets** | Real-time order book and price streaming to frontend |

### 6.2 Frontend (Web)
| Component | Technology |
|-----------|-----------|
| Framework | **React + TypeScript** (Next.js) |
| Charts | **TradingView Charting Library** (Advanced Charts v27.004) + **UDF datafeed adapter** |
| State Management | **Zustand** (simple, lightweight) |
| Internationalisation | Not required — English only |
| UI Component Library | **shadcn/ui** (modern, accessible, customisable) |

### 6.3 Mobile
| Component | Technology |
|-----------|-----------|
| Framework | **React Native** |
| Code Share | Shared business logic and API calls with web |

### 6.4 Infrastructure
| Component | Technology |
|-----------|-----------|
| Server | VPS — 8-core CPU, 32GB RAM, 200GB NVMe + 400GB SSD, Ubuntu 24.04 |
| Container Orchestration | **Docker + Coolify** (already set up) |
| Reverse Proxy | **Nginx** |
| SSL | Let's Encrypt (via Coolify) |
| Monitoring | **Grafana + Prometheus** |
| Log Management | **Loki** (via Grafana) |
| CI/CD | **GitHub Actions** → Coolify webhook deploy |

### 6.5 Open Source Base Libraries (Not full frameworks — cherry-pick)
| Library | Used For |
|---------|---------|
| CCXT | Binance and exchange API connectivity |
| TradingView Charting Library (Advanced Charts) | Candlestick and trading charts |
| python-binance | Binance WebSocket stream (price feed) |
| ccxt | Order routing in live mode |
| django-rest-framework (reference) | Authentication patterns reference |

> **Decision**: We build a custom platform using the above libraries, NOT forked from HollaEx/Peatio/OpenDAX. Reason: those are Node.js/Ruby based and introduce unnecessary complexity for a solo Python-first developer. We borrow only the exchange connectivity layer (CCXT) and chart library (TradingView).

---

## 7. System Architecture — High Level

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                        │
│   Web (Next.js/React)         Mobile (React Native)          │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / WSS
┌───────────────────────────▼─────────────────────────────────┐
│                     API GATEWAY (Nginx)                       │
│         Auth, Rate Limiting, SSL Termination                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   BACKEND SERVICES (FastAPI)                  │
│                                                               │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ User Service │  │  Order Service │  │  Market Data    │  │
│  │ Auth / KYC   │  │  OMS / Router  │  │  Service        │  │
│  └──────────────┘  └───────┬────────┘  │  (Binance WS)   │  │
│                            │           └─────────────────┘  │
│                   ┌────────▼────────┐                        │
│                   │  Execution Mode │                        │
│                   │   [SIMULATION]  │──► Paper Engine        │
│                   │   [LIVE]        │──► CCXT → Binance      │
│                   └─────────────────┘                        │
│                                                               │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ Portfolio /  │  │  Wallet        │  │  Notification   │  │
│  │ P&L Service  │  │  Service       │  │  Service        │  │
│  └──────────────┘  └────────────────┘  └─────────────────┘  │
│                                                               │
│  ┌──────────────┐  ┌────────────────┐                        │
│  │ Admin Service│  │  Risk/Margin   │                        │
│  │              │  │  Service       │                        │
│  └──────────────┘  └────────────────┘                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                       DATA LAYER                              │
│         PostgreSQL            Redis                           │
│      (persistent data)   (cache + pub/sub)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Database — Top-Level Schema Areas

These are logical groupings (detailed schema per service to be done in Phase 1 design):

| Area | Key Tables |
|------|-----------|
| Users | users, user_profiles, kyc_documents, user_roles |
| Accounts | accounts, simulation_wallets, real_wallets, balance_ledger |
| Orders | orders, order_fills, order_history |
| Positions | positions (futures/options), margin_calls, liquidations |
| Market | trading_pairs, instruments, price_history |
| Transactions | deposits, withdrawals, fee_ledger |
| Notifications | notifications, notification_preferences |
| Admin | audit_logs, admin_actions, platform_settings |

---

## 9. Execution Phases

### Phase 1 — Foundation (Months 1 – 2)
**Goal:** Working platform skeleton, user management, live price feed, basic trading UI

- [ ] Project repository setup (GitHub, CI/CD via GitHub Actions + Coolify)
- [ ] Docker Compose configuration (all services containerised from day 1)
- [ ] PostgreSQL + Redis setup on VPS via Coolify
- [ ] User registration, login, JWT authentication
- [ ] Basic user profile and account model
- [ ] Market Data Service — connect to Binance WebSocket for live prices
- [ ] Spot trading pairs configuration (BTC/USDT, ETH/USDT, 10 pairs minimum)
- [ ] Basic trading UI — price chart (TradingView), order entry form
- [ ] Simulation wallet — assign virtual balance
- [ ] Admin panel skeleton

**Deliverable:** A student can log in, see live prices, and place a simulated spot order.

---

### Phase 2 — Full Simulation Trading Engine (Months 3 – 4)
**Goal:** Full simulation order matching, all order types, Spot + Futures

- [ ] Simulation execution engine — depth-ladder fill model:
  - Market orders: walk the live Binance ask/bid ladder level by level; multiple fill records per order at each level's price
  - Partial fills: if book depth is insufficient, set order to PARTIALLY_FILLED and resume when the top 3 book levels refresh
  - Limit orders: fill only through levels at or better than the limit price using same ladder walk
  - Stop-Loss / Take-Profit: trigger on price condition, then execute as Market fill via depth ladder
- [ ] All order types: Market, Limit, Stop-Loss, Take-Profit
- [ ] Order book display (live depth from Binance WebSocket)
- [ ] Portfolio service — track open positions, P&L, balance
- [ ] Trade history page
- [ ] Futures simulation — long/short positions, leverage, margin
- [ ] Liquidation engine (simulation)
- [ ] Risk management — margin call alerts, max position limits
- [ ] Notifications — in-app (order fill, margin call, liquidation)
- [ ] Student performance dashboard (admin view)

**Deliverable:** Students can simulate full Spot and Futures trading, admin can monitor all students.

---

### Phase 3 — Academy-Ready Platform (Months 5 – 6)
**Goal:** Platform polished enough for daily use in the offline academy

- [ ] Options simulation (Call/Put, European style)
- [ ] Price alerts (user-configurable)
- [ ] Full email notification system
- [ ] Admin panel — full user management, mode switch capability
- [ ] Admin panel — simulation wallet top-up per student
- [ ] Mobile app — iOS and Android (React Native)
- [ ] Platform-wide performance and load testing
- [ ] Security audit (OWASP Top 10 review)
- [ ] Internal documentation for academy operations

**Deliverable:** Full simulation exchange platform live for academy students. Mobile apps published.

---

### Phase 4 — Live Trading Readiness (Months 7 – 9)
**Goal:** Prepare the system for real money — compliance, real wallets, Binance integration

- [ ] UAE VARA compliance review — document all requirements
- [ ] KYC/AML flow — document upload, identity verification integration
- [ ] AML screening integration (third-party provider)
- [ ] Real wallet service — crypto deposit addresses, blockchain monitoring
- [ ] CCXT Binance integration — live order routing (Spot first)
- [ ] Real execution engine — order routing, fill confirmation, reconciliation
- [ ] Fee structure implementation (trading fee, withdrawal fee)
- [ ] Compliance reports — VARA export format
- [ ] Penetration testing (third-party recommended)
- [ ] Disaster recovery plan (backup strategy, RTO/RPO defined)

**Deliverable:** System technically ready for live trading. Awaiting regulatory approval.

---

### Phase 5 — Gradual Go-Live (Months 10 – 12)
**Goal:** Controlled rollout of real trading to verified users

- [ ] VARA license / registration filing (with legal counsel)
- [ ] KYC-verified accounts activated for live mode (selected users only)
- [ ] Beta group live trading — Spot only (monitored 24/7)
- [ ] Live Futures trading (after Spot is stable)
- [ ] Options routing decision (Deribit / Bybit integration)
- [ ] Full public launch preparation
- [ ] Marketing and onboarding flow
- [ ] 24/7 monitoring + incident response runbook
- [ ] Ongoing VARA compliance calendar

**Deliverable:** Platform is a live, regulated, operating crypto exchange open to the public.

---

## 10. Key Constraints & Decisions Log

| # | Decision | Reason |
|---|----------|--------|
| 1 | Python + FastAPI for backend | Developer familiarity, async performance, clean |
| 2 | Custom build, not HollaEx/Peatio fork | Those are Node.js/Ruby; adds more complexity than value |
| 3 | CCXT for exchange connectivity | Industry standard, supports Binance + 100 other exchanges |
| 4 | TradingView Charting Library v27.004 + UDF adapter | Full-featured professional charting integrated with backend market data |
| 5 | React Native for mobile | Code sharing with web, single team can maintain |
| 6 | Options routing TBD | Binance options limited; Deribit/Bybit to be evaluated in Phase 4 |
| 7 | Single account, two wallet states | Students migrate seamlessly to live trading |
| 8 | Mode switch only by Admin | Safety control — students cannot accidentally go live |
| 9 | All services containerised from day 1 | Deployment consistency on VPS via Coolify |
| 10 | Simulation uses real Binance price data | Students learn on real market conditions, not artificial prices |

---

## 11. What This Platform Is NOT

To protect scope and avoid feature creep:

- **Not a DEX (Decentralised Exchange)** — This is a centralised exchange/broker
- **Not a crypto wallet app** — Wallet is internal to the platform, not a standalone crypto wallet
- **Not a copy trading platform** — No social/copy trading features in scope
- **Not an OTC desk** — Standard exchange order model only
- **Not a payment gateway** — Crypto deposits/withdrawals only (no fiat on-ramp in Phase 1)

---

## 12. Open Questions (To Be Resolved Before Phase 4)

| # | Question | Owner | Target |
|---|----------|-------|--------|
| 1 | Which Options exchange to integrate: Deribit or Bybit? | Sufyan | Phase 4 kickoff |
| 2 | Fiat on-ramp (bank transfer / card) in scope? | Sufyan | Phase 3 review |
| 3 | Which KYC/AML third-party provider? (Sumsub, Jumio, Onfido) | Sufyan | Phase 4 kickoff |
| 4 | VARA licensing type needed — VASP or full exchange licence? | Legal counsel | Phase 3 |
| 5 | Referral / affiliate programme in scope? | Sufyan | Phase 3 review |

---

## 13. Document Change Log

| Version | Date | Change | By |
|---------|------|--------|----|
| 1.0 | 07-May-2026 | Initial master plan created | Sufyan Ansari |
| 1.1 | 08-May-2026 | Expanded role model with Partner, Power User, and Super User; aligned role definitions with implemented RBAC controls | GitHub Copilot |

---

*End of Master Plan v1.1*
