"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface Order {
  id: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: string;
  price: string | null;
  status: string;
  created_at: string;
}

const STATUS_COLOR: Record<string, string> = {
  FILLED: "var(--accent-green)",
  CANCELLED: "var(--text-muted)",
  REJECTED: "var(--accent-red)",
  PENDING: "var(--accent-blue)",
  OPEN: "var(--accent-blue)",
  PARTIALLY_FILLED: "#f59e0b",
};

export default function HistoryPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/orders?limit=100")
      .then((res) => setOrders(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function cancelOrder(id: string) {
    try {
      await api.delete(`/api/orders/${id}`);
      setOrders((prev) =>
        prev.map((o) => (o.id === id ? { ...o, status: "CANCELLED" } : o))
      );
    } catch (_) {}
  }

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Trade History</h2>
      <div className="card">
        {loading ? (
          <p style={{ color: "var(--text-muted)" }}>Loading…</p>
        ) : orders.length === 0 ? (
          <p style={{ color: "var(--text-muted)" }}>No orders placed yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Pair</th>
                <th>Side</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Status</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td style={{ fontWeight: 600 }}>{o.symbol}</td>
                  <td
                    style={{
                      color:
                        o.side === "BUY"
                          ? "var(--accent-green)"
                          : "var(--accent-red)",
                      fontWeight: 600,
                    }}
                  >
                    {o.side}
                  </td>
                  <td>{o.order_type}</td>
                  <td>{parseFloat(o.quantity).toFixed(4)}</td>
                  <td>{o.price ? parseFloat(o.price).toLocaleString() : "Market"}</td>
                  <td style={{ color: STATUS_COLOR[o.status] ?? "#fff" }}>{o.status}</td>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    {new Date(o.created_at).toLocaleString()}
                  </td>
                  <td>
                    {(o.status === "PENDING" || o.status === "OPEN") && (
                      <button
                        onClick={() => cancelOrder(o.id)}
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
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
