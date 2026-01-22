import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSessions, useSessionDetail } from '../hooks/useSessions'
import { useTeams } from '../hooks/useTeams'
import { useAuth } from '../hooks/useAuth'
import { SessionList, SessionDetail } from '../components/sessions'
import { StatsCard, StatsGrid } from '../components/dashboard/StatsCard'

type StatusFilter = 'all' | 'active' | 'completed' | 'paused'

export function SessionsPage() {
  const { user, logout } = useAuth()
  const { teams, loading: teamsLoading } = useTeams()
  const [selectedTeamId, setSelectedTeamId] = useState<number | undefined>(undefined)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null)

  const { sessions, loading, error, startSession, completeSession, refetch } = useSessions(selectedTeamId)
  const {
    session: sessionDetail,
    decisions,
    tasks,
    loading: detailLoading,
    addDecision,
  } = useSessionDetail(selectedSessionId)

  // Filter sessions by status
  const filteredSessions = statusFilter === 'all'
    ? sessions
    : sessions.filter(s => s.status === statusFilter)

  // Calculate stats
  const totalSessions = sessions.length
  const activeSessions = sessions.filter(s => s.status === 'active').length
  const completedSessions = sessions.filter(s => s.status === 'completed').length

  const handleStartSession = async () => {
    if (!selectedTeamId) {
      alert('Please select a team first')
      return
    }
    const featureName = prompt('Enter feature name:')
    if (featureName) {
      try {
        await startSession(selectedTeamId, featureName)
      } catch (err) {
        console.error('Failed to start session:', err)
      }
    }
  }

  const handleCompleteSession = async (sessionId: number) => {
    try {
      await completeSession(sessionId)
    } catch (err) {
      console.error('Failed to complete session:', err)
    }
  }

  const handleSelectSession = (sessionId: number) => {
    setSelectedSessionId(sessionId)
  }

  const handleBackToList = () => {
    setSelectedSessionId(null)
  }

  const handleAddDecision = async (text: string, category?: string, confidence?: string) => {
    try {
      await addDecision(text, category, confidence)
    } catch (err) {
      console.error('Failed to add decision:', err)
    }
  }

  const handleCompleteCurrentSession = async () => {
    if (selectedSessionId) {
      await handleCompleteSession(selectedSessionId)
    }
  }

  // If a session is selected, show the detail view
  if (selectedSessionId) {
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
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Teams
                  </Link>
                  <Link
                    to="/sessions"
                    className="text-blue-600 hover:text-blue-800 px-3 py-2 rounded-md text-sm font-medium border-b-2 border-blue-500"
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

        {/* Session Detail */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <SessionDetail
            session={sessionDetail}
            decisions={decisions}
            tasks={tasks}
            loading={detailLoading}
            onBack={handleBackToList}
            onAddDecision={handleAddDecision}
            onComplete={handleCompleteCurrentSession}
          />
        </main>
      </div>
    )
  }

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
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Teams
                </Link>
                <Link
                  to="/sessions"
                  className="text-blue-600 hover:text-blue-800 px-3 py-2 rounded-md text-sm font-medium border-b-2 border-blue-500"
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
              title="Total Sessions"
              value={totalSessions}
              loading={loading}
              description="All sessions"
            />
            <StatsCard
              title="Active Sessions"
              value={activeSessions}
              loading={loading}
              description="Currently running"
            />
            <StatsCard
              title="Completed Sessions"
              value={completedSessions}
              loading={loading}
              description="Finished sessions"
            />
          </StatsGrid>
        </section>

        {/* Filters Section */}
        <section className="mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Team Filter */}
            <div>
              <label htmlFor="team-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Team
              </label>
              <select
                id="team-filter"
                value={selectedTeamId || ''}
                onChange={(e) => setSelectedTeamId(e.target.value ? Number(e.target.value) : undefined)}
                className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={teamsLoading}
              >
                <option value="">All Teams</option>
                {teams.map(team => (
                  <option key={team.id} value={team.id}>{team.name}</option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="paused">Paused</option>
              </select>
            </div>
          </div>
        </section>

        {/* Sessions Section */}
        <section>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Sessions
              {filteredSessions.length !== sessions.length && (
                <span className="text-sm font-normal text-gray-500 ml-2">
                  (showing {filteredSessions.length} of {sessions.length})
                </span>
              )}
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={() => refetch()}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                Refresh
              </button>
              <button
                onClick={handleStartSession}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
              >
                + Start Session
              </button>
            </div>
          </div>

          <SessionList
            sessions={filteredSessions}
            loading={loading}
            error={error}
            onSelect={handleSelectSession}
            onComplete={handleCompleteSession}
            emptyMessage={
              statusFilter !== 'all'
                ? `No ${statusFilter} sessions found.`
                : "You don't have any sessions yet. Start one to begin tracking your work!"
            }
          />
        </section>
      </main>
    </div>
  )
}
