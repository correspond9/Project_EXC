"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, AreaSeries } from "lightweight-charts";
import api from "@/lib/api";
import { wsUrl } from "@/lib/ws";
import { useAuthStore } from "@/store/authStore";

// ── Types ──────────────────────────────────────────────────────────────────

interface Holding {
  asset: string;
  quantity: string;
  average_entry_price: string;
  current_price: string;
  value_usdt: string;
  unrealised_pnl: string;
  total_realised_pnl: string;
}

interface Summary {
  total_portfolio_value: string;
  holdings_value: string;
  usdt_balance: string;
  total_realised_pnl: string;
  total_unrealised_pnl: string;
  todays_pnl_delta: string;
}

interface PnlPoint {
  date: string;
  total_portfolio_value: string;
  total_realised_pnl: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const fmt = (v: string | number) =>
  parseFloat(String(v)).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const pnlColour = (v: string) =>
  parseFloat(v) >= 0 ? "var(--accent-green)" : "var(--accent-red)";

const pnlSign = (v: string) =>
  parseFloat(v) >= 0 ? "+" : "";

// ── Component ──────────────────────────────────────────────────────────────

export default function PortfolioPage() {
  const { accessToken } = useAuthStore();

  const [summary, setSummary] = useState<Summary | null>(null);
  const [pnlHistory, setPnlHistory] = useState<PnlPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [liveSummary, setLiveSummary] = useState<Summary | null>(null);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);

  // ── Initial REST fetch ──────────────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      api.get("/api/portfolio/summary"),
      api.get("/api/portfolio/pnl/history?days=30"),
    ])
      .then(([sumRes, histRes]) => {
        setSummary(sumRes.data);
        setPnlHistory(histRes.data);
      })
      .catch(() => setError("Failed to load portfolio data"))
      .finally(() => setLoading(false));
  }, []);

  // ── P&L history chart ──────────────────────────────────────────────────
  useEffect(() => {
    if (!chartContainerRef.current || pnlHistory.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#1c2030" },
        textColor: "#64748b",
      },
      grid: {
        vertLines: { color: "#2a3045" },
        horzLines: { color: "#2a3045" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 180,
    });

    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: "#3b82f6",
      topColor: "rgba(59,130,246,0.25)",
      bottomColor: "rgba(59,130,246,0.02)",
    });

    areaSeries.setData(
      pnlHistory.map((p) => ({
        time: p.date,
        value: parseFloat(p.total_portfolio_value),
      }))
    );

    chart.timeScale().fitContent();
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    });
    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [pnlHistory]);

  // ── Live portfolio WebSocket ────────────────────────────────────────────
  useEffect(() => {
    if (!accessToken) return;

    const url = wsUrl(`/user/portfolio?token=${accessToken}`);
    const ws = new WebSocket(url);

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "portfolio_update") {
          setHoldings(msg.holdings ?? []);
          if (msg.summary) {
            setLiveSummary((prev) => ({
              ...((prev ?? summary) as Summary),
              ...msg.summary,
            }));
          }
        }
      } catch (_) {}
    };

    ws.onerror = () => {};
    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const displaySummary = liveSummary ?? summary;

  // ── Render ─────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ padding: "2rem", color: "var(--text-muted)" }}>Loading portfolio…</div>
    );
  }
  if (error) {
    return (
      <div style={{ padding: "2rem", color: "var(--accent-red)" }}>{error}</div>
    );
  }

  return (
    <div style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <h2 style={{ margin: 0, fontSize: "1.4rem" }}>Portfolio</h2>

      {/* ── Summary cards ── */}
      {displaySummary && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "1rem",
          }}
        >
          {[
            { label: "Total Value", value: `$${fmt(displaySummary.total_portfolio_value)}` },
            { label: "USDT Balance", value: `$${fmt(displaySummary.usdt_balance)}` },
            {
              label: "Unrealised P&L",
              value: `${pnlSign(displaySummary.total_unrealised_pnl)}$${fmt(displaySummary.total_unrealised_pnl)}`,
              color: pnlColour(displaySummary.total_unrealised_pnl),
            },
            {
              label: "Realised P&L",
              value: `${pnlSign(displaySummary.total_realised_pnl)}$${fmt(displaySummary.total_realised_pnl)}`,
              color: pnlColour(displaySummary.total_realised_pnl),
            },
            {
              label: "Today's P&L",
              value: `${pnlSign(displaySummary.todays_pnl_delta)}$${fmt(displaySummary.todays_pnl_delta)}`,
              color: pnlColour(displaySummary.todays_pnl_delta),
            },
          ].map(({ label, value, color }) => (
            <div key={label} className="card">
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
                {label}
              </div>
              <div style={{ fontSize: "1.25rem", fontWeight: 700, color: color ?? "var(--text-primary)" }}>
                {value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── P&L history chart ── */}
      {pnlHistory.length > 0 && (
        <div className="card">
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Portfolio Value — Last 30 Days
          </div>
          <div ref={chartContainerRef} />
        </div>
      )}

      {/* ── Holdings table ── */}
      <div className="card">
        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
          Holdings
        </div>
        {holdings.length === 0 ? (
          <p style={{ color: "var(--text-muted)", margin: 0 }}>No open positions</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ color: "var(--text-muted)", textAlign: "right" }}>
                  {["Asset", "Qty", "Avg Entry", "Current", "Value (USDT)", "Unrealised P&L", "Realised P&L"].map(
                    (h) => (
                      <th
                        key={h}
                        style={{
                          padding: "0.4rem 0.75rem",
                          fontWeight: 500,
                          textAlign: h === "Asset" ? "left" : "right",
                          borderBottom: "1px solid var(--border)",
                        }}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {holdings.map((h) => (
                  <tr key={h.asset} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "0.5rem 0.75rem", fontWeight: 600 }}>{h.asset}</td>
                    <td style={{ padding: "0.5rem 0.75rem", textAlign: "right" }}>
                      {parseFloat(h.quantity).toFixed(6)}
                    </td>
                    <td style={{ padding: "0.5rem 0.75rem", textAlign: "right" }}>
                      ${fmt(h.average_entry_price)}
                    </td>
                    <td style={{ padding: "0.5rem 0.75rem", textAlign: "right" }}>
                      ${fmt(h.current_price)}
                    </td>
                    <td style={{ padding: "0.5rem 0.75rem", textAlign: "right" }}>
                      ${fmt(h.value_usdt)}
                    </td>
                    <td
                      style={{
                        padding: "0.5rem 0.75rem",
                        textAlign: "right",
                        color: pnlColour(h.unrealised_pnl),
                        fontWeight: 600,
                      }}
                    >
                      {pnlSign(h.unrealised_pnl)}${fmt(h.unrealised_pnl)}
                    </td>
                    <td
                      style={{
                        padding: "0.5rem 0.75rem",
                        textAlign: "right",
                        color: pnlColour(h.total_realised_pnl),
                      }}
                    >
                      {pnlSign(h.total_realised_pnl)}${fmt(h.total_realised_pnl)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
