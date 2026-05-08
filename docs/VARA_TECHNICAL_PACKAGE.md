# VARA Technical Documentation Package — XChange Platform

**Document Version:** 1.0  
**Prepared for:** Virtual Assets Regulatory Authority (VARA), Dubai, UAE  
**Prepared by:** [Company Name]  
**Classification:** Confidential — VARA Review Only

---

## 1. Executive Summary

XChange is a virtual asset trading platform regulated under VARA, providing both simulation (paper trading) and live trading capabilities. The platform routes live orders to Binance (licensed VASP) via the CCXT library and maintains full audit logs of all transactions.

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
Internet → nginx (reverse proxy) → Microservices
                                        ├── user-service       (auth, KYC, profiles)
                                        ├── order-service      (order lifecycle)
                                        ├── wallet-service     (balances, ledger)
                                        ├── execution-service  (LIVE orders → Binance)
                                        ├── market-data-service (prices, WebSocket)
                                        ├── simulation-engine  (paper trading fills)
                                        ├── portfolio-service  (P&L, history)
                                        ├── notification-service (email, in-app)
                                        ├── risk-service       (margin, liquidation)
                                        └── admin-service      (admin panel)

Data Layer:
  ├── PostgreSQL 16    (shared relational DB — xchange_db)
  └── Redis 7          (AOF — order bus, cache, pub/sub)
```

### 2.2 Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend services | Python 3.12, FastAPI (async) |
| Database | PostgreSQL 16 (asyncpg driver) |
| Cache / Message Bus | Redis 7 (AOF persistence) |
| Exchange connectivity | CCXT 4.4.12 → Binance API |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Mobile | React Native 0.73.4 |
| Infrastructure | Docker, Docker Compose, nginx |
| Auth | JWT HS256 (15-min access token, 7-day refresh) |

---

## 3. Data Flow Diagrams

### 3.1 User Registration & KYC Flow

```
User → POST /api/auth/register → user-service
  → Create user (trading_mode=SIMULATION, kyc_status=PENDING)

User → POST /api/kyc/submit → user-service
  → Store document references → set kyc_status=SUBMITTED
  → Trigger AML screening (optional provider)
  → Notify admin via notification-service

Admin → POST /api/kyc/{id}/approve → user-service
  → set kyc_status=APPROVED
  → Email user: KYC approved

Admin → PUT /api/admin/users/{id}/mode {trading_mode: LIVE} → admin-service
  → Validates kyc_status=APPROVED
  → Sets trading_mode=LIVE
```

### 3.2 Live Order Flow

```
User → POST /api/orders → order-service
  → Check trading_mode=LIVE AND kyc_status=APPROVED
  → Check TRADING_HALTED flag (Redis)
  → Create Order record (status=PENDING, execution_mode=LIVE)
  → Publish to Redis channel "orders.live"

execution-service (subscribes to "orders.live")
  → Place order on Binance via CCXT
  → Store external_order_id, update status=OPEN
  → Poll Binance until filled / timeout
  → On fill: write OrderFill record
  → Write FeeLedger entry
  → Sync real_wallets balance from Binance
  → Publish to Redis "fills.{user_id}"

notification-service (subscribes to "fills.*")
  → Send in-app notification + email to user
```

### 3.3 Withdrawal Flow

```
User → POST /api/wallet/withdraw → wallet-service
  → Validate kyc_status=APPROVED AND trading_mode=LIVE
  → Lock funds in real_wallets
  → Create withdrawal_request (status=PENDING)

Admin → POST /api/admin/wallet/withdrawals/{id}/approve → wallet-service
  → Release locked funds (debit)
  → Write BalanceLedger entry (WITHDRAWAL)
  → Mark withdrawal_request as APPROVED
  → (External: process actual blockchain transfer)
```

---

## 4. Data Storage & Security Controls

### 4.1 Personal Data Storage

| Data Type | Storage Location | Access Control |
|-----------|-----------------|----------------|
| User credentials | PostgreSQL `users.password_hash` (bcrypt) | user-service only |
| KYC documents | Referenced by path only — actual files stored externally | KYC provider + admin |
| Transaction logs | PostgreSQL `balance_ledger`, `order_fills`, `fee_ledger` | admin-service, audit |
| Audit trail | PostgreSQL `audit_logs` | admin-service |
| Session tokens | HttpOnly cookies (refresh) + Bearer header (access) | user-service |

### 4.2 Encryption

- All data in transit: TLS 1.2+ (nginx terminates SSL)
- Passwords: bcrypt with cost factor 12
- JWT secrets: stored in environment variables, never in code
- Database credentials: Docker secrets / environment variables

### 4.3 Access Control

- Role-based access: STUDENT, TRADER, POWER_USER, PARTNER, ADMIN, SUPER_ADMIN, SUPER_USER
- All admin actions require ADMIN or SUPER_ADMIN JWT role claim
- SUPER_USER accounts are hidden from all non-SUPER_ADMIN callers
- All admin API actions are recorded in `audit_logs`

---

## 5. AML/CFT Controls

### 5.1 Customer Due Diligence (CDD)

- Level 1 (all users): email verification
- Level 2 (LIVE trading): full KYC — government ID + selfie + proof of address + AML screening
- Level 3 (enhanced): configurable threshold triggers additional EDD

### 5.2 Transaction Monitoring

- All deposits and withdrawals are logged in `balance_ledger` (immutable)
- Admin can manually flag transactions for SAR via `POST /api/admin/compliance/sar/{user_id}`
- Monthly compliance reports exportable via `GET /api/admin/compliance/report`

### 5.3 Sanctions Screening

- AML screening is called on KYC submission
- Provider: configurable via `AML_PROVIDER_URL` environment variable
- RISK_REVIEW threshold configurable via `AML_RISK_REVIEW_THRESHOLD`

---

## 6. Business Continuity & Disaster Recovery

- **RTO:** 30 minutes (PostgreSQL), 15 minutes (Redis), 20 minutes (API services)
- **RPO:** 5 minutes (PostgreSQL WAL), best-effort (Redis AOF)
- **DR Runbook:** see `docs/DISASTER_RECOVERY_RUNBOOK.md`
- **Backup:** Daily pg_dump + continuous WAL archiving to off-site storage

---

## 7. Penetration Testing

- Conducted by third-party firm before Phase 5 go-live
- Scope: all public API endpoints, WebSocket, admin panel, authentication
- Results documented in `docs/PENTEST_REPORT.md`
- All critical/high findings resolved before any live user funds accepted

---

## 8. Incident Response

- **Emergency halt:** Admin can halt ALL live trading via `POST /api/admin/trading/halt`
- **Escalation runbook:** see `docs/ESCALATION_RUNBOOK.md`
- **24/7 monitoring runbook:** see `docs/MONITORING_RUNBOOK.md`

---

## 9. Third-Party Dependencies

| Provider | Purpose | Due Diligence Status |
|----------|---------|---------------------|
| Binance | Live order execution (SPOT + Futures) | Licensed VASP |
| [KYC Provider] | Identity verification | [Accredited provider] |
| [AML Provider] | AML/CFT screening | [Accredited provider] |
| SendGrid / AWS SES | Transactional emails | Standard commercial |

---

*This document is submitted in confidence to VARA as part of our licence application and must not be disclosed to third parties.*
