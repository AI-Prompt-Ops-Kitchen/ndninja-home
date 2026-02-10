import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderHook, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import api from '../../api/client'
import { useSessions, useSessionDetail } from '../../hooks/useSessions'
import type { Session, SessionDecision, AgentTask } from '../../hooks/useSessions'
import { SessionCard } from '../sessions/SessionCard'
import { SessionList } from '../sessions/SessionList'
import { SessionDetail } from '../sessions/SessionDetail'

// Mock the API client
vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockApi = vi.mocked(api)

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

const mockCompletedSession: Session = {
  id: 2,
  team_id: 1,
  user_id: 1,
  feature_name: 'Completed Feature',
  status: 'completed',
  started_at: '2024-01-15T08:00:00Z',
  ended_at: '2024-01-15T10:30:00Z',
  duration_seconds: 9000,
}

const mockDecision: SessionDecision = {
  id: 1,
  session_id: 1,
  decision_text: 'Use React Query for state management',
  category: 'architecture',
  confidence: 'high',
  created_at: '2024-01-15T10:30:00Z',
}

const mockAgentTask: AgentTask = {
  id: 1,
  session_id: 1,
  agent_role: 'Architect',
  task_description: 'Design system architecture',
  status: 'completed',
  started_at: '2024-01-15T10:00:00Z',
  completed_at: '2024-01-15T10:30:00Z',
  duration_seconds: 1800,
  error_message: null,
  created_at: '2024-01-15T10:00:00Z',
}

const mockRunningTask: AgentTask = {
  id: 2,
  session_id: 1,
  agent_role: 'Frontend Dev',
  task_description: 'Implement UI components',
  status: 'running',
  started_at: '2024-01-15T10:30:00Z',
  completed_at: null,
  duration_seconds: null,
  error_message: null,
  created_at: '2024-01-15T10:30:00Z',
}

const mockFailedTask: AgentTask = {
  id: 3,
  session_id: 1,
  agent_role: 'Backend Dev',
  task_description: 'Set up API endpoints',
  status: 'failed',
  started_at: '2024-01-15T10:30:00Z',
  completed_at: '2024-01-15T10:35:00Z',
  duration_seconds: 300,
  error_message: 'Connection timeout',
  created_at: '2024-01-15T10:30:00Z',
}

// Wrapper with Router for components that use routing
const RouterWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
)

describe('useSessions hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches sessions list successfully', async () => {
    mockApi.get.mockResolvedValueOnce({ data: [mockSession, mockCompletedSession] })

    const { result } = renderHook(() => useSessions(), { wrapper: RouterWrapper })

    expect(result.current.loading).toBe(true)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.sessions).toHaveLength(2)
    expect(result.current.sessions[0].feature_name).toBe('Test Feature')
    expect(result.current.error).toBeNull()
    expect(mockApi.get).toHaveBeenCalledWith('/sessions')
  })

  it('filters sessions by team_id when provided', async () => {
    mockApi.get.mockResolvedValueOnce({ data: [mockSession] })

    const { result } = renderHook(() => useSessions(1), { wrapper: RouterWrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(mockApi.get).toHaveBeenCalledWith('/sessions', { params: { team_id: 1 } })
  })

  it('handles fetch error gracefully', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useSessions(), { wrapper: RouterWrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Failed to load sessions')
    expect(result.current.sessions).toEqual([])
  })

  it('starts a new session', async () => {
    mockApi.get.mockResolvedValueOnce({ data: [] })
    const newSession = { ...mockSession, id: 3 }
    mockApi.post.mockResolvedValueOnce({ data: newSession })

    const { result } = renderHook(() => useSessions(), { wrapper: RouterWrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.startSession(1, 'New Feature')
    })

    expect(mockApi.post).toHaveBeenCalledWith('/sessions', {
      team_id: 1,
      feature_name: 'New Feature',
    })
    expect(result.current.sessions).toContainEqual(newSession)
  })

  it('completes a session', async () => {
    mockApi.get.mockResolvedValueOnce({ data: [mockSession] })
    const completed = { ...mockSession, status: 'completed', ended_at: '2024-01-15T12:00:00Z' }
    mockApi.put.mockResolvedValueOnce({ data: completed })

    const { result } = renderHook(() => useSessions(), { wrapper: RouterWrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.completeSession(1)
    })

    expect(mockApi.put).toHaveBeenCalledWith('/sessions/1/complete')
    expect(result.current.sessions[0].status).toBe('completed')
  })

  it('refetches sessions', async () => {
    mockApi.get.mockResolvedValue({ data: [mockSession] })

    const { result } = renderHook(() => useSessions(), { wrapper: RouterWrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.refetch()
    })

    expect(mockApi.get).toHaveBeenCalledTimes(2)
  })
})

describe('useSessionDetail hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches session detail with decisions and tasks', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockSession })
      .mockResolvedValueOnce({ data: [mockDecision] })
      .mockResolvedValueOnce({ data: [mockAgentTask] })

    const { result } = renderHook(() => useSessionDetail(1), { wrapper: RouterWrapper })

    expect(result.current.loading).toBe(true)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.session).toEqual(mockSession)
    expect(result.current.decisions).toHaveLength(1)
    expect(result.current.decisions[0].decision_text).toBe('Use React Query for state management')
    expect(result.current.tasks).toHaveLength(1)
    expect(result.current.tasks[0].agent_role).toBe('Architect')
    expect(mockApi.get).toHaveBeenCalledWith('/sessions/1')
    expect(mockApi.get).toHaveBeenCalledWith('/sessions/1/decisions')
    expect(mockApi.get).toHaveBeenCalledWith('/sessions/1/tasks')
  })

  it('returns null when sessionId is null', async () => {
    const { result } = renderHook(() => useSessionDetail(null), { wrapper: RouterWrapper })

    expect(result.current.loading).toBe(false)
    expect(result.current.session).toBeNull()
    expect(result.current.decisions).toEqual([])
    expect(result.current.tasks).toEqual([])
  })

  it('adds a decision to session', async () => {
    mockApi.get
      .mockResolvedValueOnce({ data: mockSession })
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [] })
    mockApi.post.mockResolvedValueOnce({ data: mockDecision })

    const { result } = renderHook(() => useSessionDetail(1), { wrapper: RouterWrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.addDecision('Use React Query for state management', 'architecture', 'high')
    })

    expect(mockApi.post).toHaveBeenCalledWith('/sessions/1/decisions', {
      decision_text: 'Use React Query for state management',
      category: 'architecture',
      confidence: 'high',
    })
    expect(result.current.decisions).toContainEqual(mockDecision)
  })
})

describe('SessionCard component', () => {
  it('renders session information correctly', () => {
    render(<SessionCard session={mockSession} />, { wrapper: RouterWrapper })

    expect(screen.getByText('Test Feature')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('displays correct status badge for active session', () => {
    render(<SessionCard session={mockSession} />, { wrapper: RouterWrapper })

    const statusBadge = screen.getByText('active')
    expect(statusBadge).toHaveClass('bg-green-100')
  })

  it('displays correct status badge for completed session', () => {
    render(<SessionCard session={mockCompletedSession} />, { wrapper: RouterWrapper })

    const statusBadge = screen.getByText('completed')
    expect(statusBadge).toHaveClass('bg-blue-100')
  })

  it('shows duration for completed sessions', () => {
    render(<SessionCard session={mockCompletedSession} />, { wrapper: RouterWrapper })

    expect(screen.getByText(/2h 30m/)).toBeInTheDocument()
  })

  it('shows "In progress" for active sessions', () => {
    render(<SessionCard session={mockSession} />, { wrapper: RouterWrapper })

    expect(screen.getByText(/In progress/)).toBeInTheDocument()
  })

  it('calls onSelect when clicked', async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()

    render(<SessionCard session={mockSession} onSelect={onSelect} />, { wrapper: RouterWrapper })

    await user.click(screen.getByText(/View Details/))

    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('calls onComplete when complete button clicked', async () => {
    const onComplete = vi.fn()
    const user = userEvent.setup()

    render(<SessionCard session={mockSession} onComplete={onComplete} />, { wrapper: RouterWrapper })

    await user.click(screen.getByText('Complete'))

    expect(onComplete).toHaveBeenCalledWith(1)
  })

  it('hides complete button for completed sessions', () => {
    render(<SessionCard session={mockCompletedSession} onComplete={vi.fn()} />, { wrapper: RouterWrapper })

    expect(screen.queryByText('Complete')).not.toBeInTheDocument()
  })
})

describe('SessionList component', () => {
  it('renders loading state', () => {
    render(<SessionList sessions={[]} loading={true} />, { wrapper: RouterWrapper })

    expect(screen.getByText('Loading sessions...')).toBeInTheDocument()
  })

  it('renders error state', () => {
    render(<SessionList sessions={[]} error="Failed to load" />, { wrapper: RouterWrapper })

    expect(screen.getByText('Failed to load')).toBeInTheDocument()
  })

  it('renders empty state with default message', () => {
    render(<SessionList sessions={[]} />, { wrapper: RouterWrapper })

    expect(screen.getByText('No sessions found.')).toBeInTheDocument()
  })

  it('renders empty state with custom message', () => {
    render(
      <SessionList sessions={[]} emptyMessage="Start your first session!" />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('Start your first session!')).toBeInTheDocument()
  })

  it('renders list of sessions', () => {
    render(
      <SessionList sessions={[mockSession, mockCompletedSession]} />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('Test Feature')).toBeInTheDocument()
    expect(screen.getByText('Completed Feature')).toBeInTheDocument()
  })

  it('passes onSelect to SessionCards', async () => {
    const onSelect = vi.fn()
    const user = userEvent.setup()

    render(
      <SessionList sessions={[mockSession]} onSelect={onSelect} />,
      { wrapper: RouterWrapper }
    )

    await user.click(screen.getByText(/View Details/))

    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('passes onComplete to SessionCards', async () => {
    const onComplete = vi.fn()
    const user = userEvent.setup()

    render(
      <SessionList sessions={[mockSession]} onComplete={onComplete} />,
      { wrapper: RouterWrapper }
    )

    await user.click(screen.getByText('Complete'))

    expect(onComplete).toHaveBeenCalledWith(1)
  })
})

describe('SessionDetail component', () => {
  it('renders loading state', () => {
    render(<SessionDetail session={null} decisions={[]} loading={true} />, { wrapper: RouterWrapper })

    expect(screen.getByText('Loading session...')).toBeInTheDocument()
  })

  it('renders not found state when session is null', () => {
    render(<SessionDetail session={null} decisions={[]} loading={false} />, { wrapper: RouterWrapper })

    expect(screen.getByText('Session not found')).toBeInTheDocument()
  })

  it('renders session details correctly', () => {
    render(
      <SessionDetail session={mockSession} decisions={[]} loading={false} />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('Test Feature')).toBeInTheDocument()
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('renders decisions list', () => {
    render(
      <SessionDetail session={mockSession} decisions={[mockDecision]} loading={false} />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('Use React Query for state management')).toBeInTheDocument()
    expect(screen.getByText('architecture')).toBeInTheDocument()
    expect(screen.getByText('high')).toBeInTheDocument()
  })

  it('shows empty decisions message when no decisions', () => {
    render(
      <SessionDetail session={mockSession} decisions={[]} loading={false} />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('No decisions recorded yet.')).toBeInTheDocument()
  })

  it('calls onAddDecision when form submitted', async () => {
    const onAddDecision = vi.fn()
    const user = userEvent.setup()

    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        loading={false}
        onAddDecision={onAddDecision}
      />,
      { wrapper: RouterWrapper }
    )

    await user.type(screen.getByPlaceholderText('Enter decision...'), 'New decision text')
    await user.click(screen.getByText('Add Decision'))

    expect(onAddDecision).toHaveBeenCalledWith('New decision text', undefined, 'high')
  })

  it('calls onComplete when complete button clicked', async () => {
    const onComplete = vi.fn()
    const user = userEvent.setup()

    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        loading={false}
        onComplete={onComplete}
      />,
      { wrapper: RouterWrapper }
    )

    await user.click(screen.getByRole('button', { name: /complete session/i }))

    expect(onComplete).toHaveBeenCalled()
  })

  it('hides complete button for completed sessions', () => {
    render(
      <SessionDetail
        session={mockCompletedSession}
        decisions={[]}
        loading={false}
        onComplete={vi.fn()}
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.queryByRole('button', { name: /complete session/i })).not.toBeInTheDocument()
  })

  it('displays completed session duration', () => {
    render(
      <SessionDetail session={mockCompletedSession} decisions={[]} loading={false} />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText(/Duration:/)).toBeInTheDocument()
    expect(screen.getByText(/2h 30m/)).toBeInTheDocument()
  })

  it('calls onBack when back button clicked', async () => {
    const onBack = vi.fn()
    const user = userEvent.setup()

    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        loading={false}
        onBack={onBack}
      />,
      { wrapper: RouterWrapper }
    )

    await user.click(screen.getByText(/back/i))

    expect(onBack).toHaveBeenCalled()
  })

  it('renders agent tasks section', () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[mockAgentTask]}
        loading={false}
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('Agent Tasks')).toBeInTheDocument()
    expect(screen.getByText('Architect')).toBeInTheDocument()
    expect(screen.getByText('Design system architecture')).toBeInTheDocument()
    expect(screen.getByText('completed')).toBeInTheDocument()
  })

  it('displays task duration for completed tasks', () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[mockAgentTask]}
        loading={false}
      />,
      { wrapper: RouterWrapper }
    )

    // Session header has "Duration: In progress", task has "Duration: 30m 0s"
    const durationElements = screen.getAllByText(/Duration:/)
    expect(durationElements.length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText(/30m 0s/)).toBeInTheDocument()
  })

  it('shows empty tasks message when no tasks', () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[]}
        loading={false}
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('No agent tasks recorded yet.')).toBeInTheDocument()
  })

  it('displays running task status', () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[mockRunningTask]}
        loading={false}
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('Frontend Dev')).toBeInTheDocument()
    expect(screen.getByText('running')).toBeInTheDocument()
  })

  it('displays error message for failed tasks', () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[mockFailedTask]}
        loading={false}
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('failed')).toBeInTheDocument()
    expect(screen.getByText(/Connection timeout/)).toBeInTheDocument()
  })

  it('renders multiple agent tasks', () => {
    render(
      <SessionDetail
        session={mockSession}
        decisions={[]}
        tasks={[mockAgentTask, mockRunningTask, mockFailedTask]}
        loading={false}
      />,
      { wrapper: RouterWrapper }
    )

    expect(screen.getByText('Architect')).toBeInTheDocument()
    expect(screen.getByText('Frontend Dev')).toBeInTheDocument()
    expect(screen.getByText('Backend Dev')).toBeInTheDocument()
  })
})
