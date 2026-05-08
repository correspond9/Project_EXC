"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import NotificationBell from "@/components/NotificationBell";
import { ToastProvider } from "@/components/Toast";

/**
 * Layout for all protected pages (dashboard, portfolio, history, admin).
 * On mount: if no access token in memory, attempt a silent token refresh
 * using the HttpOnly refresh cookie. If that fails → redirect to /login.
 */
export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { accessToken, userEmail, userRole, setAuth, clearAuth } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (accessToken) {
      setReady(true);
      return;
    }
    // Try silent refresh
    api.post("/api/auth/refresh")
      .then((res) => {
        setAuth(res.data.access_token, res.data.email, res.data.role);
        setReady(true);
      })
      .catch(() => {
        router.replace("/login?reason=session_expired");
      });
  }, []);

  // Intercept 401 responses globally → redirect to login (session expired)
  useEffect(() => {
    const interceptorId = api.interceptors.response.use(
      (res) => res,
      (err) => {
        if (err?.response?.status === 401 && ready) {
          clearAuth();
          router.replace("/login?reason=session_expired");
        }
        return Promise.reject(err);
      }
    );
    return () => api.interceptors.response.eject(interceptorId);
  }, [ready]);

  async function handleLogout() {
    try { await api.post("/api/auth/logout"); } catch (_) {}
    clearAuth();
    router.replace("/login");
  }

  if (!ready) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)" }}>Loading…</p>
      </div>
    );
  }

  const navLinks = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/kyc", label: "KYC" },
    { href: "/portfolio", label: "Portfolio" },
    { href: "/history", label: "Trade History" },
    ...(userRole === "ADMIN" || userRole === "SUPER_ADMIN"
      ? [{ href: "/admin", label: "Admin" }]
      : []),
  ];

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top nav */}
      <nav
        style={{
          background: "var(--bg-secondary)",
          borderBottom: "1px solid var(--border)",
          padding: "0 1.5rem",
          display: "flex",
          alignItems: "center",
          height: 52,
          gap: 24,
        }}
      >
        <span style={{ fontWeight: 700, fontSize: "1.1rem", marginRight: 16 }}>XChange</span>
        {navLinks.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            style={{
              color: pathname.startsWith(l.href) ? "var(--accent-blue)" : "var(--text-muted)",
              textDecoration: "none",
              fontSize: "0.9rem",
              fontWeight: 500,
            }}
          >
            {l.label}
          </Link>
        ))}
        <span style={{ flex: 1 }} />
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{userEmail}</span>
        <NotificationBell />
        <button
          onClick={handleLogout}
          aria-label="Log out of your account"
          style={{
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: 6,
            color: "var(--text-muted)",
            cursor: "pointer",
            padding: "0.25rem 0.75rem",
            fontSize: "0.85rem",
          }}
        >
          Logout
        </button>
      </nav>

      {/* Page content */}
      <ToastProvider>
        <main style={{ flex: 1, padding: "1.5rem" }} id="main-content">{children}</main>
      </ToastProvider>
    </div>
  );
}
