# 24/7 Monitoring Runbook — XChange Platform

**Owner:** On-Call Engineering Team  
**Last Updated:** [Date]  
**Tools:** Grafana (port 3001), Prometheus (port 9090), Docker logs

---

## 1. Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API p95 latency | > 500ms | > 2000ms | Check service logs, DB query plans |
| 5xx error rate | > 0.5% | > 2% | Check service, consider rollback |
| Order placement failure rate | > 1% | > 5% | Halt trading (Sprint 20 halt endpoint) |
| WebSocket disconnect rate | > 5% | > 20% | Check nginx, market-data-service |
| DB connection pool exhaustion | > 80% | > 95% | Scale services or increase pool |
| Redis memory usage | > 70% | > 90% | Review TTLs, flush stale keys |
| Disk usage | > 70% | > 85% | Archive logs, expand storage |
| CPU usage (any service) | > 70% | > 90% | Scale horizontally |

---

## 2. Grafana Dashboards

Access: `http(s)://<platform>/grafana`  
Default login: admin / [set during deploy]

| Dashboard | URL | Description |
|-----------|-----|-------------|
| API Overview | `/grafana/d/xchange-api-overview` | Request rate, p95 latency, error rate per service |
| Order Throughput | `/grafana/d/xchange-orders` | Orders placed/filled/failed over time |
| Infrastructure | `/grafana/d/xchange-infra` | CPU, memory, disk, DB connections |

---

## 3. On-Call Response Playbook

### P1 — Critical (financial impact / security)

1. **Check:** Is it affecting LIVE orders? → Check Grafana order failure rate
2. **Halt:** If live orders are being misrouted or filled incorrectly:
   ```bash
   curl -X POST https://<platform>/api/admin/trading/halt \
     -H "Authorization: Bearer <SUPER_ADMIN_JWT>"
   ```
3. **Identify:** Check execution-service logs
   ```bash
   docker logs execution-service --tail=200 -f
   ```
4. **Escalate:** Immediately page Engineering Lead + CTO
5. **Document:** Start incident report (see `ESCALATION_RUNBOOK.md`)

### P2 — High (service degraded, no immediate financial impact)

1. **Identify** which service is slow/erroring:
   - Grafana → API Overview → filter by service
   - `docker ps` to check container health
2. **Restart** if container is crashed:
   ```bash
   docker compose restart <service-name>
   ```
3. **Review** recent deployments — was there a recent push?
4. **Escalate** to Engineering Lead if not resolved within 30 minutes

### P3/P4 — Lower severity

- Log ticket in issue tracker
- Fix in next sprint or hotfix

---

## 4. Useful Commands

### View logs
```bash
# All services
docker compose logs -f --tail=50

# Specific service
docker compose logs order-service -f --tail=100

# Execution service (live trading)
docker logs execution-service --tail=500 | grep -i "error\|fill\|reject"
```

### Check Redis halt flag
```bash
docker exec <redis-container> redis-cli GET platform:trading_halted
# Returns: (nil) = not halted, "1" = halted
```

### Check PostgreSQL connections
```bash
docker exec <postgres-container> psql -U xchange -c \
  "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

### Manual reconciliation check (LIVE orders)
```bash
# Check for orders stuck in OPEN or PENDING state
docker exec <postgres-container> psql -U xchange xchange_db -c \
  "SELECT id, user_id, symbol, status, created_at FROM orders \
   WHERE execution_mode='LIVE' AND status IN ('OPEN','PENDING') \
   AND created_at < now() - interval '30 minutes';"
```

### Check Prometheus targets
```
http://localhost:9090/targets
```

---

## 5. Escalation Matrix

| Condition | Who to page |
|-----------|------------|
| Trading halted automatically or manually | Engineering Lead + CTO |
| User funds balance discrepancy found | Engineering Lead + Finance + MLRO |
| Security breach suspected | CTO + Security team immediately |
| VARA regulatory query received | MLRO + CEO |
| Data centre outage | Engineering Lead → invoke DR runbook |

**DR Runbook:** `docs/DISASTER_RECOVERY_RUNBOOK.md`  
**Escalation Runbook:** `docs/ESCALATION_RUNBOOK.md`

---

## 6. Scheduled Checks (Daily)

Run at 09:00 UAE time by on-call:

- [ ] Grafana: no red alerts in last 24h
- [ ] Check PostgreSQL disk usage
- [ ] Check Redis memory: `docker exec <redis> redis-cli INFO memory | grep used_memory_human`
- [ ] Verify execution-service is connected: `GET /api/admin/trading/status`
- [ ] Check withdrawal queue: any pending > 24h need admin action
- [ ] Verify compliance report job ran (check admin-service logs)

---

## 7. Weekly Checks

- [ ] Review all P1/P2 incidents from the past week
- [ ] Run k6 smoke test against staging
- [ ] Review PostgreSQL WAL archiving status
- [ ] Check VARA regulatory inbox for communications
- [ ] Rotate Binance/Deribit API keys if scheduled
