import { SessionCard } from './SessionCard'
import type { Session } from '../../hooks/useSessions'

interface SessionListProps {
  sessions: Session[]
  loading?: boolean
  error?: string | null
  onSelect?: (id: number) => void
  onComplete?: (id: number) => void
  emptyMessage?: string
}

export function SessionList({
  sessions,
  loading = false,
  error = null,
  onSelect,
  onComplete,
  emptyMessage = 'No sessions found.',
}: SessionListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading sessions...</div>
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

  if (sessions.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {sessions.map(session => (
        <SessionCard
          key={session.id}
          session={session}
          onSelect={onSelect}
          onComplete={onComplete}
        />
      ))}
    </div>
  )
}
