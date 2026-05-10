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
