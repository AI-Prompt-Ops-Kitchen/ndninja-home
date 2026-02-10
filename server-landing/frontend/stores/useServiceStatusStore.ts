import { create } from 'zustand'
import { ServiceInfo, SystemMetrics } from '@/lib/types'

interface ServiceStatusState {
  // Data
  services: ServiceInfo[]
  systemMetrics: SystemMetrics | null
  lastUpdate: Date | null

  // Connection State
  isConnected: boolean
  isConnecting: boolean
  error: string | null

  // Actions
  connect: () => void
  disconnect: () => void
  reconnect: () => void
}

let ws: WebSocket | null = null
let reconnectTimeout: NodeJS.Timeout | null = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 3000

export const useServiceStatusStore = create<ServiceStatusState>((set, get) => ({
  // Initial state
  services: [],
  systemMetrics: null,
  lastUpdate: null,
  isConnected: false,
  isConnecting: false,
  error: null,

  // Actions
  connect: () => {
    const state = get()

    // Don't connect if already connected or connecting
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    set({ isConnecting: true, error: null })

    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/services`

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket connected')
        reconnectAttempts = 0
        set({ isConnected: true, isConnecting: false, error: null })
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'update') {
            set({
              services: data.services || [],
              systemMetrics: data.metrics || null,
              lastUpdate: new Date(),
              error: null
            })
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        set({ error: 'WebSocket connection error' })
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        set({ isConnected: false, isConnecting: false })

        // Attempt to reconnect
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts++
          console.log(`Reconnecting... (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`)

          reconnectTimeout = setTimeout(() => {
            get().reconnect()
          }, RECONNECT_DELAY)
        } else {
          set({ error: 'Failed to maintain WebSocket connection' })
        }
      }
    } catch (err) {
      console.error('Error creating WebSocket:', err)
      set({
        error: err instanceof Error ? err.message : 'Failed to connect',
        isConnecting: false
      })
    }
  },

  disconnect: () => {
    // Clear reconnect timeout
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }

    // Close WebSocket
    if (ws) {
      ws.close()
      ws = null
    }

    set({ isConnected: false, isConnecting: false })
  },

  reconnect: () => {
    const { disconnect, connect } = get()
    disconnect()
    setTimeout(() => {
      connect()
    }, 100)
  },
}))
