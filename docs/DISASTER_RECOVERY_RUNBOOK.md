# Disaster Recovery Runbook — XChange Platform

**Version:** 1.0  
**Owner:** DevOps / Platform Team  
**Last Reviewed:** [Date]

---

## RTO / RPO Targets

| Tier | Service | RTO (Recovery Time) | RPO (Recovery Point) |
|------|---------|--------------------|--------------------|
| T1 | PostgreSQL (primary DB) | 30 minutes | 5 minutes |
| T1 | Redis (order bus / cache) | 15 minutes | Best-effort (AOF) |
| T2 | All API services (Docker) | 20 minutes | N/A (stateless) |
| T2 | nginx / frontend | 10 minutes | N/A |
| T3 | Execution service (LIVE) | 60 minutes | Reconcile via Binance API |

---

## 1. Pre-Requisites

- Docker + Docker Compose installed on recovery host
- `.env.production` file available (stored in secure vault, NOT in git)
- Latest DB backup accessible (see Section 3)
- DNS / firewall rules updated to point to new host if needed

---

## 2. Incident Classification

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | Full platform outage / data loss risk | Immediate |
| P1 | Single service down, orders failing | 15 minutes |
| P2 | Degraded performance, non-critical feature | 1 hour |
| P3 | Cosmetic / low-impact issue | Next business day |

---

## 3. PostgreSQL Recovery

### 3a. Automated Backup Schedule
- **Full backup:** Daily at 02:00 UTC via `pg_dump`
- **WAL archiving:** Continuous to S3/backup store
- **Retention:** 30 days

### 3b. Restore Steps

```bash
# 1. Stop all services that write to DB
docker compose stop

# 2. Drop and recreate database (DESTRUCTIVE — confirm before running)
docker exec -it xchange_postgres psql -U xchange -c "DROP DATABASE xchange_db;"
docker exec -it xchange_postgres psql -U xchange -c "CREATE DATABASE xchange_db;"

# 3. Restore from latest backup
docker exec -i xchange_postgres psql -U xchange xchange_db < /backups/xchange_db_YYYY-MM-DD.sql

# 4. Verify row counts
docker exec -it xchange_postgres psql -U xchange xchange_db \
  -c "SELECT 'users' AS tbl, COUNT(*) FROM users
      UNION ALL SELECT 'orders', COUNT(*) FROM orders
      UNION ALL SELECT 'real_wallets', COUNT(*) FROM real_wallets;"

# 5. Restart services
docker compose up -d
```

### 3c. Point-in-Time Recovery (PITR)
If WAL archiving is configured, use `pg_restore` with `--target-time` to recover to a specific timestamp before the incident.

---

## 4. Redis Recovery

Redis uses AOF (Append-Only File) persistence.

```bash
# 1. Stop redis
docker compose stop redis

# 2. Restore AOF file from backup
cp /backups/appendonly_YYYY-MM-DD.aof /data/redis/appendonly.aof

# 3. Restart redis
docker compose start redis

# 4. Verify connectivity
docker exec -it xchange_redis redis-cli PING
```

**Note:** In-flight simulation orders in the `orders.simulation` channel will be lost. The simulation engine's fill loop will ignore stale order IDs (they won't match open DB records).

**LIVE orders:** After Redis recovery, the execution-service reconciliation loop (runs every 5 minutes) will re-check all open LIVE orders against Binance and record any missed fills.

---

## 5. Full Platform Recovery (New Host)

```bash
# 1. Clone repo
git clone https://github.com/correspond9/Project_EXC.git
cd "Project_EXC"

# 2. Copy env file from vault
cp /vault/xchange.env.production .env

# 3. Start all services (simulation mode)
docker compose up -d

# 4. Start execution service (LIVE mode)
docker compose --profile live up -d execution-service

# 5. Run DB migrations (auto-run on service start via Dockerfile CMD)
# Verify:
docker compose logs wallet-service | Select-String "alembic"

# 6. Smoke test
curl http://localhost/health
curl http://localhost/api/auth/login -X POST -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"test"}'
```

---

## 6. Execution Service Recovery (LIVE Outage)

If the execution-service crashes while orders are in `PENDING`/`OPEN` state:

1. Restart execution-service: `docker compose --profile live restart execution-service`
2. The reconciliation loop runs within 5 minutes of startup
3. It will poll Binance for all `OPEN` LIVE orders and record missed fills
4. Check logs: `docker compose logs execution-service --tail=100`

---

## 7. DR Drill Procedure

Drills should be run quarterly in a staging environment.

| Step | Action | Expected Outcome |
|------|--------|------------------|
| 1 | Simulate DB host failure (`docker stop postgres`) | Services return 503 |
| 2 | Restore DB from latest backup | All data recovered |
| 3 | Restart all services | 200 OK on /health |
| 4 | Place a test order in SIMULATION mode | Order fills within 5s |
| 5 | Verify wallet balance updated | Correct balance shown |
| 6 | Document RTO achieved vs target | Log in drill report |

---

## 8. Contacts

| Role | Name | Contact |
|------|------|---------|
| On-call Engineer | [Name] | [Phone / Signal] |
| DB Admin | [Name] | [Phone / Signal] |
| Binance Account Owner | [Name] | [Phone / Signal] |
| Compliance Officer | [Name] | [Phone / Signal] |

---

*This runbook must be reviewed after every major infrastructure change and at least annually.*
