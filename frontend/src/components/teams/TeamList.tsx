import { TeamCard } from './TeamCard'
import type { Team } from '../../hooks/useTeams'

interface TeamListProps {
  teams: Team[]
  loading?: boolean
  error?: string | null
  onDelete?: (id: number) => void
  emptyMessage?: string
}

export function TeamList({
  teams,
  loading = false,
  error = null,
  onDelete,
  emptyMessage = 'No teams found.',
}: TeamListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading teams...</div>
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

  if (teams.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {teams.map(team => (
        <TeamCard key={team.id} team={team} onDelete={onDelete} />
      ))}
    </div>
  )
}
