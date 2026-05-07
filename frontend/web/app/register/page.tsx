"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Register first
      await api.post("/api/auth/register", {
        email,
        password,
        full_name: fullName,
      });

      // Auto-login after registration
      const res = await api.post("/api/auth/login", { email, password });
      const { access_token, email: userEmail, role } = res.data;
      setAuth(access_token, userEmail, role);
      router.replace("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed. Please try again.");
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
          Create Account
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: 24, fontSize: "0.9rem" }}>
          Join XChange and start your trading journey
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: "0.85rem" }}>
              Full Name
            </label>
            <input
              type="text"
              required
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

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
              minLength={8}
              autoComplete="new-password"
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
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: "0.85rem", color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--accent-blue)" }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
