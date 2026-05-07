"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // POST /api/auth/login — returns access_token; sets HttpOnly refresh cookie
      const res = await api.post("/api/auth/login", { email, password });
      const { access_token, email: userEmail, role } = res.data;
      setAuth(access_token, userEmail, role);
      router.replace("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-primary)",
      }}
    >
      <div className="card" style={{ width: 380 }}>
        <h1 style={{ marginBottom: 8, fontSize: "1.5rem", fontWeight: 700 }}>
          XChange
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: 24, fontSize: "0.9rem" }}>
          Sign in to your trading account
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: "0.85rem" }}>
              Email
            </label>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: "0.85rem" }}>
              Password
            </label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && (
            <p style={{ color: "var(--accent-red)", fontSize: "0.85rem", marginBottom: 12 }}>
              {error}
            </p>
          )}

          <button
            className="btn-primary"
            type="submit"
            disabled={loading}
            style={{ width: "100%", marginTop: 8 }}
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: "0.85rem", color: "var(--text-muted)" }}>
          Don&apos;t have an account?{" "}
          <Link href="/register" style={{ color: "var(--accent-blue)" }}>
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
