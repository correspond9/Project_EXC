"use client";

import { useEffect, useRef, useCallback } from "react";

interface UseWebSocketOptions {
  /** Called whenever a message arrives */
  onMessage: (event: MessageEvent) => void;
  /** Called on successful (re)connection */
  onOpen?: () => void;
  /** Called on error */
  onError?: (event: Event) => void;
  /** Initial reconnect delay in ms (default 1000). Doubles each attempt, capped at maxDelay. */
  initialDelay?: number;
  /** Maximum reconnect delay in ms (default 30000) */
  maxDelay?: number;
  /** Set false to disable auto-reconnect (default true) */
  reconnect?: boolean;
}

/**
 * Sprint 10 — WebSocket hook with exponential back-off reconnection.
 *
 * Usage:
 *   useReconnectingWebSocket(url, { onMessage: (ev) => ... })
 *
 * The hook cleans up properly on unmount or when `url` changes.
 */
export function useReconnectingWebSocket(
  url: string | null,
  options: UseWebSocketOptions
) {
  const { onMessage, onOpen, onError, initialDelay = 1000, maxDelay = 30000, reconnect = true } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const delayRef = useRef(initialDelay);
  const mountedRef = useRef(true);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Keep callbacks in refs so the effect doesn't re-run on their identity change
  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onErrorRef = useRef(onError);
  onMessageRef.current = onMessage;
  onOpenRef.current = onOpen;
  onErrorRef.current = onError;

  const connect = useCallback(() => {
    if (!url || !mountedRef.current) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      delayRef.current = initialDelay; // reset on success
      onOpenRef.current?.();
    };

    ws.onmessage = (ev) => {
      onMessageRef.current(ev);
    };

    ws.onerror = (ev) => {
      onErrorRef.current?.(ev);
    };

    ws.onclose = () => {
      if (!mountedRef.current || !reconnect) return;
      // Schedule reconnect with exponential back-off
      timerRef.current = setTimeout(() => {
        if (mountedRef.current) {
          delayRef.current = Math.min(delayRef.current * 2, maxDelay);
          connect();
        }
      }, delayRef.current);
    };
  }, [url, initialDelay, maxDelay, reconnect]);

  useEffect(() => {
    mountedRef.current = true;
    delayRef.current = initialDelay;
    connect();

    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);
}
