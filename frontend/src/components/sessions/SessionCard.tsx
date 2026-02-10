import type { Session } from '../../hooks/useSessions'

interface SessionCardProps {
  session: Session
  onSelect?: (id: number) => void
  onComplete?: (id: number) => void
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
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function SessionCard({ session, onSelect, onComplete }: SessionCardProps) {
  const handleComplete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onComplete) {
      onComplete(session.id)
    }
  }

  const handleSelect = () => {
    if (onSelect) {
      onSelect(session.id)
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
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{session.feature_name}</h3>
          <div className="mt-2 flex items-center gap-2">
            <span className={`inline-block text-xs px-2 py-1 rounded ${statusClass}`}>
              {session.status}
            </span>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            <p>Started: {formatDate(session.started_at)}</p>
            <p>Duration: {formatDuration(session.duration_seconds)}</p>
          </div>
        </div>
        {isActive && onComplete && (
          <button
            onClick={handleComplete}
            className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
          >
            Complete
          </button>
        )}
      </div>
      <button
        onClick={handleSelect}
        className="mt-4 block text-blue-500 hover:text-blue-600 hover:underline text-sm font-medium"
      >
        View Details &rarr;
      </button>
    </div>
  )
}
