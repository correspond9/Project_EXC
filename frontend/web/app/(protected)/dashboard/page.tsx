"use client";

import { useEffect, useRef, useState, useCallback } from "react";
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

interface MarginSummary {
  total_margin_balance: string;
  available_margin: string;
  used_margin: string;
  margin_usage_pct: string;
}

interface Position {
  id: string;
  symbol: string;
  side: "LONG" | "SHORT";
  quantity: string;
  entry_price: string;
  leverage: number;
  margin: string;
  liquidation_price: string;
  unrealised_pnl: string;
  realised_pnl: string | null;
  status: string;
  created_at: string;
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

  // Tab state
  const [activeTab, setActiveTab] = useState<"SPOT" | "FUTURES" | "OPTIONS">("SPOT");

  // Spot order form
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [orderMsg, setOrderMsg] = useState("");

  // Futures order form
  const [futSide, setFutSide] = useState<"BUY" | "SELL">("BUY"); // BUY=LONG, SELL=SHORT
  const [futOrderType, setFutOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [futQuantity, setFutQuantity] = useState("");
  const [futPrice, setFutPrice] = useState("");
  const [futLeverage, setFutLeverage] = useState(10);
  const [futMsg, setFutMsg] = useState("");

  // Futures data
  const [positions, setPositions] = useState<Position[]>([]);
  const [margin, setMargin] = useState<MarginSummary | null>(null);

  // Options state
  const [optContracts, setOptContracts] = useState<OptionsContract[]>([]);
  const [optSelected, setOptSelected] = useState<OptionsContract | null>(null);
  const [optPricing, setOptPricing] = useState<OptionPricing | null>(null);
  const [optQty, setOptQty] = useState("0.01");
  const [optMsg, setOptMsg] = useState("");
  const [optPositions, setOptPositions] = useState<OptionsPosition[]>([]);

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
  const refreshWallet = useCallback(() => {
    api
      .get("/api/wallet/simulation")
      .then((res) => {
        const usdt = res.data.find((w: WalletBalance) => w.currency === "USDT");
        if (usdt) setWallet(usdt);
      })
      .catch(() => {});
  }, []);

  useEffect(() => { refreshWallet(); }, [refreshWallet]);

  // ── Fetch margin account + positions ────────────────────────────────────────
  const refreshMargin = useCallback(() => {
    api.get("/api/positions/margin").then((res) => setMargin(res.data)).catch(() => {});
    api.get("/api/positions?status=OPEN").then((res) => setPositions(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (activeTab === "FUTURES") refreshMargin();
    if (activeTab === "OPTIONS") {
      api.get(`/api/options/contracts?underlying=${symbol}`)
        .then((res) => setOptContracts(res.data))
        .catch(() => {});
      api.get("/api/options/positions?status=OPEN")
        .then((res) => setOptPositions(res.data))
        .catch(() => {});
    }
  }, [activeTab, refreshMargin, symbol]);

  // ── WebSocket: live fills + position P&L updates ─────────────────────────────
  useEffect(() => {
    if (!accessToken) return;
    const ws = new WebSocket(wsUrl(`/user/orders?token=${accessToken}`));
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);

        if (msg.type === "pnl_update") {
          setPositions((prev) =>
            prev.map((p) =>
              p.id === msg.position_id
                ? { ...p, unrealised_pnl: msg.unrealised_pnl }
                : p
            )
          );
          return;
        }

        if (msg.type === "position_opened") {
          refreshMargin();
          setFutMsg(`Position opened: ${msg.side} ${msg.quantity} ${msg.symbol} @ ${parseFloat(msg.entry_price).toLocaleString()} | Lev ${msg.leverage}x`);
          return;
        }

        if (msg.type === "position_closed") {
          setPositions((prev) => prev.filter((p) => p.id !== msg.position_id));
          refreshMargin();
          const pnlNum = parseFloat(msg.realised_pnl);
          setFutMsg(`Position closed: P&L ${pnlNum >= 0 ? "+" : ""}${pnlNum.toFixed(2)} USDT`);
          return;
        }

        if (msg.type === "liquidation") {
          setPositions((prev) => prev.filter((p) => p.id !== msg.position_id));
          refreshMargin();
          setFutMsg(`⚠ LIQUIDATED: ${msg.side} ${msg.symbol}`);
          return;
        }

        if (msg.order_status === "FILLED" || msg.order_status === "PARTIALLY_FILLED") {
          const shortId = (msg.order_id ?? "").substring(0, 8);
          const fillQty = parseFloat(msg.fill_quantity ?? "0").toFixed(4);
          const fillPx = parseFloat(msg.fill_price ?? "0").toLocaleString();
          setOrderMsg(
            `✓ ${msg.order_status}: ${msg.side} ${fillQty} ${msg.symbol} @ ${fillPx} [${shortId}…]`
          );
          refreshWallet();
        }
      } catch (_) {}
    };
    ws.onerror = () => {};
    return () => ws.close();
  }, [accessToken, refreshWallet, refreshMargin]);

  // ── Submit SPOT order ────────────────────────────────────────────────────────
  async function handleSpotOrder(e: React.FormEvent) {
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

  // ── Submit FUTURES order ─────────────────────────────────────────────────────
  async function handleFuturesOrder(e: React.FormEvent) {
    e.preventDefault();
    setFutMsg("");
    try {
      const body: any = {
        symbol: symbol.replace("USDT", "/USDT"),
        side: futSide,
        order_type: futOrderType,
        market_type: "FUTURES",
        quantity: parseFloat(futQuantity),
        leverage: futLeverage,
        reduce_only: false,
      };
      if (futOrderType === "LIMIT") body.price = parseFloat(futPrice);
      const res = await api.post("/api/orders", body);
      setFutMsg(`Futures order submitted! ID: ${res.data.order_id.substring(0, 8)}…`);
      setFutQuantity("");
      setFutPrice("");
    } catch (err: any) {
      setFutMsg(err?.response?.data?.detail || "Order failed.");
    }
  }

  // ── Close position (reduce_only) ─────────────────────────────────────────────
  async function handleClosePosition(pos: Position) {
    setFutMsg("");
    try {
      const body: any = {
        symbol: pos.symbol,
        side: pos.side === "LONG" ? "SELL" : "BUY",
        order_type: "MARKET",
        market_type: "FUTURES",
        quantity: parseFloat(pos.quantity),
        leverage: pos.leverage,
        reduce_only: true,
      };
      await api.post("/api/orders", body);
      setFutMsg(`Closing position ${pos.symbol} ${pos.side}…`);
    } catch (err: any) {
      setFutMsg(err?.response?.data?.detail || "Close failed.");
    }
  }

  // ── Options: fetch pricing for a contract ───────────────────────────────────
  async function handleGetOptPrice(contract: OptionsContract) {
    setOptSelected(contract);
    setOptPricing(null);
    try {
      const res = await api.get(`/api/options/price?contract_id=${contract.id}`);
      setOptPricing(res.data);
    } catch {
      setOptPricing(null);
    }
  }

  // ── Options: buy an option ──────────────────────────────────────────────────
  async function handleBuyOption(e: React.FormEvent) {
    e.preventDefault();
    if (!optSelected) return;
    setOptMsg("");
    try {
      const res = await api.post("/api/options/buy", {
        contract_id: optSelected.id,
        quantity: parseFloat(optQty),
      });
      setOptMsg(
        `Option purchased! Cost: ${parseFloat(res.data.total_cost).toFixed(4)} USDT`
      );
      refreshWallet();
      api.get("/api/options/positions?status=OPEN")
        .then((r) => setOptPositions(r.data))
        .catch(() => {});
    } catch (err: any) {
      setOptMsg(err?.response?.data?.detail || "Purchase failed.");
    }
  }

  // ── Estimated margin & liquidation price ─────────────────────────────────────
  const lastPrice = parseFloat(ticker?.last_price ?? "0");
  const futQtyNum = parseFloat(futQuantity || "0");
  const estMargin = futQtyNum > 0 && lastPrice > 0
    ? (futQtyNum * lastPrice) / futLeverage
    : 0;
  const estLiqPrice = futQtyNum > 0 && lastPrice > 0
    ? futSide === "BUY"
      ? lastPrice * (1 - 1 / futLeverage + 0.005)
      : lastPrice * (1 + 1 / futLeverage - 0.005)
    : 0;

  const pctColor =
    parseFloat(ticker?.price_change_pct ?? "0") >= 0
      ? "var(--accent-green)"
      : "var(--accent-red)";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 16 }}>
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

        {/* Open Futures Positions Table (only shown when FUTURES tab active) */}
        {activeTab === "FUTURES" && (
          <div className="card" style={{ marginTop: 16 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: "0.9rem" }}>Open Positions</h3>
            {positions.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>No open positions.</p>
            ) : (
              <table style={{ width: "100%", fontSize: "0.78rem" }}>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Size</th>
                    <th>Entry</th>
                    <th>Mark</th>
                    <th>Lev</th>
                    <th>Liq Price</th>
                    <th>P&L</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => {
                    const pnl = parseFloat(pos.unrealised_pnl);
                    const posSymbol = pos.symbol.replace("/", "");
                    const markPx = posSymbol === symbol ? lastPrice : null;
                    return (
                      <tr key={pos.id}>
                        <td>{pos.symbol}</td>
                        <td style={{ color: pos.side === "LONG" ? "var(--accent-green)" : "var(--accent-red)", fontWeight: 600 }}>
                          {pos.side}
                        </td>
                        <td>{parseFloat(pos.quantity).toFixed(4)}</td>
                        <td>{parseFloat(pos.entry_price).toLocaleString()}</td>
                        <td>{markPx !== null ? markPx.toLocaleString() : "—"}</td>
                        <td>{pos.leverage}x</td>
                        <td style={{ color: "var(--accent-red)" }}>
                          {parseFloat(pos.liquidation_price).toLocaleString()}
                        </td>
                        <td style={{ color: pnl >= 0 ? "var(--accent-green)" : "var(--accent-red)", fontWeight: 600 }}>
                          {pnl >= 0 ? "+" : ""}{pnl.toFixed(2)} USDT
                        </td>
                        <td>
                          <button
                            style={{ fontSize: "0.72rem", padding: "2px 8px", background: "var(--accent-red)", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}
                            onClick={() => handleClosePosition(pos)}
                          >
                            Close
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* Right column: tab switcher + wallet/margin + order entry */}
      <div>
        {/* Tab Switcher */}
        <div style={{ display: "flex", gap: 0, marginBottom: 16, borderRadius: 8, overflow: "hidden", border: "1px solid var(--border-color)" }}>
          {(["SPOT", "FUTURES", "OPTIONS"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                flex: 1,
                padding: "0.45rem",
                border: "none",
                cursor: "pointer",
                background: activeTab === tab ? "var(--accent-blue)" : "var(--bg-secondary)",
                color: "#fff",
                fontWeight: 600,
                fontSize: "0.8rem",
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* ── SPOT PANEL ────────────────────────────────────────────────────── */}
        {activeTab === "SPOT" && (
          <>
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

            {/* Spot order entry form */}
            <div className="card">
              <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                <button
                  style={{ flex: 1, padding: "0.4rem", borderRadius: 6, border: "none", cursor: "pointer", background: side === "BUY" ? "var(--accent-green)" : "var(--bg-secondary)", color: "#fff", fontWeight: 600 }}
                  onClick={() => setSide("BUY")}
                >Buy</button>
                <button
                  style={{ flex: 1, padding: "0.4rem", borderRadius: 6, border: "none", cursor: "pointer", background: side === "SELL" ? "var(--accent-red)" : "var(--bg-secondary)", color: "#fff", fontWeight: 600 }}
                  onClick={() => setSide("SELL")}
                >Sell</button>
              </div>

              <form onSubmit={handleSpotOrder}>
                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Order Type</label>
                  <select value={orderType} onChange={(e) => setOrderType(e.target.value as "MARKET" | "LIMIT")}>
                    <option value="MARKET">Market</option>
                    <option value="LIMIT">Limit</option>
                  </select>
                </div>

                {orderType === "LIMIT" && (
                  <div style={{ marginBottom: 12 }}>
                    <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Price (USDT)</label>
                    <input type="number" step="any" min="0" required value={price} onChange={(e) => setPrice(e.target.value)} placeholder={ticker?.last_price ?? "0"} />
                  </div>
                )}

                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>
                    Quantity ({symbol.replace("USDT", "")})
                  </label>
                  <input type="number" step="any" min="0" required value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="0.00" />
                </div>

                <button type="submit" className={side === "BUY" ? "btn-buy" : "btn-sell"}>
                  {side === "BUY" ? "Buy" : "Sell"} {symbol.replace("USDT", "")}
                </button>

                {orderMsg && (
                  <p style={{ fontSize: "0.8rem", marginTop: 12, color: "var(--accent-blue)" }}>{orderMsg}</p>
                )}
              </form>
            </div>
          </>
        )}

        {/* ── FUTURES PANEL ─────────────────────────────────────────────────── */}
        {activeTab === "FUTURES" && (
          <>
            {/* Margin account summary */}
            <div className="card" style={{ marginBottom: 16 }}>
              <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 6 }}>
                Margin Account (Simulation)
              </p>
              {margin ? (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: "0.8rem" }}>
                  <span style={{ color: "var(--text-muted)" }}>Total</span>
                  <span style={{ fontWeight: 600, textAlign: "right" }}>
                    ${parseFloat(margin.total_margin_balance).toLocaleString()} USDT
                  </span>
                  <span style={{ color: "var(--text-muted)" }}>Available</span>
                  <span style={{ fontWeight: 600, color: "var(--accent-green)", textAlign: "right" }}>
                    ${parseFloat(margin.available_margin).toLocaleString()} USDT
                  </span>
                  <span style={{ color: "var(--text-muted)" }}>Used</span>
                  <span style={{ fontWeight: 600, color: "var(--accent-red)", textAlign: "right" }}>
                    ${parseFloat(margin.used_margin).toLocaleString()} USDT
                  </span>
                  <span style={{ color: "var(--text-muted)" }}>Usage</span>
                  <span style={{ textAlign: "right" }}>{margin.margin_usage_pct}%</span>
                </div>
              ) : (
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  No margin account. Ask admin to fund your account.
                </p>
              )}
            </div>

            {/* Futures order entry form */}
            <div className="card">
              {/* Long / Short buttons */}
              <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                <button
                  style={{ flex: 1, padding: "0.4rem", borderRadius: 6, border: "none", cursor: "pointer", background: futSide === "BUY" ? "var(--accent-green)" : "var(--bg-secondary)", color: "#fff", fontWeight: 600 }}
                  onClick={() => setFutSide("BUY")}
                >Long</button>
                <button
                  style={{ flex: 1, padding: "0.4rem", borderRadius: 6, border: "none", cursor: "pointer", background: futSide === "SELL" ? "var(--accent-red)" : "var(--bg-secondary)", color: "#fff", fontWeight: 600 }}
                  onClick={() => setFutSide("SELL")}
                >Short</button>
              </div>

              <form onSubmit={handleFuturesOrder}>
                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Order Type</label>
                  <select value={futOrderType} onChange={(e) => setFutOrderType(e.target.value as "MARKET" | "LIMIT")}>
                    <option value="MARKET">Market</option>
                    <option value="LIMIT">Limit</option>
                  </select>
                </div>

                {futOrderType === "LIMIT" && (
                  <div style={{ marginBottom: 12 }}>
                    <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Price (USDT)</label>
                    <input type="number" step="any" min="0" required value={futPrice} onChange={(e) => setFutPrice(e.target.value)} placeholder={ticker?.last_price ?? "0"} />
                  </div>
                )}

                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>
                    Quantity ({symbol.replace("USDT", "")})
                  </label>
                  <input type="number" step="any" min="0" required value={futQuantity} onChange={(e) => setFutQuantity(e.target.value)} placeholder="0.00" />
                </div>

                {/* Leverage slider */}
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: "0.8rem", display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span>Leverage</span>
                    <span style={{ fontWeight: 700, color: "var(--accent-blue)" }}>{futLeverage}x</span>
                  </label>
                  <input
                    type="range" min={1} max={20} step={1}
                    value={futLeverage}
                    onChange={(e) => setFutLeverage(parseInt(e.target.value))}
                    style={{ width: "100%" }}
                  />
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.7rem", color: "var(--text-muted)" }}>
                    <span>1x</span><span>5x</span><span>10x</span><span>20x</span>
                  </div>
                </div>

                {/* Estimates */}
                {estMargin > 0 && (
                  <div style={{ background: "var(--bg-secondary)", borderRadius: 6, padding: "8px 10px", marginBottom: 14, fontSize: "0.78rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                      <span style={{ color: "var(--text-muted)" }}>Est. Margin</span>
                      <span>${estMargin.toFixed(2)} USDT</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-muted)" }}>Est. Liq. Price</span>
                      <span style={{ color: "var(--accent-red)" }}>${estLiqPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  style={{
                    width: "100%",
                    padding: "0.55rem",
                    borderRadius: 6,
                    border: "none",
                    cursor: "pointer",
                    background: futSide === "BUY" ? "var(--accent-green)" : "var(--accent-red)",
                    color: "#fff",
                    fontWeight: 700,
                    fontSize: "0.9rem",
                  }}
                >
                  {futSide === "BUY" ? "Open Long" : "Open Short"} {futLeverage}x
                </button>

                {futMsg && (
                  <p style={{ fontSize: "0.8rem", marginTop: 12, color: "var(--accent-blue)" }}>{futMsg}</p>
                )}
              </form>
            </div>
          </>
        )}

        {/* ── OPTIONS PANEL ─────────────────────────────────────────────────── */}
        {activeTab === "OPTIONS" && (
          <>
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

            {/* Contracts list */}
            <div className="card" style={{ marginBottom: 16 }}>
              <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: 8 }}>
                Active Contracts — {symbol}
              </p>
              {optContracts.length === 0 ? (
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  No active contracts for {symbol}.
                </p>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
                  <thead>
                    <tr style={{ color: "var(--text-muted)" }}>
                      <th style={{ textAlign: "left", paddingBottom: 4 }}>Type</th>
                      <th style={{ textAlign: "right", paddingBottom: 4 }}>Strike</th>
                      <th style={{ textAlign: "right", paddingBottom: 4 }}>Expiry</th>
                      <th style={{ textAlign: "right", paddingBottom: 4 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {optContracts.map((c) => (
                      <tr
                        key={c.id}
                        style={{
                          borderTop: "1px solid var(--border-color)",
                          background: optSelected?.id === c.id ? "var(--bg-secondary)" : "transparent",
                        }}
                      >
                        <td style={{ padding: "4px 0", color: c.option_type === "CALL" ? "var(--accent-green)" : "var(--accent-red)", fontWeight: 600 }}>
                          {c.option_type}
                        </td>
                        <td style={{ textAlign: "right" }}>
                          ${parseFloat(c.strike_price).toLocaleString()}
                        </td>
                        <td style={{ textAlign: "right" }}>{c.expiry_date}</td>
                        <td style={{ textAlign: "right" }}>
                          <button
                            onClick={() => handleGetOptPrice(c)}
                            style={{ fontSize: "0.7rem", padding: "2px 8px", borderRadius: 4, border: "none", cursor: "pointer", background: "var(--accent-blue)", color: "#fff" }}
                          >
                            Price
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Pricing + buy form */}
            {optSelected && (
              <div className="card" style={{ marginBottom: 16 }}>
                <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: 8 }}>
                  {optSelected.option_type} — Strike ${parseFloat(optSelected.strike_price).toLocaleString()} — Exp {optSelected.expiry_date}
                </p>
                {optPricing ? (
                  <>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: "0.78rem", marginBottom: 12 }}>
                      <span style={{ color: "var(--text-muted)" }}>Premium</span>
                      <span style={{ fontWeight: 700, textAlign: "right" }}>${parseFloat(String(optPricing.premium_per_unit)).toFixed(4)} USDT</span>
                      <span style={{ color: "var(--text-muted)" }}>Delta</span>
                      <span style={{ textAlign: "right" }}>{Number(optPricing.delta).toFixed(4)}</span>
                      <span style={{ color: "var(--text-muted)" }}>Gamma</span>
                      <span style={{ textAlign: "right" }}>{Number(optPricing.gamma).toFixed(6)}</span>
                      <span style={{ color: "var(--text-muted)" }}>Theta/day</span>
                      <span style={{ textAlign: "right" }}>{Number(optPricing.theta_per_day).toFixed(4)}</span>
                    </div>
                    <form onSubmit={handleBuyOption}>
                      <div style={{ marginBottom: 12 }}>
                        <label style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Quantity (contracts)</label>
                        <input
                          type="number" step="0.001" min="0.001"
                          value={optQty}
                          onChange={(e) => setOptQty(e.target.value)}
                          required
                        />
                      </div>
                      <div style={{ background: "var(--bg-secondary)", borderRadius: 6, padding: "6px 10px", marginBottom: 12, fontSize: "0.78rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-muted)" }}>Total Cost</span>
                          <span style={{ fontWeight: 600 }}>
                            ${(parseFloat(String(optPricing.premium_per_unit)) * parseFloat(optQty || "0")).toFixed(4)} USDT
                          </span>
                        </div>
                      </div>
                      <button
                        type="submit"
                        style={{ width: "100%", padding: "0.5rem", borderRadius: 6, border: "none", cursor: "pointer", background: optSelected.option_type === "CALL" ? "var(--accent-green)" : "var(--accent-red)", color: "#fff", fontWeight: 700 }}
                      >
                        Buy {optSelected.option_type}
                      </button>
                      {optMsg && (
                        <p style={{ fontSize: "0.8rem", marginTop: 10, color: "var(--accent-blue)" }}>{optMsg}</p>
                      )}
                    </form>
                  </>
                ) : (
                  <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Loading price…</p>
                )}
              </div>
            )}

            {/* Open options positions */}
            {optPositions.length > 0 && (
              <div className="card">
                <p style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: 8 }}>Open Options</p>
                {optPositions.map((p) => (
                  <div key={p.id} style={{ borderTop: "1px solid var(--border-color)", padding: "6px 0", fontSize: "0.78rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: p.option_type === "CALL" ? "var(--accent-green)" : "var(--accent-red)", fontWeight: 600 }}>
                        {p.option_type}
                      </span>
                      <span>Qty {p.quantity}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-muted)" }}>
                      <span>Strike ${parseFloat(p.strike_price).toLocaleString()}</span>
                      <span>Exp {p.expiry_date}</span>
                    </div>
                    <div style={{ color: "var(--text-muted)" }}>
                      Premium paid: ${parseFloat(p.premium_paid).toFixed(4)} USDT
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Options-specific interfaces ───────────────────────────────────────────────

interface OptionsContract {
  id: string;
  underlying_symbol: string;
  option_type: "CALL" | "PUT";
  strike_price: string;
  expiry_date: string;
  implied_volatility: string;
}

interface OptionPricing {
  contract_id: string;
  underlying_price: string;
  strike_price: string;
  expiry_date: string;
  option_type: "CALL" | "PUT";
  premium_per_unit: number;
  delta: number;
  gamma: number;
  theta_per_day: number;
}

interface OptionsPosition {
  id: string;
  underlying_symbol: string;
  option_type: "CALL" | "PUT";
  strike_price: string;
  expiry_date: string;
  quantity: string;
  premium_paid: string;
  status: string;
  payout: string | null;
  settlement_price: string | null;
  settled_at: string | null;
  created_at: string | null;
}
