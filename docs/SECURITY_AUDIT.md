# Security Audit — OWASP Top 10 Review

> **Platform:** XChange Crypto Trading Platform  
> **Sprint:** 12  
> **Standard:** OWASP Top 10 (2021)

---

## A01 — Broken Access Control

| Check | Status | Detail |
|---|---|---|
| All protected endpoints require JWT | ✅ PASS | `get_current_user` dependency on every route |
| Admin endpoints enforce `role == ADMIN` | ✅ PASS | `require_admin` dependency in admin-service |
| SUPER_USER visibility restricted to SUPER_ADMIN | ✅ PASS | Non-SUPER_ADMIN callers receive not-found semantics for SUPER_USER records |
| Users cannot access other users' data | ✅ PASS | All queries filter by `user_id` from JWT `sub` |
| Futures positions isolated per user | ✅ PASS | `WHERE user_id = :uid` on all position queries |
| IDOR on wallet top-up | ✅ PASS | Top-up only via admin endpoint, not user-facing |
| Partner referred-trade visibility permissioned | ✅ PASS | Access requires explicit `VIEW_REFERRED_TRADE_HISTORY` grant |

**Recommendation:** Add rate limiting on login endpoint (e.g. 5 attempts/min per IP via nginx `limit_req`).

---

## A02 — Cryptographic Failures

| Check | Status | Detail |
|---|---|---|
| Passwords hashed with bcrypt | ✅ PASS | `passlib[bcrypt]` used in auth-service |
| JWT signed with HS256 + `SECRET_KEY` from env | ✅ PASS | Never hardcoded |
| HttpOnly cookie for refresh token | ✅ PASS | `httponly=True, secure=True, samesite='lax'` |
| No sensitive data in JWT payload | ✅ PASS | Only `sub` (user_id), `exp`, `role` |
| HTTPS enforced in production | ⚠️ REVIEW | nginx config has no TLS block — add SSL termination before production |

**Action required:** Configure TLS in nginx (`ssl_certificate`, `ssl_certificate_key`) before any production deployment.

---

## A03 — Injection

| Check | Status | Detail |
|---|---|---|
| All DB queries use parameterised statements | ✅ PASS | SQLAlchemy ORM + `text()` with `:param` binds |
| No raw f-string SQL | ✅ PASS | Reviewed all services |
| Redis keys use fixed prefixes + UUID | ✅ PASS | `ticker:{SYMBOL}`, `fills.{user_id}` — UUIDs from DB |
| Input validation via Pydantic models | ✅ PASS | All request bodies validated |

---

## A04 — Insecure Design

| Check | Status | Detail |
|---|---|---|
| Simulation wallet top-up is admin-only | ✅ PASS | `POST /api/admin/wallet/topup` requires ADMIN role |
| Options contract creation is admin-only | ✅ PASS | `POST /api/admin/options/contracts` requires ADMIN role |
| Fee configuration is admin-only | ✅ PASS | `PUT /api/admin/fees/*` requires ADMIN role |
| Users cannot self-promote role | ✅ PASS | Role set only at registration, no user-facing role update |

---

## A05 — Security Misconfiguration

| Check | Status | Detail |
|---|---|---|
| Debug mode disabled in production | ✅ PASS | No `debug=True` in any FastAPI app |
| CORS restricted | ⚠️ REVIEW | `allow_origins=["*"]` in some services — restrict to frontend origin in production |
| Sensitive env vars not committed | ✅ PASS | `SECRET_KEY`, `DATABASE_URL` loaded from environment |
| Docker containers run as non-root | ⚠️ REVIEW | Add `USER nonroot` to Dockerfiles for production hardening |

**Action:** Update CORS in all services: `allow_origins=["https://your-domain.com"]` before production.

---

## A06 — Vulnerable and Outdated Components

| Check | Status | Detail |
|---|---|---|
| Python dependencies pinned | ✅ PASS | `requirements.txt` has version pins |
| No known CVE in core deps | ✅ PASS | `fastapi >= 0.109`, `sqlalchemy >= 2.0`, `python-jose >= 3.3` |
| Frontend dependencies audited | ⚠️ REVIEW | Run `npm audit` before production — address any high/critical findings |

---

## A07 — Identification and Authentication Failures

| Check | Status | Detail |
|---|---|---|
| Access token expires in 15 min | ✅ PASS | `exp = now + 15min` |
| Refresh token 7-day HttpOnly cookie | ✅ PASS | Rotated on each use |
| No credentials in URL parameters | ✅ PASS | Auth via JSON body + cookies only |
| Password minimum length enforced | ⚠️ REVIEW | Add `min_length=8` Pydantic validator to RegisterRequest |
| Account lockout after failed logins | ⚠️ REVIEW | Not implemented — add Redis-based attempt counter |

---

## A08 — Software and Data Integrity Failures

| Check | Status | Detail |
|---|---|---|
| No `pickle` or unsafe deserialization | ✅ PASS | JSON only for all inter-service communication |
| Redis messages validated on receipt | ✅ PASS | `json.loads()` with try/except |

---

## A09 — Security Logging and Monitoring Failures

| Check | Status | Detail |
|---|---|---|
| Auth failures logged | ⚠️ REVIEW | Add structured logging for failed login attempts |
| Order anomalies logged | ✅ PASS | Order placement errors logged via uvicorn |
| Liquidation events recorded in DB | ✅ PASS | `liquidations` table with timestamp |

---

## A10 — Server-Side Request Forgery (SSRF)

| Check | Status | Detail |
|---|---|---|
| No user-supplied URLs fetched by backend | ✅ PASS | No URL fetch endpoints exist |
| External price feeds (future) | N/A | Not yet implemented |

---

## Summary

| Rating | Count |
|---|---|
| ✅ PASS | 28 |
| ⚠️ REVIEW (pre-production action) | 8 |
| ❌ FAIL | 0 |

### Pre-Production Checklist
- [ ] Configure TLS in nginx
- [ ] Restrict CORS to production domain
- [ ] Add `USER nonroot` to all Dockerfiles
- [ ] Add `min_length=8` to RegisterRequest password validator
- [ ] Add nginx `limit_req` on `/api/auth/login`
- [ ] Add Redis-based login attempt counter
- [ ] Run `npm audit` on frontend and fix high/critical
- [ ] Enable structured logging for security events
