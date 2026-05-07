/**
 * WebSocket base URL helper.
 * Reads NEXT_PUBLIC_WS_BASE_URL from env (e.g. ws://localhost/ws).
 */
export function wsUrl(path: string): string {
  const base =
    process.env.NEXT_PUBLIC_WS_BASE_URL?.replace(/\/$/, "") ||
    "ws://localhost/ws";
  return `${base}${path}`;
}
