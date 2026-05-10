# SYSTEM BASELINE

Generated: 2026-05-10
Branch: stabilization-phase
Scope: Phase 0 baseline snapshot only (no functional fixes applied)

## 1) Current Routes Snapshot

Source logs:
- `audit-runtime-logs/40-api-router-prefixes.log`
- `audit-runtime-logs/41-nginx-locations.log`

### FastAPI router prefixes discovered
- admin-service: `/api/admin/users`, `/api/admin`, `/api/admin/fees`, `/api/admin/market`, `/api/admin/options`, `/api/admin/performance`, `/api/admin/trading`
- user-service: `/auth`, `/kyc`, `/partner`, `/users` (mounted by service main app under `/api` in runtime)
- market-data-service: `/api/market`
- order-service: `/api/orders`, `/api/options`
- notification-service: `/api/notifications`, `/api/alerts`
- wallet-service: `/api/wallet`, `/api/admin/wallet` (including admin topup paths)

### Nginx API/WebSocket locations discovered
- Auth: `/api/auth/login`, `/api/auth/register`, `/api/auth/refresh`, `/api/auth/`
- User/KYC/Partner: `/api/users/`, `/api/kyc/`, `/api/partner/`
- Trading/Data: `/api/market/`, `/api/orders/history`, `/api/orders/fills`, `/api/orders/margin`, `/api/orders/`, `/api/options/`, `/api/positions`, `/api/portfolio/`
- Wallet: `/api/wallet/`
- Notifications: `/api/notifications`, `/api/alerts`
- Admin: `/api/admin/`
- WebSocket: `/ws/`, `/ws/user/portfolio`, `/ws/user/notifications`, `/ws/user/`

## 2) Current Services Snapshot

Source log:
- `audit-runtime-logs/42-compose-services.log`

Compose services:
- `postgres`
- `redis`
- `risk-service`
- `simulation-engine`
- `wallet-service`
- `notification-service`
- `order-service`
- `user-service`
- `web-frontend`
- `worker`
- `admin-service`
- `market-data-service`
- `portfolio-service`
- `nginx`

## 3) Current Docker Status

Source log:
- `audit-runtime-logs/02-docker-ps.log`

Result:
- Docker Engine connection failed on this machine at baseline capture time:
  - `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`
- Compose config can still be rendered (see `audit-runtime-logs/03-docker-config.log`).
- Compose warns: `version` key in `docker-compose.yml` is obsolete.

## 4) Current Build Status

Source log:
- `audit-runtime-logs/10-frontend-build.log`

Result:
- Frontend production build: PASS
- Framework: Next.js 16.2.5
- Static routes generated successfully

## 5) Current Failing Areas (Baseline)

Source logs:
- `audit-runtime-logs/22-backend-lint-ruff.log`
- `audit-runtime-logs/31-backend-tests-pytest.log`
- `audit-runtime-logs/02-docker-ps.log`

Observed failures:
- Backend lint: FAIL (multiple `F401` unused imports across services)
- Backend tests: FAIL (pytest exit code 5 because no tests were collected)
- Docker runtime status check: FAIL (daemon unavailable)

Known critical audit mismatch confirmed in baseline route inventory:
- Nginx routes `/api/admin/` to admin-service while admin wallet topup endpoints exist in wallet-service under `/api/admin/wallet/...`.

## 6) Current Test Count

Source log:
- `audit-runtime-logs/31-backend-tests-pytest.log`

Result:
- Collected tests: `0`
- Pytest outcome: `no tests ran`
- Exit code: `5`

## 7) Current CI Behavior

Source files:
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`

CI pipeline behavior (baseline):
- `lint` job runs ruff on service directories.
- `build` job builds backend, nginx, and frontend images.
- `test` job conditionally runs pytest **only if tests are found**.
- If no test files exist, CI prints: `No test files found yet. CI passes.` (can produce false green).

Deployment behavior (baseline):
- Main branch deploy workflow builds/pushes images and triggers Coolify webhook.

## 8) Baseline Command Evidence Index

- `audit-runtime-logs/00-baseline-timestamp.log`
- `audit-runtime-logs/01-git-status.log`
- `audit-runtime-logs/02-docker-ps.log`
- `audit-runtime-logs/03-docker-config.log`
- `audit-runtime-logs/10-frontend-build.log`
- `audit-runtime-logs/21-backend-tools-install.log`
- `audit-runtime-logs/22-backend-lint-ruff.log`
- `audit-runtime-logs/31-backend-tests-pytest.log`
- `audit-runtime-logs/40-api-router-prefixes.log`
- `audit-runtime-logs/41-nginx-locations.log`
- `audit-runtime-logs/42-compose-services.log`
