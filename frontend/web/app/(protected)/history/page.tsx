"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface Fill {
  fill_id: string;
  fill_price: string;
  fill_quantity: string;
  fee: string;
  fee_currency: string;
  filled_at: string | null;
}

interface Order {
  order_id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: string;
  price: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  fills: Fill[];
  // legacy field from /api/orders list (cancel-compatible)
  id?: string;
}

const STATUS_COLOR: Record<string, string> = {
  FILLED: "var(--accent-green)",
  CANCELLED: "var(--text-muted)",
  REJECTED: "var(--accent-red)",
  PENDING: "var(--accent-blue)",
  OPEN: "var(--accent-blue)",
  PARTIALLY_FILLED: "#f59e0b",
};

const fmt2 = (v: string | number) =>
  parseFloat(String(v)).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function HistoryPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [openOrders, setOpenOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    Promise.all([
      api.get("/api/orders/history?limit=100"),
      api.get("/api/orders?limit=100"),
    ])
      .then(([histRes, activeRes]) => {
        setOrders(histRes.data);
        setOpenOrders(
          activeRes.data.filter(
            (o: { status: string }) => o.status === "PENDING" || o.status === "OPEN"
          )
        );
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function cancelOrder(id: string) {
    try {
      await api.delete(`/api/orders/${id}`);
      setOpenOrders((prev) =>
        prev.map((o) => ((o.id ?? o.order_id) === id ? { ...o, status: "CANCELLED" } : o))
      );
    } catch (_) {}
  }

  function toggleExpand(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <h2 style={{ margin: 0, fontSize: "1.4rem" }}>Trade History</h2>

      {/* ── Open / Pending orders ── */}
      {openOrders.length > 0 && (
        <div className="card">
          <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Open Orders
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ color: "var(--text-muted)" }}>
                  {["Pair", "Side", "Type", "Qty", "Price", "Status", "Date", ""].map((h) => (
                    <th
                      key={h}
                      style={{ padding: "0.4rem 0.75rem", fontWeight: 500, borderBottom: "1px solid var(--border)" }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {openOrders.map((o) => {
                  const oid = o.id ?? o.order_id;
                  return (
                    <tr key={oid} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "0.5rem 0.75rem", fontWeight: 600 }}>{o.symbol}</td>
                      <td
                        style={{
                          padding: "0.5rem 0.75rem",
                          color: o.side === "BUY" ? "var(--accent-green)" : "var(--accent-red)",
                          fontWeight: 600,
                        }}
                      >
                        {o.side}
                      </td>
                      <td style={{ padding: "0.5rem 0.75rem" }}>{o.order_type}</td>
                      <td style={{ padding: "0.5rem 0.75rem" }}>{parseFloat(o.quantity).toFixed(4)}</td>
                      <td style={{ padding: "0.5rem 0.75rem" }}>
                        {o.price ? parseFloat(o.price).toLocaleString() : "Market"}
                      </td>
                      <td style={{ padding: "0.5rem 0.75rem", color: STATUS_COLOR[o.status] ?? "#fff" }}>
                        {o.status}
                      </td>
                      <td style={{ padding: "0.5rem 0.75rem", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                        {new Date(o.created_at).toLocaleString()}
                      </td>
                      <td style={{ padding: "0.5rem 0.75rem" }}>
                        <button
                          onClick={() => cancelOrder(oid)}
                          style={{
                            background: "transparent",
                            border: "1px solid var(--accent-red)",
                            borderRadius: 4,
                            color: "var(--accent-red)",
                            cursor: "pointer",
                            fontSize: "0.75rem",
                            padding: "2px 8px",
                          }}
                        >
                          Cancel
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Filled order history ── */}
      <div className="card">
        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
          Filled Orders
        </div>
        {loading ? (
          <p style={{ color: "var(--text-muted)" }}>Loading…</p>
        ) : orders.length === 0 ? (
          <p style={{ color: "var(--text-muted)", margin: 0 }}>No filled orders yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ color: "var(--text-muted)" }}>
                  {["Pair", "Side", "Type", "Qty", "Price", "Status", "Date", "Fills"].map((h) => (
                    <th
                      key={h}
                      style={{ padding: "0.4rem 0.75rem", fontWeight: 500, borderBottom: "1px solid var(--border)" }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => {
                  const isExpanded = expanded.has(o.order_id);
                  return (
                    <>
                      <tr key={o.order_id} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "0.5rem 0.75rem", fontWeight: 600 }}>{o.symbol}</td>
                        <td
                          style={{
                            padding: "0.5rem 0.75rem",
                            color: o.side === "BUY" ? "var(--accent-green)" : "var(--accent-red)",
                            fontWeight: 600,
                          }}
                        >
                          {o.side}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem" }}>{o.order_type}</td>
                        <td style={{ padding: "0.5rem 0.75rem" }}>{parseFloat(o.quantity).toFixed(4)}</td>
                        <td style={{ padding: "0.5rem 0.75rem" }}>
                          {o.price ? parseFloat(o.price).toLocaleString() : "Market"}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem", color: STATUS_COLOR[o.status] ?? "#fff" }}>
                          {o.status}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                          {new Date(o.updated_at ?? o.created_at).toLocaleString()}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem" }}>
                          {o.fills.length > 0 && (
                            <button
                              onClick={() => toggleExpand(o.order_id)}
                              style={{
                                background: "transparent",
                                border: "1px solid var(--accent-blue)",
                                borderRadius: 4,
                                color: "var(--accent-blue)",
                                cursor: "pointer",
                                fontSize: "0.75rem",
                                padding: "2px 8px",
                              }}
                            >
                              {isExpanded ? "▲ Hide" : `▼ ${o.fills.length}`}
                            </button>
                          )}
                        </td>
                      </tr>
                      {isExpanded &&
                        o.fills.map((f) => (
                          <tr
                            key={f.fill_id}
                            style={{
                              background: "rgba(59,130,246,0.04)",
                              fontSize: "0.8rem",
                              color: "var(--text-muted)",
                            }}
                          >
                            <td colSpan={2} style={{ padding: "0.3rem 1.5rem" }}>
                              Fill
                            </td>
                            <td style={{ padding: "0.3rem 0.75rem" }}>
                              Price: ${fmt2(f.fill_price)}
                            </td>
                            <td style={{ padding: "0.3rem 0.75rem" }}>
                              Qty: {parseFloat(f.fill_quantity).toFixed(6)}
                            </td>
                            <td colSpan={2} style={{ padding: "0.3rem 0.75rem" }}>
                              Fee: {fmt2(f.fee)} {f.fee_currency}
                            </td>
                            <td colSpan={2} style={{ padding: "0.3rem 0.75rem" }}>
                              {f.filled_at ? new Date(f.filled_at).toLocaleString() : "—"}
                            </td>
                          </tr>
                        ))}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
