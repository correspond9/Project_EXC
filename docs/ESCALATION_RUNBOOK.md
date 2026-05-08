# Escalation Runbook — XChange Platform

**Owner:** On-Call Engineering Lead  
**Last Updated:** [Date]  
**Applicability:** All incidents affecting real user funds or live trading

---

## 1. Emergency Trading Halt Procedure

### When to halt

Halt ALL live trading immediately if ANY of the following occur:
- Orders are being duplicated or filled at incorrect prices
- Real wallet balances are updating incorrectly
- Binance API is returning unexpected errors (not normal rate limits)
- A security breach or unauthorized access is suspected
- Any condition where continued trading could cause uncontrolled financial loss

### How to halt

**Via Admin Panel (preferred):**
1. Log in to the Admin Panel at `http(s)://<platform>/admin`
2. Navigate to **Trading Controls**
3. Click **"Halt All Trading"**
4. Confirm the action
5. Verify halt is active: the status badge turns red and shows "HALTED"

**Via API (if admin panel is unavailable):**
```bash
curl -X POST https://<platform>/api/admin/trading/halt \
  -H "Authorization: Bearer <SUPER_ADMIN_JWT>"
```

Expected response:
```json
{"halted": true, "message": "Platform trading has been halted."}
```

**Verify halt is active:**
```bash
curl https://<platform>/api/admin/trading/status \
  -H "Authorization: Bearer <ADMIN_JWT>"
# → {"halted": true}
```

**Direct Redis (if API is unavailable):**
```bash
docker exec <redis-container> redis-cli SET platform:trading_halted 1
```

---

## 2. Resuming Trading

Only resume after the root cause has been confirmed and resolved.

**Via API:**
```bash
curl -X POST https://<platform>/api/admin/trading/resume \
  -H "Authorization: Bearer <SUPER_ADMIN_JWT>"
```

**Checklist before resuming:**
- [ ] Root cause identified and documented in incident report
- [ ] Fix deployed or confirmed as not affecting trading
- [ ] All open orders reconciled — run reconciliation manually if needed:
  - Check execution-service logs for any LIVE orders in PENDING/OPEN state
  - Confirm their status matches Binance
- [ ] Finance team notified of any financial impact
- [ ] MLRO notified if any AML/compliance concern exists

---

## 3. Severity Classification

| Severity | Definition | Response Time | Action |
|----------|-----------|---------------|--------|
| P1 — Critical | Financial loss / security breach / wrong fills | Immediate | Halt trading, escalate to CTO + CEO |
| P2 — High | Orders failing / balances stuck / KYC broken | < 30 min | Investigate, halt if risk of P1 |
| P3 — Medium | Feature degraded, non-financial | < 2 hours | Fix or schedule hotfix |
| P4 — Low | UI bugs, cosmetic issues | Next sprint | Log ticket |

---

## 4. Escalation Contacts

| Role | Responsibility | Contact |
|------|---------------|---------|
| On-Call Engineer | First responder, initial diagnosis | [PagerDuty rotation] |
| Engineering Lead | Approves halt / resume, coordinates fix | [Contact] |
| CTO | P1 incidents, VARA communication | [Contact] |
| MLRO / Compliance | AML/CFT incidents, SAR filings | [Contact] |
| CEO | Media/PR, VARA urgent notification | [Contact] |

---

## 5. Reconciliation After Halt

After any halt and resume:
1. Check `order_fills` for any LIVE orders placed just before the halt
2. Compare with Binance via execution-service reconciliation loop (runs every 5 min automatically)
3. If any fills are missing, manually trigger reconciliation:
   ```bash
   # Check execution-service logs
   docker logs execution-service --tail=200
   ```
4. Correct any discrepancies in `balance_ledger` (append-only) via admin wallet correction entries
5. Notify affected users if their orders were impacted

---

## 6. Incident Report Template

After every P1/P2 incident, file an incident report within 24 hours:

```
Incident ID: INC-[YYYY-MM-DD-NNN]
Date/Time: 
Severity: P1 / P2
Duration: 
Impact: (number of users affected, financial amount if any)
Root Cause: 
Timeline:
  HH:MM — Event detected
  HH:MM — Trading halted
  HH:MM — Root cause identified
  HH:MM — Fix deployed
  HH:MM — Trading resumed
Actions Taken:
Prevention Measures:
VARA Notification Required: YES / NO
```

---

## 7. VARA Notification Requirements

Under VARA regulations, notify VARA within **24 hours** of:
- Any security incident affecting user funds
- Any significant system outage (> 4 hours)
- Any suspicious activity pattern

Contact: [VARA regulatory point of contact]
