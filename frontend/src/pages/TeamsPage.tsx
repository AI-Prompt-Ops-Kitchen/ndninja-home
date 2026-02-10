import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTeams } from '../hooks/useTeams'
import { useAuth } from '../hooks/useAuth'
import { TeamList } from '../components/teams/TeamList'
import { CreateTeamModal } from '../components/teams/CreateTeamModal'
import { StatsCard, StatsGrid } from '../components/dashboard/StatsCard'

export function TeamsPage() {
  const { user, logout } = useAuth()
  const { teams, loading, error, createTeam, deleteTeam, refetch } = useTeams()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  const handleCreateTeam = async (name: string, description?: string) => {
    await createTeam(name, description)
  }

  const handleDeleteTeam = async (teamId: number) => {
    try {
      await deleteTeam(teamId)
    } catch (err) {
      console.error('Failed to delete team:', err)
    }
  }

  // Calculate stats from teams data
  const totalTeams = teams.length
  const sharedTeams = teams.filter(t => t.is_shared).length
  const personalTeams = teams.filter(t => !t.is_shared).length

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-gray-900">Sage Mode</h1>
              <nav className="flex space-x-4">
                <Link
                  to="/"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/teams"
                  className="text-blue-600 hover:text-blue-800 px-3 py-2 rounded-md text-sm font-medium border-b-2 border-blue-500"
                >
                  Teams
                </Link>
                <Link
                  to="/sessions"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Sessions
                </Link>
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-gray-600 text-sm">
                Welcome, {user?.username}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Overview</h2>
          <StatsGrid columns={3}>
            <StatsCard
              title="Total Teams"
              value={totalTeams}
              loading={loading}
              description="All teams you belong to"
            />
            <StatsCard
              title="Shared Teams"
              value={sharedTeams}
              loading={loading}
              description="Collaborative teams"
            />
            <StatsCard
              title="Personal Teams"
              value={personalTeams}
              loading={loading}
              description="Your private teams"
            />
          </StatsGrid>
        </section>

        {/* Teams Section */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Your Teams</h2>
            <div className="flex space-x-2">
              <button
                onClick={() => refetch()}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                Refresh
              </button>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
              >
                + Create Team
              </button>
            </div>
          </div>

          <TeamList
            teams={teams}
            loading={loading}
            error={error}
            onDelete={handleDeleteTeam}
            emptyMessage="You don't have any teams yet. Create one to get started!"
          />
        </section>
      </main>

      {/* Create Team Modal */}
      <CreateTeamModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreate={handleCreateTeam}
      />
    </div>
  )
}
