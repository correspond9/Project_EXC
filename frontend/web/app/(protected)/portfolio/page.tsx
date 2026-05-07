"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface WalletBalance {
  currency: string;
  balance: string;
  locked_balance: string;
  available_balance: string;
}

export default function PortfolioPage() {
  const [wallets, setWallets] = useState<WalletBalance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/wallet/simulation")
      .then((res) => setWallets(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Portfolio — Simulation</h2>
      <div className="card">
        {loading ? (
          <p style={{ color: "var(--text-muted)" }}>Loading…</p>
        ) : wallets.length === 0 ? (
          <p style={{ color: "var(--text-muted)" }}>
            No simulation wallet yet. An admin will assign a starting balance.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Currency</th>
                <th>Total Balance</th>
                <th>In Orders</th>
                <th>Available</th>
              </tr>
            </thead>
            <tbody>
              {wallets.map((w) => (
                <tr key={w.currency}>
                  <td style={{ fontWeight: 700 }}>{w.currency}</td>
                  <td>{parseFloat(w.balance).toLocaleString(undefined, { maximumFractionDigits: 4 })}</td>
                  <td style={{ color: "var(--text-muted)" }}>
                    {parseFloat(w.locked_balance).toLocaleString(undefined, { maximumFractionDigits: 4 })}
                  </td>
                  <td style={{ color: "var(--accent-green)", fontWeight: 600 }}>
                    {parseFloat(w.available_balance).toLocaleString(undefined, { maximumFractionDigits: 4 })}
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
