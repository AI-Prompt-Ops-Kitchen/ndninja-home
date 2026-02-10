import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Connection status for WebSocket
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'

/**
 * Message types sent from the backend WebSocket
 */
export type WebSocketMessageType =
  | 'connected'
  | 'agent_task_started'
  | 'agent_task_completed'
  | 'agent_task_failed'
  | 'session_completed'
  | 'decision_added'
  | 'pong'

/**
 * WebSocket message structure
 */
export interface WebSocketMessage {
  type: WebSocketMessageType
  agent_role?: string
  task_id?: number
  message?: string
  timestamp?: string
  session_id?: number
  user_id?: number
  decision_id?: number
  decision_text?: string
  [key: string]: unknown
}

/**
 * Return type for the useWebSocket hook
 */
export interface UseWebSocketReturn {
  /** Current connection status */
  status: ConnectionStatus
  /** Array of all received messages */
  messages: WebSocketMessage[]
  /** Most recently received message */
  lastMessage: WebSocketMessage | null
  /** Function to send a message through the WebSocket */
  sendMessage: (message: object) => void
}

// Close codes that should NOT trigger reconnection
const NON_RECONNECT_CODES = [
  1000, // Normal closure
  4001, // Unauthorized
  4003, // Forbidden
]

// Reconnection delay in ms
const RECONNECT_DELAY = 3000

/**
 * Hook for managing WebSocket connections to session updates
 *
 * @param sessionId - The session ID to connect to, or null to disconnect
 * @returns WebSocket state and control functions
 *
 * @example
 * ```tsx
 * const { status, messages, lastMessage, sendMessage } = useWebSocket(sessionId)
 *
 * // Check connection status
 * if (status === 'connected') {
 *   // Send a ping
 *   sendMessage({ type: 'ping' })
 * }
 *
 * // React to new messages
 * useEffect(() => {
 *   if (lastMessage?.type === 'agent_task_completed') {
 *     // Handle task completion
 *   }
 * }, [lastMessage])
 * ```
 */
export function useWebSocket(sessionId: number | null): UseWebSocketReturn {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const [messages, setMessages] = useState<WebSocketMessage[]>([])

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const shouldReconnectRef = useRef<boolean>(false)

  // Clear any pending reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current !== null) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  // Schedule a reconnection attempt
  const scheduleReconnect = useCallback(() => {
    clearReconnectTimeout()
    setStatus('reconnecting')

    reconnectTimeoutRef.current = window.setTimeout(() => {
      if (shouldReconnectRef.current) {
        connect()
      }
    }, RECONNECT_DELAY)
  }, [clearReconnectTimeout])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (sessionId === null) {
      return
    }

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setStatus('connecting')

    // Build WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/sessions/${sessionId}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
      shouldReconnectRef.current = true
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        setMessages((prev) => [...prev, message])
      } catch (e) {
        // Ignore malformed messages
        console.warn('Failed to parse WebSocket message:', e)
      }
    }

    ws.onerror = () => {
      setStatus('error')
    }

    ws.onclose = (event: CloseEvent) => {
      wsRef.current = null

      // Check if we should attempt to reconnect
      if (shouldReconnectRef.current && !NON_RECONNECT_CODES.includes(event.code)) {
        scheduleReconnect()
      } else {
        setStatus('disconnected')
        shouldReconnectRef.current = false
      }
    }
  }, [sessionId, scheduleReconnect])

  // Send a message through the WebSocket
  const sendMessage = useCallback((message: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  // Connect when sessionId changes
  useEffect(() => {
    // Clear messages when session changes
    setMessages([])
    clearReconnectTimeout()

    if (sessionId === null) {
      // Disconnect if no session
      if (wsRef.current) {
        shouldReconnectRef.current = false
        wsRef.current.close()
        wsRef.current = null
      }
      setStatus('disconnected')
      return
    }

    // Connect to new session
    connect()

    // Cleanup on unmount or sessionId change
    return () => {
      clearReconnectTimeout()
      shouldReconnectRef.current = false
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [sessionId, connect, clearReconnectTimeout])

  // Compute last message
  const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null

  return {
    status,
    messages,
    lastMessage,
    sendMessage,
  }
}
