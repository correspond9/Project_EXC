"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  CrosshairMode,
} from "lightweight-charts";
import api from "@/lib/api";
import { wsUrl } from "@/lib/ws";
import { useAuthStore } from "@/store/authStore";

// ── Types ──────────────────────────────────────────────────────────────────────

interface Ticker {
  symbol: string;
  last_price: string;
  price_change_pct: string;
  high_24h: string;
  low_24h: string;
  volume_24h: string;
}

interface OrderBookEntry {
  price: string;
  quantity: string;
}

interface OrderBook {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
}

interface WalletBalance {
  currency: string;
  balance: string;
  available_balance: string;
}

// ── Constants ──────────────────────────────────────────────────────────────────

const SYMBOLS = [
  "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
  "ADAUSDT","DOGEUSDT","AVAXUSDT","DOTUSDT","MATICUSDT",
];

const INTERVALS = ["1m", "5m", "1h", "1d"];

// ── Component ──────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { accessToken } = useAuthStore();
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [interval, setInterval] = useState("1h");
  const [ticker, setTicker] = useState<Ticker | null>(null);
  const [orderBook, setOrderBook] = useState<OrderBook | null>(null);
  const [wallet, setWallet] = useState<WalletBalance | null>(null);

  // Order form
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [orderMsg, setOrderMsg] = useState("");

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // ── Init chart ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!chartContainerRef.current) return;
    const chart = createChart(chartContainerRef.current, {
      layout: { background: { color: "#1c2030" }, textColor: "#e2e8f0" },
      grid: { vertLines: { color: "#2a3045" }, horzLines: { color: "#2a3045" } },
      crosshair: { mode: CrosshairMode.Normal },
      timeScale: { timeVisible: true, secondsVisible: false },
      width: chartContainerRef.current.clientWidth,
      height: 340,
    });
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      if (chartContainerRef.current)
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  // ── Load historical klines ───────────────────────────────────────────────────
  useEffect(() => {
    if (!candleSeriesRef.current) return;
    api
      .get(`/api/market/klines/${symbol}`, { params: { interval, limit: 200 } })
      .then((res) => {
        const data: CandlestickData[] = res.data.map((k: any) => ({
          time: Math.floor(k.open_time / 1000) as any,
          open: parseFloat(k.open_price),
          high: parseFloat(k.high_price),
          low: parseFloat(k.low_price),
          close: parseFloat(k.close_price),
        }));
        candleSeriesRef.current?.setData(data);
        chartRef.current?.timeScale().fitContent();
      })
      .catch(() => {});
  }, [symbol, interval]);

  // ── WebSocket: live candle updates ───────────────────────────────────────────
  useEffect(() => {
    const ws = new WebSocket(wsUrl(`/market/${symbol}/kline/${interval}`));
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.error) return;
        const candle: CandlestickData = {
          time: Math.floor(msg.open_time / 1000) as any,
          open: parseFloat(msg.open_price),
          high: parseFloat(msg.high_price),
          low: parseFloat(msg.low_price),
          close: parseFloat(msg.close_price),
        };
        candleSeriesRef.current?.update(candle);
      } catch (_) {}
    };
    return () => ws.close();
  }, [symbol, interval]);

  // ── WebSocket: live ticker ───────────────────────────────────────────────────
  useEffect(() => {
    const ws = new WebSocket(wsUrl(`/market/${symbol}/ticker`));
    ws.onmessage = (ev) => {
      try { setTicker(JSON.parse(ev.data)); } catch (_) {}
    };
    return () => ws.close();
  }, [symbol]);

  // ── WebSocket: live order book ───────────────────────────────────────────────
  useEffect(() => {
    const ws = new WebSocket(wsUrl(`/market/${symbol}/orderbook`));
    ws.onmessage = (ev) => {
      try { setOrderBook(JSON.parse(ev.data)); } catch (_) {}
    };
    return () => ws.close();
  }, [symbol]);

  // ── Fetch simulation wallet balance ─────────────────────────────────────────
  useEffect(() => {
    api
      .get("/api/wallet/simulation")
      .then((res) => {
        const usdt = res.data.find((w: WalletBalance) => w.currency === "USDT");
        if (usdt) setWallet(usdt);
      })
      .catch(() => {});
  }, []);

  // ── WebSocket: live fill notifications ───────────────────────────────────────
  useEffect(() => {
    if (!accessToken) return;
    const ws = new WebSocket(wsUrl(`/user/orders?token=${accessToken}`));
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.order_status === "FILLED" || msg.order_status === "PARTIALLY_FILLED") {
          const shortId = (msg.order_id ?? "").substring(0, 8);
          const fillQty = parseFloat(msg.fill_quantity ?? "0").toFixed(4);
          const fillPx = parseFloat(msg.fill_price ?? "0").toLocaleString();
          setOrderMsg(
            `✓ ${msg.order_status}: ${msg.side} ${fillQty} ${msg.symbol} @ ${fillPx} [${shortId}…]`
          );
          // Refresh wallet balance after fill
          api
            .get("/api/wallet/simulation")
            .then((res) => {
              const usdt = res.data.find((w: WalletBalance) => w.currency === "USDT");
              if (usdt) setWallet(usdt);
            })
            .catch(() => {});
        }
      } catch (_) {}
    };
    ws.onerror = () => {};
    return () => ws.close();
  }, [accessToken]);

  // ── Submit order ─────────────────────────────────────────────────────────────
  async function handleOrder(e: React.FormEvent) {
    e.preventDefault();
    setOrderMsg("");
    try {
      const body: any = {
        symbol: symbol.replace("USDT", "/USDT"),
        side,
        order_type: orderType,
        market_type: "SPOT",
        quantity: parseFloat(quantity),
      };
      if (orderType === "LIMIT") body.price = parseFloat(price);

      const res = await api.post("/api/orders", body);
      setOrderMsg(`Order submitted! ID: ${res.data.order_id.substring(0, 8)}…`);
      setQuantity("");
      setPrice("");
    } catch (err: any) {
      setOrderMsg(err?.response?.data?.detail || "Order failed.");
    }
  }

  const pctColor =
    parseFloat(ticker?.price_change_pct ?? "0") >= 0
      ? "var(--accent-green)"
      : "var(--accent-red)";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 260px", gap: 16 }}>
      {/* Left column: selector + chart + ticker bar */}
      <div>
        {/* Selectors */}
        <div style={{ display: "flex", gap: 12, marginBottom: 12, alignItems: "center" }}>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            style={{ width: 160 }}
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
            style={{ width: 80 }}
          >
            {INTERVALS.map((i) => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
          {ticker && (
            <div style={{ display: "flex", gap: 20, marginLeft: 16 }}>
              <span style={{ fontSize: "1.2rem", fontWeight: 700 }}>
                ${parseFloat(ticker.last_price).toLocaleString()}
              </span>
              <span style={{ color: pctColor, fontWeight: 600 }}>
                {parseFloat(ticker.price_change_pct) >= 0 ? "+" : ""}
                {ticker.price_change_pct}%
              </span>
              <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                H: ${parseFloat(ticker.high_24h).toLocaleString()}
              </span>
              <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                L: ${parseFloat(ticker.low_24h).toLocaleString()}
              </span>
              <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                Vol: {parseFloat(ticker.volume_24h).toLocaleString()}
              </span>
            </div>
          )}
        </div>

        {/* Chart */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div ref={chartContainerRef} style={{ width: "100%" }} />
        </div>

        {/* Order book */}
        <div className="card" style={{ marginTop: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: "0.9rem" }}>Order Book</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <p style={{ color: "var(--accent-red)", fontSize: "0.8rem", marginBottom: 4 }}>
                Asks (Sell)
              </p>
              <table>
                <thead><tr><th>Price</th><th>Amount</th></tr></thead>
                <tbody>
                  {(orderBook?.asks?.slice(0, 10) ?? []).map((a, i) => (
                    <tr key={i}>
                      <td style={{ color: "var(--accent-red)", fontSize: "0.8rem" }}>
                        {parseFloat(a.price).toLocaleString()}
                      </td>
                      <td style={{ fontSize: "0.8rem" }}>{parseFloat(a.quantity).toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <p style={{ color: "var(--accent-green)", fontSize: "0.8rem", marginBottom: 4 }}>
                Bids (Buy)
              </p>
              <table>
                <thead><tr><th>Price</th><th>Amount</th></tr></thead>
                <tbody>
                  {(orderBook?.bids?.slice(0, 10) ?? []).map((b, i) => (
                    <tr key={i}>
                      <td style={{ color: "var(--accent-green)", fontSize: "0.8rem" }}>
                        {parseFloat(b.price).toLocaleString()}
                      </td>
                      <td style={{ fontSize: "0.8rem" }}>{parseFloat(b.quantity).toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Right column: wallet + order entry */}
      <div>
        {/* Wallet balance */}
        <div className="card" style={{ marginBottom: 16 }}>
          <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 4 }}>
            Available Balance (Simulation)
          </p>
          <p style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0 }}>
            {wallet
              ? `$${parseFloat(wallet.available_balance).toLocaleString()} USDT`
              : "—"}
          </p>
        </div>

        {/* Order entry form */}
        <div className="card">
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <button
              style={{
                flex: 1,
                padding: "0.4rem",
                borderRadius: 6,
                border: "none",
                cursor: "pointer",
                background: side === "BUY" ? "var(--accent-green)" : "var(--bg-secondary)",
                color: "#fff",
                fontWeight: 600,
              }}
              onClick={() => setSide("BUY")}
            >
              Buy
            </button>
            <button
              style={{
                flex: 1,
                padding: "0.4rem",
                borderRadius: 6,
                border: "none",
                cursor: "pointer",
                background: side === "SELL" ? "var(--accent-red)" : "var(--bg-secondary)",
                color: "#fff",
                fontWeight: 600,
              }}
              onClick={() => setSide("SELL")}
            >
              Sell
            </button>
          </div>

          <form onSubmit={handleOrder}>
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>
                Order Type
              </label>
              <select
                value={orderType}
                onChange={(e) => setOrderType(e.target.value as "MARKET" | "LIMIT")}
              >
                <option value="MARKET">Market</option>
                <option value="LIMIT">Limit</option>
              </select>
            </div>

            {orderType === "LIMIT" && (
              <div style={{ marginBottom: 12 }}>
                <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>
                  Price (USDT)
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  required
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder={ticker?.last_price ?? "0"}
                />
              </div>
            )}

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>
                Quantity ({symbol.replace("USDT", "")})
              </label>
              <input
                type="number"
                step="any"
                min="0"
                required
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="0.00"
              />
            </div>

            <button
              type="submit"
              className={side === "BUY" ? "btn-buy" : "btn-sell"}
            >
              {side === "BUY" ? "Buy" : "Sell"} {symbol.replace("USDT", "")}
            </button>

            {orderMsg && (
              <p style={{ fontSize: "0.8rem", marginTop: 12, color: "var(--accent-blue)" }}>
                {orderMsg}
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}
