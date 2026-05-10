# STABILIZATION PROGRESS

## 2026-05-10T13:00:00+05:30 — Phase 0 Baseline Snapshot

### Issue Fixed
- None. Phase 0 intentionally performed baseline capture only.

### Files Changed
- `SYSTEM_BASELINE.md` (created)
- `STABILIZATION_PROGRESS.md` (created)
- Baseline evidence logs under `audit-runtime-logs/`

### Verification Performed
- Branch created/switched: `stabilization-phase`
- Frontend production build executed and logged (`EXIT_CODE=0`)
- Backend lint executed and logged (ruff findings present)
- Backend tests executed and logged (`collected 0 items`, `EXIT_CODE=5`)
- Docker compose config validation executed and logged
- Docker compose ps executed and logged (engine unavailable)
- Route inventories generated from service routers and nginx locations

### Remaining Risks
- Critical routing mismatch likely remains for admin wallet topup flow (`/api/admin/wallet/...` path ownership vs gateway route target).
- AML fallback behavior in user-service still potentially permits unsafe clear path when provider is missing.
- CI can report green without real tests due conditional skip logic.
- Docker runtime unavailable on current machine, limiting live container verification until engine is started.

### Next Planned Step
- Phase 1 Task 1 only: admin wallet topup routing stabilization with targeted integration and gateway route verification tests.

## 2026-05-10T13:10:00+05:30 — Phase 1 Task 1: Admin Wallet Topup Routing

### Issue Fixed
- Gateway route mismatch for admin wallet topup path.
- Added explicit nginx route so `/api/admin/wallet/*` is proxied to wallet-service before generic `/api/admin/*`.

### Files Changed
- `infrastructure/nginx/conf.d/default.conf`
- `infrastructure/nginx/tests/test_admin_wallet_route.py`
- `services/wallet-service/tests/test_admin_wallet_topup.py`

### Verification Performed
- Docker compose config validation rerun.
- Frontend production build rerun (`EXIT_CODE=0`).
- Targeted lint on new tests rerun.
- Gateway route verification test passed.
- Wallet admin topup integration tests passed:
	- balance accumulation across calls
	- missing auth rejected
	- non-admin role rejected

### Remaining Risks
- Full end-to-end admin UI wallet topup through running containers was not executed because Docker engine was unavailable on this machine during this run.

### Next Planned Step
- Phase 1 Task 2: remove AML auto-clear fallback and enforce fail-closed LIVE gating.

## 2026-05-10T13:18:00+05:30 — Phase 1 Task 2: AML Fallback Hard-Fail

### Issue Fixed
- Removed AML auto-clear fallback behavior when provider URL is missing.
- Enforced fail-closed guard for enabling LIVE mode when AML provider is not configured.
- Added AML failure audit logging in KYC approval failure path.

### Files Changed
- `services/user-service/app/services/compliance_service.py`
- `services/user-service/app/routers/kyc.py`
- `services/admin-service/app/config.py`
- `services/admin-service/app/routers/admin.py`
- `services/user-service/tests/test_aml_hard_fail.py`
- `services/admin-service/tests/test_live_mode_aml_gate.py`

### Verification Performed
- Frontend production build rerun (`EXIT_CODE=0`).
- Docker compose config validation rerun.
- Lint on changed Task 2 files passed (`EXIT_CODE=0`).
- Task 2 targeted tests passed (`3 passed`):
	- AML service fails closed when provider missing
	- KYC AML failure path includes audit-failure logging contract
	- LIVE mode route contains AML provider hard-fail gate

### Remaining Risks
- Runtime container-level E2E for LIVE activation flow could not be executed in this run due unavailable Docker engine.
- Broader regression suite is still limited; additional integration tests are required in later phases.

### Next Planned Step
- Phase 2 Task 3: build API contract source-of-truth document and begin contract drift reconciliation.

## 2026-05-10T13:20:00+05:30 — Live Container E2E Validation (Admin UI Top-up)

### Issue Fixed
- Runtime blocker discovered during live admin UI check: `GET /api/admin/users` returned 500 because `created_at` schema type in admin-service expected string while API returned datetime.
- Runtime blocker discovered during live top-up check: wallet-service failed `POST /api/admin/wallet/topup` with FK resolution error due missing local users table mirror in SQLAlchemy metadata.
- Cleanup fix applied to wallet-service duplicate `/health` definition to restore lint compliance and avoid route ambiguity.

### Files Changed
- `services/admin-service/app/schemas/admin.py`
- `services/wallet-service/app/models/user_mirror.py`
- `services/wallet-service/app/main.py`

### Verification Performed
- Docker stack started and verified running via compose.
- Browser E2E through gateway on `http://localhost`:
	- login as super admin succeeded
	- navigate to Admin panel succeeded
	- click Top Up for test student user succeeded
	- success message shown in UI (`Credited 321.5 USDT to simulation wallet.`)
- Persistence verified in PostgreSQL: `simulation_wallets.balance = 321.50000000` for test user.
- Auth enforcement verified on gateway route:
	- unauthenticated top-up rejected (`403 Not authenticated`)
	- non-admin top-up rejected (`403 Admin access required`)
- Lint and targeted tests rerun and passed after fixes.
- Frontend production build rerun and passed.

### Remaining Risks
- This validation covered the critical admin wallet top-up path end-to-end; broader regression (other admin modules, websocket auth, and multi-service migration startup checks) remains for later phases.

### Next Planned Step
- Continue strict sequence at Phase 2 Task 3 (API contract source-of-truth and drift reconciliation).
