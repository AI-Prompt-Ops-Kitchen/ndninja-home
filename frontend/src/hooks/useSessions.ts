import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'

export interface Session {
  id: number
  team_id: number
  user_id: number
  feature_name: string
  status: string
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
}

export interface SessionDecision {
  id: number
  session_id: number
  decision_text: string
  category: string | null
  confidence: string
  created_at: string
}

export interface AgentTask {
  id: number
  session_id: number
  agent_role: string
  task_description: string
  status: string
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  error_message: string | null
  created_at: string
}

export function useSessions(teamId?: number) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true)
      const params = teamId ? { params: { team_id: teamId } } : undefined
      const res = teamId
        ? await api.get('/sessions', params)
        : await api.get('/sessions')
      setSessions(res.data)
      setError(null)
    } catch (err) {
      setError('Failed to load sessions')
      setSessions([])
    } finally {
      setLoading(false)
    }
  }, [teamId])

  const startSession = async (teamId: number, featureName: string) => {
    const res = await api.post('/sessions', {
      team_id: teamId,
      feature_name: featureName,
    })
    setSessions([...sessions, res.data])
    return res.data
  }

  const completeSession = async (sessionId: number) => {
    const res = await api.put(`/sessions/${sessionId}/complete`)
    setSessions(sessions.map(s =>
      s.id === sessionId ? res.data : s
    ))
    return res.data
  }

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  return {
    sessions,
    loading,
    error,
    startSession,
    completeSession,
    refetch: fetchSessions
  }
}

export function useSessionDetail(sessionId: number | null) {
  const [session, setSession] = useState<Session | null>(null)
  const [decisions, setDecisions] = useState<SessionDecision[]>([])
  const [tasks, setTasks] = useState<AgentTask[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSessionDetail = useCallback(async () => {
    if (sessionId === null) return

    try {
      setLoading(true)
      const [sessionRes, decisionsRes, tasksRes] = await Promise.all([
        api.get(`/sessions/${sessionId}`),
        api.get(`/sessions/${sessionId}/decisions`),
        api.get(`/sessions/${sessionId}/tasks`),
      ])
      setSession(sessionRes.data)
      setDecisions(decisionsRes.data)
      setTasks(tasksRes.data)
      setError(null)
    } catch (err) {
      setError('Failed to load session details')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  const addDecision = async (
    decisionText: string,
    category?: string,
    confidence: string = 'high'
  ) => {
    if (sessionId === null) return

    const res = await api.post(`/sessions/${sessionId}/decisions`, {
      decision_text: decisionText,
      category,
      confidence,
    })
    setDecisions([...decisions, res.data])
    return res.data
  }

  useEffect(() => {
    fetchSessionDetail()
  }, [fetchSessionDetail])

  return {
    session,
    decisions,
    tasks,
    loading,
    error,
    addDecision,
    refetch: fetchSessionDetail
  }
}
