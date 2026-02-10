import { Link } from 'react-router-dom'
import type { Team } from '../../hooks/useTeams'

interface TeamCardProps {
  team: Team
  onDelete?: (id: number) => void
}

export function TeamCard({ team, onDelete }: TeamCardProps) {
  const handleDelete = () => {
    if (onDelete && window.confirm(`Are you sure you want to delete "${team.name}"?`)) {
      onDelete(team.id)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{team.name}</h3>
          {team.description && (
            <p className="text-sm text-gray-500 mt-1">{team.description}</p>
          )}
          <span
            className={`inline-block text-xs px-2 py-1 rounded mt-2 ${
              team.is_shared
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {team.is_shared ? 'Shared' : 'Personal'}
          </span>
        </div>
        {onDelete && (
          <button
            onClick={handleDelete}
            className="text-red-500 hover:text-red-700 text-sm font-medium transition-colors"
            aria-label={`Delete ${team.name}`}
          >
            Delete
          </button>
        )}
      </div>
      <Link
        to={`/teams/${team.id}`}
        className="mt-4 block text-blue-500 hover:text-blue-600 hover:underline text-sm font-medium"
      >
        View Team &rarr;
      </Link>
    </div>
  )
}
