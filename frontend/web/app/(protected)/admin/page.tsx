"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface User {
  id: string;
  email: string;
  role: string;
  trading_mode: string;
  kyc_status: string;
  is_active: boolean;
  created_at: string;
}

interface TopUpForm {
  userId: string;
  amount: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [topUp, setTopUp] = useState<TopUpForm | null>(null);
  const [topUpAmount, setTopUpAmount] = useState("");
  const [msg, setMsg] = useState("");

  const PER_PAGE = 20;

  function loadUsers(p: number) {
    setLoading(true);
    api
      .get(`/api/admin/users?page=${p}&per_page=${PER_PAGE}`)
      .then((res) => {
        setUsers(res.data.users);
        setTotal(res.data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(() => { loadUsers(page); }, [page]);

  async function toggleMode(userId: string, currentMode: string) {
    const newMode = currentMode === "SIMULATION" ? "LIVE" : "SIMULATION";
    await api.put(`/api/admin/users/${userId}/mode`, { trading_mode: newMode });
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, trading_mode: newMode } : u))
    );
  }

  async function toggleStatus(userId: string, isActive: boolean) {
    await api.put(`/api/admin/users/${userId}/status`, { is_active: !isActive });
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, is_active: !isActive } : u))
    );
  }

  async function handleTopUp() {
    if (!topUp) return;
    setMsg("");
    try {
      const res = await api.post("/api/admin/wallet/topup", {
        user_id: topUp.userId,
        currency: "USDT",
        amount: parseFloat(topUpAmount),
      });
      setMsg(res.data.message);
      setTopUp(null);
      setTopUpAmount("");
    } catch (err: any) {
      setMsg(err?.response?.data?.detail || "Top-up failed.");
    }
  }

  const totalPages = Math.ceil(total / PER_PAGE);

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>User Management</h2>

      {msg && (
        <p style={{ color: "var(--accent-green)", marginBottom: 12 }}>{msg}</p>
      )}

      {/* Top-up modal */}
      {topUp && (
        <div
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
          }}
        >
          <div className="card" style={{ width: 340 }}>
            <h3 style={{ marginBottom: 12 }}>Assign Simulation Balance</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 12 }}>
              User: {users.find((u) => u.id === topUp.userId)?.email}
            </p>
            <label style={{ fontSize: "0.85rem", display: "block", marginBottom: 6 }}>
              Amount (USDT)
            </label>
            <input
              type="number"
              min="1"
              value={topUpAmount}
              onChange={(e) => setTopUpAmount(e.target.value)}
              placeholder="e.g. 10000"
              style={{ marginBottom: 16 }}
            />
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn-primary" onClick={handleTopUp}>Confirm</button>
              <button
                onClick={() => { setTopUp(null); setTopUpAmount(""); }}
                style={{
                  background: "transparent", border: "1px solid var(--border)",
                  borderRadius: 6, color: "var(--text-muted)", cursor: "pointer",
                  padding: "0.5rem 1rem",
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        {loading ? (
          <p style={{ color: "var(--text-muted)" }}>Loading…</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Mode</th>
                  <th>KYC</th>
                  <th>Status</th>
                  <th>Registered</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.email}</td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{u.role}</td>
                    <td>
                      <span
                        style={{
                          fontSize: "0.75rem",
                          padding: "2px 8px",
                          borderRadius: 4,
                          background:
                            u.trading_mode === "LIVE"
                              ? "rgba(239,68,68,0.15)"
                              : "rgba(59,130,246,0.15)",
                          color:
                            u.trading_mode === "LIVE"
                              ? "var(--accent-red)"
                              : "var(--accent-blue)",
                        }}
                      >
                        {u.trading_mode}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                      {u.kyc_status}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: "0.75rem",
                          color: u.is_active ? "var(--accent-green)" : "var(--accent-red)",
                        }}
                      >
                        {u.is_active ? "Active" : "Suspended"}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        <button
                          onClick={() => setTopUp({ userId: u.id, amount: "" })}
                          style={{
                            background: "transparent",
                            border: "1px solid var(--accent-blue)",
                            borderRadius: 4,
                            color: "var(--accent-blue)",
                            cursor: "pointer",
                            fontSize: "0.72rem",
                            padding: "2px 8px",
                          }}
                        >
                          Top Up
                        </button>
                        <button
                          onClick={() => toggleMode(u.id, u.trading_mode)}
                          style={{
                            background: "transparent",
                            border: "1px solid var(--border)",
                            borderRadius: 4,
                            color: "var(--text-muted)",
                            cursor: "pointer",
                            fontSize: "0.72rem",
                            padding: "2px 8px",
                          }}
                        >
                          {u.trading_mode === "SIMULATION" ? "→ Live" : "→ Sim"}
                        </button>
                        <button
                          onClick={() => toggleStatus(u.id, u.is_active)}
                          style={{
                            background: "transparent",
                            border: `1px solid ${u.is_active ? "var(--accent-red)" : "var(--accent-green)"}`,
                            borderRadius: 4,
                            color: u.is_active ? "var(--accent-red)" : "var(--accent-green)",
                            cursor: "pointer",
                            fontSize: "0.72rem",
                            padding: "2px 8px",
                          }}
                        >
                          {u.is_active ? "Suspend" : "Activate"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div style={{ display: "flex", gap: 8, marginTop: 16, justifyContent: "flex-end" }}>
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="btn-primary"
                  style={{ opacity: page === 1 ? 0.4 : 1 }}
                >
                  ← Prev
                </button>
                <span style={{ color: "var(--text-muted)", lineHeight: "2rem" }}>
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="btn-primary"
                  style={{ opacity: page === totalPages ? 0.4 : 1 }}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
