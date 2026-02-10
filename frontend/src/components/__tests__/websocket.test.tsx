import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { renderHook, act as actHook } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { useWebSocket, WebSocketMessage, ConnectionStatus } from '../../hooks/useWebSocket'
import { SessionDetail } from '../sessions/SessionDetail'
import type { Session, SessionDecision, AgentTask } from '../../hooks/useSessions'

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = []
  url: string
  readyState: number = WebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  sentMessages: string[] = []

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
    // Simulate async connection
    setTimeout(() => {
      if (this.readyState === WebSocket.CONNECTING) {
        this.readyState = WebSocket.OPEN
        this.onopen?.(new Event('open'))
      }
    }, 0)
  }

  send(data: string) {
    this.sentMessages.push(data)
  }

  close(code?: number, reason?: string) {
    this.readyState = WebSocket.CLOSED
    this.onclose?.(new CloseEvent('close', { code, reason }))
  }

  // Test helpers
  simulateMessage(data: object) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }))
  }

  simulateError() {
    this.onerror?.(new Event('error'))
  }

  simulateClose(code: number = 1000, reason: string = '') {
    this.readyState = WebSocket.CLOSED
    this.onclose?.(new CloseEvent('close', { code, reason }))
  }

  static reset() {
    MockWebSocket.instances = []
  }

  static getLastInstance(): MockWebSocket | undefined {
    return MockWebSocket.instances[MockWebSocket.instances.length - 1]
  }
}

// Replace global WebSocket with mock
const originalWebSocket = global.WebSocket

beforeEach(() => {
  vi.useFakeTimers()
  MockWebSocket.reset()
  global.WebSocket = MockWebSocket as unknown as typeof WebSocket
})

afterEach(() => {
  vi.useRealTimers()
  global.WebSocket = originalWebSocket
  vi.clearAllMocks()
})

// Sample test data
const mockSession: Session = {
  id: 1,
  team_id: 1,
  user_id: 1,
  feature_name: 'Test Feature',
  status: 'active',
  started_at: '2024-01-15T10:00:00Z',
  ended_at: null,
  duration_seconds: null,
}

const mockDecision: SessionDecision = {
  id: 1,
  session_id: 1,
  decision_text: 'Use React Query',
  category: 'architecture',
  confidence: 'high',
  created_at: '2024-01-15T10:30:00Z',
}

const mockAgentTask: AgentTask = {
  id: 1,
  session_id: 1,
  agent_role: 'Architect',
  task_description: 'Design system architecture',
  status: 'pending',
  started_at: null,
  completed_at: null,
  duration_seconds: null,
  error_message: null,
  created_at: '2024-01-15T10:00:00Z',
}

// Wrapper with Router
const RouterWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
)

describe('useWebSocket hook', () => {
  describe('connection lifecycle', () => {
    it('connects to WebSocket when sessionId is provided', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      expect(result.current.status).toBe('connecting')

      // Let the mock WebSocket connect
      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      expect(MockWebSocket.getLastInstance()?.url).toContain('/ws/sessions/1')
      expect(result.current.status).toBe('connected')
    })

    it('does not connect when sessionId is null', () => {
      const { result } = renderHook(() => useWebSocket(null), { wrapper: RouterWrapper })

      expect(result.current.status).toBe('disconnected')
      expect(MockWebSocket.instances).toHaveLength(0)
    })

    it('disconnects and reconnects when sessionId changes', async () => {
      const { result, rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { wrapper: RouterWrapper, initialProps: { sessionId: 1 as number | null } }
      )

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      expect(MockWebSocket.instances).toHaveLength(1)
      expect(MockWebSocket.instances[0].url).toContain('/ws/sessions/1')

      // Change session ID
      rerender({ sessionId: 2 })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      // Should have closed the old connection and opened a new one
      expect(MockWebSocket.instances).toHaveLength(2)
      expect(MockWebSocket.instances[1].url).toContain('/ws/sessions/2')
    })

    it('cleans up WebSocket connection on unmount', async () => {
      const { unmount } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()
      expect(ws?.readyState).toBe(WebSocket.OPEN)

      unmount()

      expect(ws?.readyState).toBe(WebSocket.CLOSED)
    })

    it('updates status to disconnected on close', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      expect(result.current.status).toBe('connected')

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateClose()
      })

      expect(result.current.status).toBe('disconnected')
    })

    it('updates status to error on WebSocket error', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateError()
      })

      expect(result.current.status).toBe('error')
    })
  })

  describe('message handling', () => {
    it('stores received messages', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      const message: WebSocketMessage = {
        type: 'agent_task_started',
        agent_role: 'Architect',
        task_id: 1,
        message: 'Starting architecture analysis',
        timestamp: '2024-01-15T10:30:00Z',
      }

      await actHook(async () => {
        ws?.simulateMessage(message)
      })

      expect(result.current.messages).toHaveLength(1)
      expect(result.current.messages[0]).toEqual(message)
    })

    it('accumulates multiple messages', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      const messages: WebSocketMessage[] = [
        {
          type: 'agent_task_started',
          agent_role: 'Architect',
          task_id: 1,
          message: 'Starting',
          timestamp: '2024-01-15T10:30:00Z',
        },
        {
          type: 'agent_task_completed',
          agent_role: 'Architect',
          task_id: 1,
          message: 'Completed',
          timestamp: '2024-01-15T10:35:00Z',
        },
      ]

      await actHook(async () => {
        for (const msg of messages) {
          ws?.simulateMessage(msg)
        }
      })

      expect(result.current.messages).toHaveLength(2)
      expect(result.current.messages[0].type).toBe('agent_task_started')
      expect(result.current.messages[1].type).toBe('agent_task_completed')
    })

    it('returns the latest message', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'agent_task_started',
          agent_role: 'Architect',
          task_id: 1,
          message: 'First',
          timestamp: '2024-01-15T10:30:00Z',
        })
        ws?.simulateMessage({
          type: 'agent_task_completed',
          agent_role: 'Architect',
          task_id: 1,
          message: 'Second',
          timestamp: '2024-01-15T10:35:00Z',
        })
      })

      expect(result.current.lastMessage?.type).toBe('agent_task_completed')
    })

    it('clears messages when session changes', async () => {
      const { result, rerender } = renderHook(
        ({ sessionId }) => useWebSocket(sessionId),
        { wrapper: RouterWrapper, initialProps: { sessionId: 1 as number | null } }
      )

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'agent_task_started',
          agent_role: 'Architect',
          task_id: 1,
          message: 'Message for session 1',
          timestamp: '2024-01-15T10:30:00Z',
        })
      })

      expect(result.current.messages).toHaveLength(1)

      // Change session ID
      rerender({ sessionId: 2 })

      expect(result.current.messages).toHaveLength(0)
    })
  })

  describe('sendMessage function', () => {
    it('sends messages through WebSocket', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        result.current.sendMessage({ type: 'ping' })
      })

      expect(ws?.sentMessages).toHaveLength(1)
      expect(JSON.parse(ws?.sentMessages[0] || '')).toEqual({ type: 'ping' })
    })

    it('does not send when not connected', async () => {
      const { result } = renderHook(() => useWebSocket(null), { wrapper: RouterWrapper })

      await actHook(async () => {
        result.current.sendMessage({ type: 'ping' })
      })

      // No WebSocket instance created, so nothing sent
      expect(MockWebSocket.instances).toHaveLength(0)
    })
  })

  describe('reconnection', () => {
    it('attempts to reconnect after unexpected close', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      expect(result.current.status).toBe('connected')
      expect(MockWebSocket.instances).toHaveLength(1)

      const ws = MockWebSocket.getLastInstance()

      // Simulate unexpected close (not a clean close)
      await actHook(async () => {
        ws?.simulateClose(1006, 'Connection lost')
      })

      expect(result.current.status).toBe('reconnecting')

      // Wait for reconnect delay (3 seconds default)
      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(3000)
      })

      // Should have created a new connection
      expect(MockWebSocket.instances).toHaveLength(2)
    })

    it('does not reconnect after clean close', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      // Simulate clean close (code 1000)
      await actHook(async () => {
        ws?.simulateClose(1000, 'Normal closure')
      })

      expect(result.current.status).toBe('disconnected')

      // Wait for potential reconnect time
      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(5000)
      })

      // Should not have created a new connection
      expect(MockWebSocket.instances).toHaveLength(1)
    })

    it('does not reconnect after auth error (4001)', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      // Simulate auth error close
      await actHook(async () => {
        ws?.simulateClose(4001, 'Unauthorized')
      })

      expect(result.current.status).toBe('disconnected')

      // Wait for potential reconnect time
      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(5000)
      })

      // Should not have created a new connection
      expect(MockWebSocket.instances).toHaveLength(1)
    })
  })

  describe('message types', () => {
    it('handles agent_task_started message', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'agent_task_started',
          agent_role: 'Architect',
          task_id: 1,
          message: 'Starting architecture analysis',
          timestamp: '2024-01-15T10:30:00Z',
        })
      })

      expect(result.current.lastMessage?.type).toBe('agent_task_started')
      expect(result.current.lastMessage?.agent_role).toBe('Architect')
    })

    it('handles agent_task_completed message', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'agent_task_completed',
          agent_role: 'Architect',
          task_id: 1,
          message: 'Architecture analysis complete',
          timestamp: '2024-01-15T10:35:00Z',
        })
      })

      expect(result.current.lastMessage?.type).toBe('agent_task_completed')
    })

    it('handles agent_task_failed message', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'agent_task_failed',
          agent_role: 'Backend Dev',
          task_id: 2,
          message: 'Connection timeout',
          timestamp: '2024-01-15T10:40:00Z',
        })
      })

      expect(result.current.lastMessage?.type).toBe('agent_task_failed')
    })

    it('handles session_completed message', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'session_completed',
          message: 'Session completed successfully',
          timestamp: '2024-01-15T11:00:00Z',
        })
      })

      expect(result.current.lastMessage?.type).toBe('session_completed')
    })

    it('handles decision_added message', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'decision_added',
          decision_id: 1,
          decision_text: 'Use microservices architecture',
          message: 'New decision recorded',
          timestamp: '2024-01-15T10:45:00Z',
        })
      })

      expect(result.current.lastMessage?.type).toBe('decision_added')
    })

    it('handles connected message', async () => {
      const { result } = renderHook(() => useWebSocket(1), { wrapper: RouterWrapper })

      await actHook(async () => {
        await vi.advanceTimersByTimeAsync(10)
      })

      const ws = MockWebSocket.getLastInstance()

      await actHook(async () => {
        ws?.simulateMessage({
          type: 'connected',
          session_id: 1,
          user_id: 1,
        })
      })

      expect(result.current.lastMessage?.type).toBe('connected')
    })
  })
})

describe('SessionDetail with WebSocket integration', () => {
  it('shows connection status indicator', async () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[mockDecision]}
        tasks={[mockAgentTask]}
        loading={false}
        connectionStatus="connected"
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByTestId('connection-status')).toBeInTheDocument()
    expect(screen.getByText(/connected/i)).toBeInTheDocument()
  })

  it('shows disconnected status', async () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[]}
        loading={false}
        connectionStatus="disconnected"
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText(/disconnected/i)).toBeInTheDocument()
  })

  it('shows reconnecting status', async () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[]}
        loading={false}
        connectionStatus="reconnecting"
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText(/reconnecting/i)).toBeInTheDocument()
  })

  it('shows connecting status', async () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[]}
        loading={false}
        connectionStatus="connecting"
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText(/connecting/i)).toBeInTheDocument()
  })

  it('shows error status', async () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[]}
        loading={false}
        connectionStatus="error"
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText(/error/i)).toBeInTheDocument()
  })

  it('does not show connection status for completed sessions', async () => {
    const completedSession: Session = {
      ...mockSession,
      status: 'completed',
      ended_at: '2024-01-15T12:00:00Z',
      duration_seconds: 7200,
    }

    render(
      <SessionDetail
        session={completedSession}
        decisions={[]}
        tasks={[]}
        loading={false}
        connectionStatus="disconnected"
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.queryByTestId('connection-status')).not.toBeInTheDocument()
  })

  it('updates task status when receiving agent_task_started', async () => {
    const onTaskUpdate = vi.fn()

    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[mockAgentTask]}
        loading={false}
        connectionStatus="connected"
        onTaskUpdate={onTaskUpdate}
      />,
      { wrapper: RouterWrapper }
    )

    // Verify initial task status
    expect(screen.getByText('pending')).toBeInTheDocument()
  })
})
