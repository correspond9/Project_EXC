"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import api from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

interface Notification {
  id: string;
  type: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string | null;
}

function typeColor(type: string): string {
  switch (type) {
    case "MARGIN_CALL":   return "#facc15"; // yellow
    case "LIQUIDATION":  return "#f87171"; // red
    case "FILL":         return "#4ade80"; // green
    default:             return "#94a3b8"; // muted
  }
}

export default function NotificationBell() {
  const { accessToken } = useAuthStore();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  // Load initial notifications
  const loadNotifications = useCallback(async () => {
    if (!accessToken) return;
    try {
      const res = await api.get<Notification[]>("/api/notifications?limit=20");
      setNotifications(res.data);
    } catch (_) {}
  }, [accessToken]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  // Live WS connection
  useEffect(() => {
    if (!accessToken) return;

    const wsBase =
      (process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost/ws")
        .replace(/\/$/, "")
        .replace(/\/ws$/, ""); // strip trailing /ws — we'll add /ws/user/notifications

    const url = `${wsBase}/ws/user/notifications?token=${encodeURIComponent(accessToken)}`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "ping") return;
        setNotifications((prev) => [data as Notification, ...prev].slice(0, 50));
      } catch (_) {}
    };

    return () => {
      socket.close();
    };
  }, [accessToken]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  async function handleMarkRead(id: string) {
    try {
      await api.put(`/api/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (_) {}
  }

  async function handleMarkAllRead() {
    try {
      await api.put("/api/notifications/read-all");
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (_) {}
  }

  return (
    <div ref={dropdownRef} style={{ position: "relative" }}>
      {/* Bell button */}
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: "var(--text-muted)",
          fontSize: "1.25rem",
          position: "relative",
          padding: "0.2rem 0.4rem",
          lineHeight: 1,
        }}
        title="Notifications"
        aria-label="Notifications"
      >
        🔔
        {unreadCount > 0 && (
          <span
            style={{
              position: "absolute",
              top: -2,
              right: -4,
              background: "#f87171",
              color: "#fff",
              borderRadius: "999px",
              fontSize: "0.65rem",
              fontWeight: 700,
              padding: "0 4px",
              minWidth: 16,
              textAlign: "center",
              lineHeight: "16px",
              pointerEvents: "none",
            }}
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div
          style={{
            position: "absolute",
            top: "110%",
            right: 0,
            width: 340,
            maxHeight: 440,
            overflowY: "auto",
            background: "var(--bg-secondary)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            zIndex: 1000,
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "0.6rem 1rem",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--accent-blue)",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                }}
              >
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          {notifications.length === 0 ? (
            <div
              style={{
                padding: "1.5rem 1rem",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "0.85rem",
              }}
            >
              No notifications yet
            </div>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                onClick={() => !n.is_read && handleMarkRead(n.id)}
                style={{
                  padding: "0.6rem 1rem",
                  borderBottom: "1px solid var(--border)",
                  cursor: n.is_read ? "default" : "pointer",
                  background: n.is_read ? "transparent" : "rgba(255,255,255,0.03)",
                  opacity: n.is_read ? 0.6 : 1,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    marginBottom: 2,
                  }}
                >
                  <span
                    style={{
                      fontSize: "0.65rem",
                      fontWeight: 700,
                      color: typeColor(n.type),
                      background: "rgba(255,255,255,0.05)",
                      borderRadius: 4,
                      padding: "1px 5px",
                    }}
                  >
                    {n.type.replace("_", " ")}
                  </span>
                  <span style={{ fontWeight: 600, fontSize: "0.82rem", color: "var(--text-primary)" }}>
                    {n.title}
                  </span>
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                  {n.body}
                </div>
                {n.created_at && (
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: 3 }}>
                    {new Date(n.created_at).toLocaleString()}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
