"use client";

/**
 * Sprint 10 — Skeleton loading components with Tailwind pulse animation.
 */

interface SkeletonProps {
  className?: string;
  height?: string | number;
  width?: string | number;
  rounded?: boolean;
}

export function Skeleton({ className = "", height, width, rounded = false }: SkeletonProps) {
  const style: React.CSSProperties = {};
  if (height) style.height = typeof height === "number" ? `${height}px` : height;
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse bg-gray-700 ${rounded ? "rounded-full" : "rounded"} ${className}`}
      style={style}
    />
  );
}

export function CardSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="card"
      style={{ padding: 16 }}
    >
      <Skeleton height={12} width="40%" className="mb-3" />
      <Skeleton height={28} width="70%" className="mb-2" />
      <Skeleton height={12} width="55%" />
    </div>
  );
}

export function TableRowSkeleton({ cols = 5 }: { cols?: number }) {
  return (
    <tr aria-hidden="true">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} style={{ padding: "8px 12px" }}>
          <Skeleton height={14} width="80%" />
        </td>
      ))}
    </tr>
  );
}

export function ChartSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="card animate-pulse"
      style={{ height: 356, padding: 0, background: "var(--bg-secondary)" }}
    >
      <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Loading chart…</p>
      </div>
    </div>
  );
}
