"use client";

import { useEffect, useMemo, useState } from "react";
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

  const portfolioTrend = useMemo(() => {
    const values = pnlHistory
      .map((p) => ({ date: p.date, value: parseFloat(p.total_portfolio_value) }))
      .filter((p) => Number.isFinite(p.value));

    if (values.length === 0) {
      return null;
    }

    const width = 900;
    const height = 180;
    const padding = 16;

    const min = Math.min(...values.map((v) => v.value));
    const max = Math.max(...values.map((v) => v.value));
    const range = Math.max(1, max - min);

    const xAt = (index: number) => {
      if (values.length === 1) return width / 2;
      return padding + (index / (values.length - 1)) * (width - padding * 2);
    };

    const yAt = (value: number) => {
      return padding + ((max - value) / range) * (height - padding * 2);
    };

    const linePath = values
      .map((point, index) => `${index === 0 ? "M" : "L"} ${xAt(index)} ${yAt(point.value)}`)
      .join(" ");

    const areaPath = `${linePath} L ${xAt(values.length - 1)} ${height - padding} L ${xAt(0)} ${height - padding} Z`;

    return {
      width,
      height,
      linePath,
      areaPath,
      min,
      max,
      startDate: values[0].date,
      endDate: values[values.length - 1].date,
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
      {portfolioTrend && (
        <div className="card">
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Portfolio Value — Last 30 Days
          </div>
          <div style={{ width: "100%", height: 180 }}>
            <svg viewBox={`0 0 ${portfolioTrend.width} ${portfolioTrend.height}`} width="100%" height="100%" preserveAspectRatio="none" role="img" aria-label="Portfolio value trend chart">
              <defs>
                <linearGradient id="portfolioAreaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.03" />
                </linearGradient>
              </defs>
              <path d={portfolioTrend.areaPath} fill="url(#portfolioAreaGradient)" />
              <path d={portfolioTrend.linePath} fill="none" stroke="#3b82f6" strokeWidth="2" />
            </svg>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
            <span>{portfolioTrend.startDate}</span>
            <span>Low: ${fmt(portfolioTrend.min)} | High: ${fmt(portfolioTrend.max)}</span>
            <span>{portfolioTrend.endDate}</span>
          </div>
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
