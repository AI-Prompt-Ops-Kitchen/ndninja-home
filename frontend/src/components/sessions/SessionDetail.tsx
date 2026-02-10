import { useState } from 'react'
import type { Session, SessionDecision, AgentTask } from '../../hooks/useSessions'
import type { ConnectionStatus } from '../../hooks/useWebSocket'

interface SessionDetailProps {
  session: Session | null
  decisions: SessionDecision[]
  tasks?: AgentTask[]
  loading: boolean
  error?: string | null
  onAddDecision?: (text: string, category?: string, confidence?: string) => void
  onComplete?: () => void
  onBack?: () => void
  /** WebSocket connection status for real-time updates */
  connectionStatus?: ConnectionStatus
  /** Callback when a task should be updated from WebSocket message */
  onTaskUpdate?: (taskId: number, status: string) => void
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return 'In progress'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatTaskDuration(seconds: number | null): string {
  if (seconds === null) return '-'
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

/**
 * Connection status indicator component
 */
function ConnectionStatusIndicator({ status }: { status: ConnectionStatus }) {
  const statusConfig: Record<ConnectionStatus, { label: string; dotClass: string; textClass: string }> = {
    connected: {
      label: 'Connected',
      dotClass: 'bg-green-500',
      textClass: 'text-green-700',
    },
    connecting: {
      label: 'Connecting',
      dotClass: 'bg-yellow-500 animate-pulse',
      textClass: 'text-yellow-700',
    },
    disconnected: {
      label: 'Disconnected',
      dotClass: 'bg-gray-400',
      textClass: 'text-gray-600',
    },
    reconnecting: {
      label: 'Reconnecting',
      dotClass: 'bg-yellow-500 animate-pulse',
      textClass: 'text-yellow-700',
    },
    error: {
      label: 'Error',
      dotClass: 'bg-red-500',
      textClass: 'text-red-700',
    },
  }

  const config = statusConfig[status]

  return (
    <div
      data-testid="connection-status"
      className="flex items-center gap-2 text-sm"
    >
      <span className={`w-2 h-2 rounded-full ${config.dotClass}`} />
      <span className={config.textClass}>{config.label}</span>
    </div>
  )
}

export function SessionDetail({
  session,
  decisions,
  tasks = [],
  loading,
  error,
  onAddDecision,
  onComplete,
  onBack,
  connectionStatus,
  onTaskUpdate: _onTaskUpdate,
}: SessionDetailProps) {
  // Note: onTaskUpdate is available for parent components to pass, but task updates
  // are typically handled by the parent via the useWebSocket hook's lastMessage
  const [decisionText, setDecisionText] = useState('')
  const [category, setCategory] = useState('')
  const [confidence, setConfidence] = useState('high')

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading session...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-700">{error}</p>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Session not found</p>
      </div>
    )
  }

  const handleAddDecision = (e: React.FormEvent) => {
    e.preventDefault()
    if (onAddDecision && decisionText.trim()) {
      onAddDecision(decisionText.trim(), category || undefined, confidence)
      setDecisionText('')
      setCategory('')
      setConfidence('high')
    }
  }

  const statusClasses: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    completed: 'bg-blue-100 text-blue-800',
    paused: 'bg-yellow-100 text-yellow-800',
  }

  const statusClass = statusClasses[session.status] || 'bg-gray-100 text-gray-800'
  const isActive = session.status === 'active'

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <div>
            {onBack && (
              <button
                onClick={onBack}
                className="text-gray-500 hover:text-gray-700 text-sm mb-2 flex items-center"
              >
                &larr; Back to Sessions
              </button>
            )}
            <h2 className="text-2xl font-bold text-gray-900">{session.feature_name}</h2>
            <div className="mt-2 flex items-center gap-3">
              <span className={`inline-block text-sm px-3 py-1 rounded ${statusClass}`}>
                {session.status}
              </span>
              {/* Show connection status for active sessions */}
              {isActive && connectionStatus && (
                <ConnectionStatusIndicator status={connectionStatus} />
              )}
            </div>
          </div>
          {isActive && onComplete && (
            <button
              onClick={onComplete}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Complete Session
            </button>
          )}
        </div>

        {/* Session Info */}
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Started:</span> {formatDate(session.started_at)}
          </div>
          {session.ended_at && (
            <div>
              <span className="font-medium">Ended:</span> {formatDate(session.ended_at)}
            </div>
          )}
          <div>
            <span className="font-medium">Duration:</span> {formatDuration(session.duration_seconds)}
          </div>
        </div>
      </div>

      {/* Decisions Section */}
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Decisions</h3>

        {/* Add Decision Form */}
        {isActive && onAddDecision && (
          <form onSubmit={handleAddDecision} className="mb-6">
            <div className="flex gap-2">
              <input
                type="text"
                value={decisionText}
                onChange={(e) => setDecisionText(e.target.value)}
                placeholder="Enter decision..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Category</option>
                <option value="architecture">Architecture</option>
                <option value="design">Design</option>
                <option value="implementation">Implementation</option>
                <option value="testing">Testing</option>
              </select>
              <select
                value={confidence}
                onChange={(e) => setConfidence(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <button
                type="submit"
                disabled={!decisionText.trim()}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Add Decision
              </button>
            </div>
          </form>
        )}

        {/* Decisions List */}
        {decisions.length === 0 ? (
          <p className="text-gray-500">No decisions recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {decisions.map((decision) => (
              <div
                key={decision.id}
                className="p-4 bg-gray-50 rounded-lg border border-gray-200"
              >
                <p className="text-gray-900">{decision.decision_text}</p>
                <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
                  {decision.category && (
                    <span className="px-2 py-0.5 bg-gray-200 rounded">{decision.category}</span>
                  )}
                  <span className={`px-2 py-0.5 rounded ${
                    decision.confidence === 'high'
                      ? 'bg-green-100 text-green-700'
                      : decision.confidence === 'medium'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {decision.confidence}
                  </span>
                  <span>{formatDate(decision.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Agent Tasks Section */}
      <div className="p-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Tasks</h3>

        {tasks.length === 0 ? (
          <p className="text-gray-500">No agent tasks recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {tasks.map((task) => {
              const taskStatusClasses: Record<string, string> = {
                pending: 'bg-gray-100 text-gray-700',
                running: 'bg-blue-100 text-blue-700',
                completed: 'bg-green-100 text-green-700',
                failed: 'bg-red-100 text-red-700',
              }
              const taskStatusClass = taskStatusClasses[task.status] || 'bg-gray-100 text-gray-700'

              return (
                <div
                  key={task.id}
                  className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-medium text-gray-900">{task.agent_role}</span>
                      <p className="text-gray-700 mt-1">{task.task_description}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-sm ${taskStatusClass}`}>
                      {task.status}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                    {task.duration_seconds !== null && (
                      <span>
                        <span className="font-medium">Duration:</span> {formatTaskDuration(task.duration_seconds)}
                      </span>
                    )}
                    {task.error_message && (
                      <span className="text-red-600">
                        <span className="font-medium">Error:</span> {task.error_message}
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
