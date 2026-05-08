# Load Test Results

> **Platform:** XChange Crypto Trading Platform  
> **Test Date:** Sprint 12  
> **Tool:** [k6](https://k6.io/) (recommended) / Locust  
> **Environment:** Docker Compose (local) + staging

---

## Test Scenarios

### 1. WebSocket Concurrency — 500 Simultaneous Users

**Target:** 500 concurrent WebSocket connections to the notification and market data endpoints.

**Endpoints tested:**
- `ws://<host>/ws/user/notifications` — per-user notification stream
- `ws://<host>/ws/market/ticker/*` — market ticker broadcast

**k6 script (k6/ws_load.js):**
```js
import ws from 'k6/ws';
import { check } from 'k6';

export const options = {
  vus: 500,
  duration: '2m',
};

export default function () {
  const url = 'ws://localhost/ws/market/ticker/BTCUSDT';
  const res = ws.connect(url, {}, function (socket) {
    socket.on('open', () => socket.setTimeout(() => socket.close(), 60000));
    socket.on('message', (data) => {
      check(data, { 'message received': (d) => d.length > 0 });
    });
  });
  check(res, { 'status was 101': (r) => r && r.status === 101 });
}
```

**Baseline targets:**
| Metric | Target |
|---|---|
| Connection success rate | ≥ 99% |
| Message delivery latency (p95) | < 200ms |
| Memory per connection (nginx) | < 50KB |
| Server CPU under load | < 70% |

---

### 2. Order Placement — 200 Concurrent Users

**Target:** 200 users placing spot orders simultaneously over 1 minute.

**Endpoint:** `POST /api/orders/spot`

**k6 script (k6/order_load.js):**
```js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 200,
  duration: '1m',
};

const BASE_URL = 'http://localhost';

export default function () {
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: `loadtest_${__VU}@test.com`,
    password: 'TestPass123!',
  }), { headers: { 'Content-Type': 'application/json' } });

  check(loginRes, { 'login 200': (r) => r.status === 200 });

  const orderRes = http.post(`${BASE_URL}/api/orders/spot`, JSON.stringify({
    symbol: 'BTCUSDT',
    side: 'BUY',
    quantity: 0.001,
    order_type: 'MARKET',
  }), { headers: { 'Content-Type': 'application/json' } });

  check(orderRes, {
    'order accepted': (r) => r.status === 200 || r.status === 201,
    'no 500 errors': (r) => r.status < 500,
  });

  sleep(1);
}
```

**Baseline targets:**
| Metric | Target |
|---|---|
| Order acceptance rate | ≥ 99% |
| p50 latency | < 100ms |
| p95 latency | < 500ms |
| p99 latency | < 1000ms |
| Error rate (5xx) | < 0.1% |

---

### 3. REST API Stress Test — General Endpoints

**Target:** General API endpoints under mixed load.

**Endpoints:**
- `GET /api/wallet/balances`
- `GET /api/orders/history`
- `GET /api/market/tickers`
- `GET /api/futures/positions`

**Baseline targets:**
| Metric | Target |
|---|---|
| Throughput | ≥ 1000 req/s |
| p95 latency | < 300ms |
| DB connection pool exhaustion | None |

---

## How to Run

### With k6

```bash
# Install k6 (Windows)
choco install k6

# Run WebSocket test
k6 run k6/ws_load.js

# Run Order placement test
k6 run k6/order_load.js
```

### With Locust

```bash
pip install locust
locust -f locustfile.py --host=http://localhost --users 200 --spawn-rate 20
```

---

## Pre-Test Checklist

- [ ] All services running via `docker compose up -d`
- [ ] Load test user accounts pre-seeded (use seed script)
- [ ] Redis AOF disabled temporarily during test (for fair latency readings)
- [ ] PostgreSQL `max_connections = 200` confirmed in `postgresql.conf`
- [ ] nginx `worker_connections 1024` confirmed

---

## Known Bottlenecks & Mitigations

| Area | Risk | Mitigation |
|---|---|---|
| PostgreSQL connections | Pool exhaustion at 200+ VUs | Use `asyncpg` pool size = 20 per service; use PgBouncer if needed |
| Redis pub/sub | Fan-out latency at 500+ WS connections | Redis 7 with `io-threads 4` |
| Order matching (simulation engine) | Single-threaded Celery worker | Scale to 2–4 Celery workers |
| WebSocket memory | nginx buffering 500+ connections | Tune `proxy_read_timeout 3600s` |

---

*Results to be filled in after test run on staging environment.*
