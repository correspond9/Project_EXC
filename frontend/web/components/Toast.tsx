"use client";

import { useEffect, useCallback, useState, createContext, useContext, ReactNode, useRef } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────

export type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToastContextValue {
  addToast: (message: string, type?: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
}

// ── Context ───────────────────────────────────────────────────────────────────

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}

// ── Provider ──────────────────────────────────────────────────────────────────

/**
 * Sprint 10 — Toast notification provider.
 * Wrap layout children with <ToastProvider> to enable toasts anywhere.
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, type: ToastType = "info", duration = 4000) => {
      counterRef.current += 1;
      const id = `toast-${counterRef.current}`;
      setToasts((prev) => [...prev, { id, message, type, duration }]);
      setTimeout(() => removeToast(id), duration);
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

// ── Toast Container ───────────────────────────────────────────────────────────

const TYPE_COLORS: Record<ToastType, string> = {
  success: "var(--accent-green)",
  error: "var(--accent-red)",
  info: "var(--accent-blue)",
  warning: "#f59e0b",
};

const TYPE_ICONS: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  info: "ℹ",
  warning: "⚠",
};

function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: Toast[];
  onRemove: (id: string) => void;
}) {
  return (
    <div
      aria-live="polite"
      aria-label="Notifications"
      style={{
        position: "fixed",
        bottom: 24,
        right: 24,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        maxWidth: 360,
      }}
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 10,
            padding: "12px 16px",
            borderRadius: 8,
            background: "var(--bg-secondary)",
            border: `1px solid ${TYPE_COLORS[t.type]}`,
            boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
            fontSize: "0.85rem",
            animation: "slideInRight 0.2s ease",
          }}
        >
          <span style={{ color: TYPE_COLORS[t.type], fontWeight: 700, minWidth: 16 }}>
            {TYPE_ICONS[t.type]}
          </span>
          <span style={{ flex: 1, color: "var(--text-primary)" }}>{t.message}</span>
          <button
            onClick={() => onRemove(t.id)}
            aria-label="Dismiss notification"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "var(--text-muted)",
              fontSize: "1rem",
              padding: 0,
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
