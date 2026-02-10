import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'

export interface Team {
  id: number
  name: string
  description?: string
  is_shared: boolean
  owner_id: number
  created_at?: string
}

export interface TeamStats {
  total_sessions: number
  active_sessions: number
  total_members: number
  storage_used_mb: number
}

export function useTeams() {
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTeams = useCallback(async () => {
    try {
      setLoading(true)
      const res = await api.get('/teams')
      setTeams(res.data)
      setError(null)
    } catch (err) {
      setError('Failed to load teams')
    } finally {
      setLoading(false)
    }
  }, [])

  const createTeam = async (name: string, description?: string) => {
    const res = await api.post('/teams', { name, description })
    setTeams([...teams, res.data])
    return res.data
  }

  const deleteTeam = async (teamId: number) => {
    await api.delete(`/teams/${teamId}`)
    setTeams(teams.filter(t => t.id !== teamId))
  }

  useEffect(() => {
    fetchTeams()
  }, [fetchTeams])

  return { teams, loading, error, createTeam, deleteTeam, refetch: fetchTeams }
}

export function useTeamStats(teamId: number | null) {
  const [stats, setStats] = useState<TeamStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    if (teamId === null) return

    try {
      setLoading(true)
      const res = await api.get(`/dashboard/teams/${teamId}/stats`)
      setStats(res.data)
      setError(null)
    } catch (err) {
      setError('Failed to load team stats')
    } finally {
      setLoading(false)
    }
  }, [teamId])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return { stats, loading, error, refetch: fetchStats }
}
