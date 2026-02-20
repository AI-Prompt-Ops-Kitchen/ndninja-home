import { useEffect, useRef } from 'react';

function getWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws`;
}

// ---------------------------------------------------------------------------
// Event bus — lets multiple hooks subscribe to WS events independently
// ---------------------------------------------------------------------------

type Handler = (data: unknown) => void;

class WSEventBus {
  private listeners = new Map<string, Set<Handler>>();
  private wildcardListeners = new Set<Handler>();

  subscribe(eventType: string, handler: Handler): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);
    return () => this.listeners.get(eventType)?.delete(handler);
  }

  /** Subscribe to ALL events (handler receives {type, data}). */
  subscribeAll(handler: Handler): () => void {
    this.wildcardListeners.add(handler);
    return () => this.wildcardListeners.delete(handler);
  }

  emit(eventType: string, data: unknown): void {
    this.listeners.get(eventType)?.forEach(h => h(data));
    this.wildcardListeners.forEach(h => h({ type: eventType, data }));
  }
}

export const wsEventBus = new WSEventBus();

// ---------------------------------------------------------------------------
// Singleton WebSocket connection — shared across all hooks
// ---------------------------------------------------------------------------

let wsInstance: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
let refCount = 0;

function connectWs() {
  if (wsInstance && wsInstance.readyState <= WebSocket.OPEN) return;

  const ws = new WebSocket(getWsUrl());
  wsInstance = ws;

  const pingInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.send('ping');
  }, 25_000);

  ws.onopen = () => console.log('[WS] connected');

  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data) as { type: string; data: unknown };
      wsEventBus.emit(msg.type, msg.data);
    } catch { /* ignore */ }
  };

  ws.onerror = () => ws.close();

  ws.onclose = () => {
    clearInterval(pingInterval);
    wsInstance = null;
    console.log('[WS] disconnected — reconnecting in 3s');
    reconnectTimer = setTimeout(connectWs, 3_000);
  };
}

function disconnectWs() {
  clearTimeout(reconnectTimer);
  if (wsInstance) {
    wsInstance.onclose = null;
    wsInstance.close();
    wsInstance = null;
  }
}

/**
 * Hook that keeps the singleton WS connection alive.
 * Call once (e.g., in useJobs) or multiple times — it ref-counts.
 */
export function useWebSocket(onMessage?: (msg: unknown) => void) {
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    refCount++;
    if (refCount === 1) connectWs();

    // Legacy compatibility: if caller passes onMessage, subscribe via wildcard
    let unsub: (() => void) | undefined;
    if (onMessageRef.current) {
      unsub = wsEventBus.subscribeAll((msg) => onMessageRef.current?.(msg));
    }

    return () => {
      unsub?.();
      refCount--;
      if (refCount === 0) disconnectWs();
    };
  }, []);
}
