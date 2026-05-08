/**
 * XChange Platform — k6 Load Test Scenarios
 * Sprint 23 — Pre-Launch Performance Validation
 *
 * Scenarios:
 *   1. ws_viewers     — 500 concurrent WebSocket market-data viewers
 *   2. order_placers  — 200 concurrent REST order placements
 *   3. portfolio_viewers — 100 concurrent portfolio/history queries
 *
 * Prerequisites:
 *   - k6 installed: https://k6.io/docs/getting-started/installation/
 *   - Set BASE_URL env var (default: http://localhost)
 *   - Set TRADER_TOKEN env var (valid JWT for a SIMULATION trader)
 *   - Set SYMBOLS env var (comma-separated, default: BTCUSDT,ETHUSDT)
 *
 * Run:
 *   k6 run --env BASE_URL=https://your.platform --env TRADER_TOKEN=<jwt> load-tests/k6/scenarios.js
 *
 * Success criteria (P95 thresholds):
 *   - REST API p95 < 500ms
 *   - WebSocket connect success rate > 99%
 *   - Order placement error rate < 1%
 */

import http from "k6/http";
import ws from "k6/ws";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

// ── Custom metrics ────────────────────────────────────────────────────────────
const orderErrors = new Rate("order_errors");
const wsConnectErrors = new Rate("ws_connect_errors");
const orderLatency = new Trend("order_latency_ms", true);
const portfolioLatency = new Trend("portfolio_latency_ms", true);

// ── Configuration ─────────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || "http://localhost";
const WS_BASE = BASE_URL.replace(/^http/, "ws");
const TOKEN = __ENV.TRADER_TOKEN || "";
const SYMBOLS = (__ENV.SYMBOLS || "BTCUSDT,ETHUSDT").split(",");

// ── Thresholds ─────────────────────────────────────────────────────────────────
export const options = {
  scenarios: {
    // 500 concurrent WebSocket viewers — ramp up over 60s, hold 3 min
    ws_viewers: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "60s", target: 500 },
        { duration: "180s", target: 500 },
        { duration: "30s", target: 0 },
      ],
      exec: "wsViewerScenario",
    },

    // 200 concurrent order placers — ramp up over 30s, hold 2 min
    order_placers: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 200 },
        { duration: "120s", target: 200 },
        { duration: "30s", target: 0 },
      ],
      exec: "orderPlacerScenario",
      startTime: "30s", // start after ws_viewers are ramping
    },

    // 100 concurrent portfolio viewers
    portfolio_viewers: {
      executor: "constant-vus",
      vus: 100,
      duration: "3m",
      exec: "portfolioViewerScenario",
      startTime: "30s",
    },
  },

  thresholds: {
    // REST p95 under 500ms
    http_req_duration: ["p(95)<500"],
    // Custom order latency
    order_latency_ms: ["p(95)<500"],
    portfolio_latency_ms: ["p(95)<300"],
    // Error rates
    order_errors: ["rate<0.01"],      // < 1% order errors
    ws_connect_errors: ["rate<0.01"], // < 1% WS connect failures
  },
};

const AUTH_HEADERS = {
  Authorization: `Bearer ${TOKEN}`,
  "Content-Type": "application/json",
};

// ── Scenario: WebSocket market data viewer ────────────────────────────────────
export function wsViewerScenario() {
  const symbol = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];
  const wsUrl = `${WS_BASE}/ws/market/${symbol}`;

  const res = ws.connect(wsUrl, {}, function (socket) {
    socket.on("open", () => {
      // Subscribe to ticker
      socket.send(JSON.stringify({ type: "subscribe", channel: `ticker.${symbol}` }));
    });

    socket.on("message", (data) => {
      // Just consume messages
    });

    socket.on("error", (e) => {
      wsConnectErrors.add(1);
    });

    // Hold connection for 30-60 seconds
    socket.setTimeout(() => socket.close(), Math.floor(Math.random() * 30000) + 30000);
  });

  const connected = check(res, { "ws connected": (r) => r && r.status === 101 });
  if (!connected) wsConnectErrors.add(1);

  sleep(1);
}

// ── Scenario: Order placer (simulation mode) ──────────────────────────────────
export function orderPlacerScenario() {
  const symbol = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];
  const side = Math.random() > 0.5 ? "BUY" : "SELL";

  const payload = JSON.stringify({
    symbol: `${symbol.slice(0, -4)}/${symbol.slice(-4)}`, // BTCUSDT → BTC/USDT
    side: side,
    order_type: "MARKET",
    market_type: "SPOT",
    quantity: "0.001",
  });

  const start = Date.now();
  const res = http.post(`${BASE_URL}/api/orders`, payload, { headers: AUTH_HEADERS });
  orderLatency.add(Date.now() - start);

  const ok = check(res, {
    "order placed (201)": (r) => r.status === 201,
    "has order_id": (r) => {
      try {
        return JSON.parse(r.body).order_id !== undefined;
      } catch {
        return false;
      }
    },
  });

  if (!ok) orderErrors.add(1);
  else orderErrors.add(0);

  sleep(Math.random() * 3 + 1); // 1–4 second think time
}

// ── Scenario: Portfolio viewer ─────────────────────────────────────────────────
export function portfolioViewerScenario() {
  const start = Date.now();
  const res = http.get(`${BASE_URL}/api/portfolio`, { headers: AUTH_HEADERS });
  portfolioLatency.add(Date.now() - start);

  check(res, {
    "portfolio ok (200)": (r) => r.status === 200,
  });

  sleep(Math.random() * 5 + 2); // 2–7 second between portfolio reads
}
