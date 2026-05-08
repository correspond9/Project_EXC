"use client";

import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

interface User {
  id: string;
  email: string;
  role: string;
  trading_mode: string;
  kyc_status: string;
  is_active: boolean;
  created_at: string;
}

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  email: string;
  total_trades: number;
  realised_pnl: number;
  current_balance: number;
  win_rate_pct: number;
  best_trade: number;
  worst_trade: number;
}

interface TradingPair {
  id: string;
  symbol: string;
  is_active: boolean;
  max_leverage: number;
}

interface FeeConfig {
  maker_fee: string;
  taker_fee: string;
}

interface OptionsContract {
  id: string;
  underlying_symbol: string;
  option_type: string;
  strike_price: string;
  expiry_date: string;
  implied_volatility: string;
  is_active: boolean;
}

type AdminTab = "USERS" | "LEADERBOARD" | "MARKET" | "FEES" | "OPTIONS";

const PER_PAGE = 20;

// ── Component ─────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>("USERS");

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Admin Panel</h2>

      {/* Tab bar */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, borderBottom: "1px solid var(--border)", paddingBottom: 0 }}>
        {(["USERS", "LEADERBOARD", "MARKET", "FEES", "OPTIONS"] as AdminTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            aria-pressed={activeTab === tab}
            aria-label={`Switch to ${tab} tab`}
            style={{
              background: "transparent",
              border: "none",
              borderBottom: activeTab === tab ? "2px solid var(--accent-blue)" : "2px solid transparent",
              color: activeTab === tab ? "var(--accent-blue)" : "var(--text-muted)",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.85rem",
              padding: "8px 16px",
              marginBottom: -1,
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "USERS" && <UsersTab />}
      {activeTab === "LEADERBOARD" && <LeaderboardTab />}
      {activeTab === "MARKET" && <MarketTab />}
      {activeTab === "FEES" && <FeesTab />}
      {activeTab === "OPTIONS" && <OptionsAdminTab />}
    </div>
  );
}

// ── Users Tab ─────────────────────────────────────────────────────────────────

function UsersTab() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [topUpUserId, setTopUpUserId] = useState<string | null>(null);
  const [topUpAmount, setTopUpAmount] = useState("");
  const [msg, setMsg] = useState("");

  const loadUsers = useCallback(
    (p: number, s: string, r: string) => {
      setLoading(true);
      const params: Record<string, unknown> = { page: p, per_page: PER_PAGE };
      if (s) params.search = s;
      if (r) params.role = r;
      api
        .get("/api/admin/users", { params })
        .then((res) => {
          setUsers(res.data.users);
          setTotal(res.data.total);
        })
        .catch(() => {})
        .finally(() => setLoading(false));
    },
    []
  );

  useEffect(() => { loadUsers(page, search, roleFilter); }, [page]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    loadUsers(1, search, roleFilter);
  }

  async function toggleMode(userId: string, currentMode: string) {
    const newMode = currentMode === "SIMULATION" ? "LIVE" : "SIMULATION";
    await api.put(`/api/admin/users/${userId}/mode`, { trading_mode: newMode });
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, trading_mode: newMode } : u))
    );
  }

  async function toggleStatus(userId: string, isActive: boolean) {
    try {
      await api.put(`/api/admin/users/${userId}/status`, { is_active: !isActive });
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: !isActive } : u))
      );
    } catch {
      setMsg("Failed to update status.");
    }
  }

  async function handleTopUp() {
    if (!topUpUserId) return;
    setMsg("");
    try {
      const res = await api.post("/api/admin/wallet/topup", {
        user_id: topUpUserId,
        currency: "USDT",
        amount: parseFloat(topUpAmount),
      });
      setMsg(res.data.message || "Top-up successful.");
      setTopUpUserId(null);
      setTopUpAmount("");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMsg(e?.response?.data?.detail || "Top-up failed.");
    }
  }

  const totalPages = Math.ceil(total / PER_PAGE);

  return (
    <>
      {msg && <p style={{ color: "var(--accent-green)", marginBottom: 12 }}>{msg}</p>}

      {/* Top-up modal */}
      {topUpUserId && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Assign simulation balance"
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
          }}
        >
          <div className="card" style={{ width: 340 }}>
            <h3 style={{ marginBottom: 12 }}>Assign Simulation Balance</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 12 }}>
              User: {users.find((u) => u.id === topUpUserId)?.email}
            </p>
            <label htmlFor="topup-amount" style={{ fontSize: "0.85rem", display: "block", marginBottom: 6 }}>
              Amount (USDT)
            </label>
            <input
              id="topup-amount"
              type="number"
              min="1"
              value={topUpAmount}
              onChange={(e) => setTopUpAmount(e.target.value)}
              placeholder="e.g. 10000"
              style={{ marginBottom: 16 }}
              aria-label="Top-up amount in USDT"
            />
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn-primary" onClick={handleTopUp} aria-label="Confirm top-up">Confirm</button>
              <button
                onClick={() => { setTopUpUserId(null); setTopUpAmount(""); }}
                aria-label="Cancel top-up"
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

      {/* Search/filter bar */}
      <form
        onSubmit={handleSearch}
        style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}
        aria-label="Search and filter users"
      >
        <input
          type="search"
          placeholder="Search by email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search users by email"
          style={{ width: 220 }}
        />
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          aria-label="Filter by role"
          style={{ width: 140 }}
        >
          <option value="">All Roles</option>
          <option value="STUDENT">Student</option>
          <option value="TRADER">Trader</option>
          <option value="ADMIN">Admin</option>
        </select>
        <button type="submit" className="btn-primary" style={{ width: "auto" }}>
          Search
        </button>
      </form>

      <div className="card">
        {loading ? (
          <p style={{ color: "var(--text-muted)" }} aria-live="polite">Loading...</p>
        ) : (
          <>
            <table aria-label="User management table">
              <thead>
                <tr>
                  <th scope="col">Email</th>
                  <th scope="col">Role</th>
                  <th scope="col">Mode</th>
                  <th scope="col">KYC</th>
                  <th scope="col">Status</th>
                  <th scope="col">Registered</th>
                  <th scope="col">Actions</th>
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
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{u.kyc_status}</td>
                    <td>
                      <span style={{ fontSize: "0.75rem", color: u.is_active ? "var(--accent-green)" : "var(--accent-red)" }}>
                        {u.is_active ? "Active" : "Suspended"}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        <button onClick={() => setTopUpUserId(u.id)} aria-label={`Top up balance for ${u.email}`} style={actionBtnStyle("var(--accent-blue)")}>Top Up</button>
                        <button onClick={() => toggleMode(u.id, u.trading_mode)} aria-label={`Toggle trading mode for ${u.email}`} style={actionBtnStyle("var(--accent-green)")}>{u.trading_mode === "SIMULATION" ? "-> LIVE" : "-> SIM"}</button>
                        <button onClick={() => toggleStatus(u.id, u.is_active)} aria-label={u.is_active ? `Suspend ${u.email}` : `Activate ${u.email}`} style={actionBtnStyle(u.is_active ? "var(--accent-red)" : "var(--accent-green)")}>{u.is_active ? "Suspend" : "Activate"}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {totalPages > 1 && (
              <div style={{ display: "flex", gap: 8, marginTop: 16, justifyContent: "center", alignItems: "center" }} aria-label="Pagination">
                <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="btn-primary" aria-label="Previous page" style={{ opacity: page === 1 ? 0.4 : 1 }}>Prev</button>
                <span style={{ color: "var(--text-muted)", lineHeight: "2rem" }} aria-live="polite">Page {page} of {totalPages}</span>
                <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)} className="btn-primary" aria-label="Next page" style={{ opacity: page === totalPages ? 0.4 : 1 }}>Next</button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

// ── Leaderboard Tab ───────────────────────────────────────────────────────────

function LeaderboardTab() {
  const [rows, setRows] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/admin/performance/leaderboard")
      .then((res) => setRows(res.data.leaderboard))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="card">
      <h3 style={{ margin: "0 0 16px" }}>Student Performance Leaderboard</h3>
      {loading ? (
        <p style={{ color: "var(--text-muted)" }} aria-live="polite">Loading...</p>
      ) : rows.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No student data yet.</p>
      ) : (
        <table aria-label="Student leaderboard">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Email</th>
              <th scope="col">P&L (USDT)</th>
              <th scope="col">Balance</th>
              <th scope="col">Trades</th>
              <th scope="col">Win Rate</th>
              <th scope="col">Best</th>
              <th scope="col">Worst</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.user_id}>
                <td style={{ fontWeight: 700, color: r.rank <= 3 ? "var(--accent-blue)" : undefined }}>{r.rank}</td>
                <td>{r.email}</td>
                <td style={{ color: r.realised_pnl >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                  {r.realised_pnl >= 0 ? "+" : ""}{r.realised_pnl.toFixed(2)}
                </td>
                <td>{r.current_balance.toFixed(2)}</td>
                <td>{r.total_trades}</td>
                <td>{r.win_rate_pct}%</td>
                <td style={{ color: "var(--accent-green)", fontSize: "0.8rem" }}>+{r.best_trade.toFixed(2)}</td>
                <td style={{ color: "var(--accent-red)", fontSize: "0.8rem" }}>{r.worst_trade.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ── Market Config Tab ─────────────────────────────────────────────────────────

function MarketTab() {
  const [pairs, setPairs] = useState<TradingPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/api/admin/market/pairs")
      .then((res) => setPairs(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function togglePair(symbol: string, isActive: boolean) {
    try {
      const res = await api.patch(`/api/admin/market/pairs/${symbol}`, { is_active: !isActive });
      setPairs((prev) => prev.map((p) => p.symbol === symbol ? { ...p, is_active: res.data.is_active } : p));
      setMsg(`${symbol} ${!isActive ? "enabled" : "disabled"}.`);
    } catch { setMsg("Failed to update pair."); }
  }

  async function updateLeverage(symbol: string, leverage: number) {
    if (leverage < 1 || leverage > 125) return;
    try {
      const res = await api.patch(`/api/admin/market/pairs/${symbol}`, { max_leverage: leverage });
      setPairs((prev) => prev.map((p) => p.symbol === symbol ? { ...p, max_leverage: res.data.max_leverage } : p));
      setMsg(`${symbol} max leverage updated.`);
    } catch { setMsg("Failed to update leverage."); }
  }

  return (
    <div className="card">
      <h3 style={{ margin: "0 0 16px" }}>Trading Pair Configuration</h3>
      {msg && <p style={{ color: "var(--accent-green)", marginBottom: 12 }}>{msg}</p>}
      {loading ? <p style={{ color: "var(--text-muted)" }}>Loading...</p> : (
        <table aria-label="Trading pair configuration">
          <thead>
            <tr>
              <th scope="col">Symbol</th>
              <th scope="col">Status</th>
              <th scope="col">Max Leverage</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {pairs.map((p) => (
              <tr key={p.id}>
                <td style={{ fontWeight: 600 }}>{p.symbol}</td>
                <td><span style={{ color: p.is_active ? "var(--accent-green)" : "var(--accent-red)", fontSize: "0.8rem" }}>{p.is_active ? "Active" : "Disabled"}</span></td>
                <td>
                  <input type="number" min={1} max={125} defaultValue={p.max_leverage} onBlur={(e) => updateLeverage(p.symbol, parseInt(e.target.value))} aria-label={`Max leverage for ${p.symbol}`} style={{ width: 80 }} />
                </td>
                <td>
                  <button onClick={() => togglePair(p.symbol, p.is_active)} aria-label={`${p.is_active ? "Disable" : "Enable"} ${p.symbol}`} style={actionBtnStyle(p.is_active ? "var(--accent-red)" : "var(--accent-green)")}>
                    {p.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ── Fees Tab ──────────────────────────────────────────────────────────────────

function FeesTab() {
  const [makerFee, setMakerFee] = useState("0.001");
  const [takerFee, setTakerFee] = useState("0.001");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/api/admin/fees/default")
      .then((res) => { setMakerFee(res.data.maker_fee); setTakerFee(res.data.taker_fee); })
      .catch(() => {});
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      await api.put("/api/admin/fees/default", { maker_fee: parseFloat(makerFee), taker_fee: parseFloat(takerFee) });
      setMsg("Fee configuration saved.");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMsg(e?.response?.data?.detail || "Failed to save fees.");
    }
  }

  return (
    <div className="card" style={{ maxWidth: 400 }}>
      <h3 style={{ margin: "0 0 16px" }}>Platform Fee Configuration</h3>
      {msg && <p style={{ color: "var(--accent-green)", marginBottom: 12 }}>{msg}</p>}
      <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: 16 }}>
        Values between 0 and 0.1 (e.g. 0.001 = 0.1%).
      </p>
      <form onSubmit={handleSave} aria-label="Fee configuration form">
        <div style={{ marginBottom: 12 }}>
          <label htmlFor="maker-fee" style={{ fontSize: "0.85rem", display: "block", marginBottom: 4 }}>Maker Fee</label>
          <input id="maker-fee" type="number" step="0.0001" min="0" max="0.1" value={makerFee} onChange={(e) => setMakerFee(e.target.value)} aria-label="Maker fee rate" />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label htmlFor="taker-fee" style={{ fontSize: "0.85rem", display: "block", marginBottom: 4 }}>Taker Fee</label>
          <input id="taker-fee" type="number" step="0.0001" min="0" max="0.1" value={takerFee} onChange={(e) => setTakerFee(e.target.value)} aria-label="Taker fee rate" />
        </div>
        <button type="submit" className="btn-primary" style={{ width: "auto" }}>Save Changes</button>
      </form>
    </div>
  );
}

// ── Options Admin Tab ─────────────────────────────────────────────────────────

function OptionsAdminTab() {
  const [contracts, setContracts] = useState<OptionsContract[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [optType, setOptType] = useState("CALL");
  const [strike, setStrike] = useState("");
  const [expiry, setExpiry] = useState("");
  const [iv, setIv] = useState("0.60");

  const loadContracts = useCallback(() => {
    setLoading(true);
    api.get("/api/admin/options/contracts")
      .then((res) => setContracts(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadContracts(); }, [loadContracts]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setMsg("");
    try {
      await api.post("/api/admin/options/contracts", {
        underlying_symbol: symbol,
        option_type: optType,
        strike_price: parseFloat(strike),
        expiry_date: expiry,
        implied_volatility: parseFloat(iv),
      });
      setMsg("Contract created.");
      setStrike("");
      loadContracts();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMsg(e?.response?.data?.detail || "Failed to create contract.");
    }
  }

  async function toggleContract(id: string) {
    try {
      const res = await api.patch(`/api/admin/options/contracts/${id}/toggle`);
      setContracts((prev) => prev.map((c) => c.id === id ? { ...c, is_active: res.data.is_active } : c));
    } catch { setMsg("Failed to toggle contract."); }
  }

  return (
    <div>
      {msg && <p style={{ color: "var(--accent-green)", marginBottom: 12 }}>{msg}</p>}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ margin: "0 0 16px" }}>Create Options Contract</h3>
        <form onSubmit={handleCreate} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }} aria-label="Create options contract">
          <div>
            <label htmlFor="opt-symbol" style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Symbol</label>
            <select id="opt-symbol" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"].map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="opt-type" style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Type</label>
            <select id="opt-type" value={optType} onChange={(e) => setOptType(e.target.value)}>
              <option value="CALL">CALL</option>
              <option value="PUT">PUT</option>
            </select>
          </div>
          <div>
            <label htmlFor="opt-strike" style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Strike Price</label>
            <input id="opt-strike" type="number" step="any" min="0" required value={strike} onChange={(e) => setStrike(e.target.value)} placeholder="e.g. 70000" />
          </div>
          <div>
            <label htmlFor="opt-expiry" style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Expiry Date</label>
            <input id="opt-expiry" type="date" required value={expiry} onChange={(e) => setExpiry(e.target.value)} />
          </div>
          <div>
            <label htmlFor="opt-iv" style={{ fontSize: "0.8rem", display: "block", marginBottom: 4 }}>Implied Vol</label>
            <input id="opt-iv" type="number" step="0.01" min="0.01" max="5" value={iv} onChange={(e) => setIv(e.target.value)} />
          </div>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button type="submit" className="btn-primary" style={{ width: "100%" }}>Create</button>
          </div>
        </form>
      </div>
      <div className="card">
        <h3 style={{ margin: "0 0 16px" }}>Existing Contracts</h3>
        {loading ? <p style={{ color: "var(--text-muted)" }}>Loading...</p> :
          contracts.length === 0 ? <p style={{ color: "var(--text-muted)" }}>No contracts yet.</p> : (
          <table aria-label="Options contracts">
            <thead>
              <tr>
                <th scope="col">Symbol</th>
                <th scope="col">Type</th>
                <th scope="col">Strike</th>
                <th scope="col">Expiry</th>
                <th scope="col">IV</th>
                <th scope="col">Status</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 600 }}>{c.underlying_symbol}</td>
                  <td style={{ color: c.option_type === "CALL" ? "var(--accent-green)" : "var(--accent-red)" }}>{c.option_type}</td>
                  <td>{parseFloat(c.strike_price).toLocaleString()}</td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{c.expiry_date}</td>
                  <td style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{(parseFloat(c.implied_volatility) * 100).toFixed(0)}%</td>
                  <td><span style={{ color: c.is_active ? "var(--accent-green)" : "var(--accent-red)", fontSize: "0.8rem" }}>{c.is_active ? "Active" : "Inactive"}</span></td>
                  <td>
                    <button onClick={() => toggleContract(c.id)} aria-label={`Toggle ${c.underlying_symbol} ${c.option_type} contract`} style={actionBtnStyle(c.is_active ? "var(--accent-red)" : "var(--accent-green)")}>
                      {c.is_active ? "Deactivate" : "Activate"}
                    </button>
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

// ── Helpers ───────────────────────────────────────────────────────────────────

function actionBtnStyle(color: string): React.CSSProperties {
  return {
    background: "transparent",
    border: `1px solid ${color}`,
    borderRadius: 4,
    color,
    cursor: "pointer",
    fontSize: "0.72rem",
    padding: "3px 8px",
    whiteSpace: "nowrap",
  };
}
