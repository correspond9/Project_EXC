/**
 * WebSocket base URL helper.
 * Reads NEXT_PUBLIC_WS_BASE_URL from env (e.g. ws://localhost/ws).
 */
export function wsUrl(path: string): string {
  const fallbackBase =
    typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws`
      : "ws://localhost/ws";

  const base =
    process.env.NEXT_PUBLIC_WS_BASE_URL?.replace(/\/$/, "") ||
    fallbackBase;
  return `${base}${path}`;
}
