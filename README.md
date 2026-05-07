# XChange Platform

A full-stack crypto trading exchange platform built with FastAPI (Python), Next.js, and React Native. Supports **Simulation mode** (paper trading at real market prices) and **Live mode** (real order routing via Binance). The only difference between the two modes is the execution engine — every other feature, UI, and account structure is identical.

> **Current Status:** Sprint 1 — Foundation (Infrastructure & Project Skeleton)

---

## Project Documents

All planning documents are in the `docs/` folder:

| Document | Purpose |
|----------|---------|
| [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) | Vision, scope, business model, technology decisions — single source of truth |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, service map, database schema, security architecture |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Sprint-by-sprint execution plan — 24 sprints across 12 months |

---

## Quick Start (Local Development)

### Prerequisites
- Docker Desktop installed and running
- Git

### 1. Clone the repository
```bash
git clone https://github.com/correspond9/Project_EXC.git
cd Project_EXC
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Open .env and fill in the required values (see comments inside)
```

### 3. Start all services

**On Linux / macOS:**
```bash
make up
```

**On Windows (PowerShell):**
```powershell
.\scripts\dev.ps1 up
```

### 4. Verify everything is running
```bash
# Linux/macOS
make ps

# Windows
.\scripts\dev.ps1 ps
```

Visit `http://localhost` — you should see the platform placeholder page.

### 5. Check individual service health
```
GET http://localhost/api/users/health
GET http://localhost/api/orders/health
GET http://localhost/api/market/health
```

---

## Services

| Service | Internal Port | Purpose |
|---------|--------------|---------|
| `nginx` | 80 | API gateway, reverse proxy, rate limiting |
| `user-service` | 8000 | Registration, login, JWT, profiles, KYC |
| `market-data-service` | 8000 | Binance WebSocket feed, OHLCV, price broadcast |
| `order-service` | 8000 | Order creation, validation, routing |
| `simulation-engine` | 8000 | Paper trading — fills at real market price |
| `execution-service` | 8000 | Live order routing to Binance (Phase 4+) |
| `portfolio-service` | 8000 | Positions, P&L, balance calculations |
| `wallet-service` | 8000 | Simulation and real wallet management |
| `risk-service` | 8000 | Margin monitoring, liquidation triggers |
| `notification-service` | 8000 | Email, in-app, push notifications |
| `admin-service` | 8000 | Admin panel API |
| `worker` | — | Celery background tasks |
| `postgres` | 5432 | Primary database (internal only) |
| `redis` | 6379 | Cache + pub/sub (internal only) |
| `web-frontend` | 3000 | Next.js web app |

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production — deploys automatically to VPS via Coolify |
| `dev` | Integration — all feature branches merge here first |
| `feature/<name>` | Individual feature work |

**Workflow:** `feature/*` → PR to `dev` → test → PR to `main` → auto-deploy

---

## Useful Commands

**Linux/macOS (Makefile):**
```bash
make up        # Start all services
make down      # Stop all services
make build     # Rebuild all images
make logs      # Tail all logs
make ps        # Show running containers
make clean     # Stop + remove all volumes (WARNING: deletes local data)
make migrate   # Run database migrations
make seed      # Run database seed scripts
```

**Windows (PowerShell):**
```powershell
.\scripts\dev.ps1 up
.\scripts\dev.ps1 down
.\scripts\dev.ps1 build
.\scripts\dev.ps1 logs
.\scripts\dev.ps1 ps
.\scripts\dev.ps1 clean
```

---

## CI/CD

| Trigger | Action |
|---------|--------|
| Push to `feature/*` or `dev` | Lint + build + test (GitHub Actions) |
| Push to `main` | Build images → push to `ghcr.io` → deploy via Coolify webhook |

**Required GitHub Secrets** (Settings → Secrets → Actions):
- `COOLIFY_WEBHOOK_URL` — Your Coolify deploy webhook URL
- `COOLIFY_WEBHOOK_TOKEN` — Your Coolify webhook token

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values. The `.env` file is git-ignored and must never be committed.

---

## Technology Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Celery
- **Database:** PostgreSQL 16, Redis 7
- **Frontend:** Next.js (React + TypeScript), TradingView Lightweight Charts, shadcn/ui
- **Mobile:** React Native
- **Infrastructure:** Docker, Nginx, Coolify, GitHub Actions
- **Exchange Connectivity:** CCXT (Binance — Phase 4+)
