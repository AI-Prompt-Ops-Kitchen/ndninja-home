import { createContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import api, { tokenStorage } from '../api/client'

interface User {
  id: number
  username: string
  email: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  signup: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is already logged in (has valid token)
    const token = tokenStorage.getAccessToken()
    if (token) {
      api.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          // Token invalid or expired, clear it
          tokenStorage.clearTokens()
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const res = await api.post('/auth/login', { username, password })
    const { user: userData, tokens } = res.data
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    setUser(userData)
  }

  const signup = async (username: string, email: string, password: string) => {
    const res = await api.post('/auth/signup', { username, email, password })
    const { user: userData, tokens } = res.data
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    setUser(userData)
  }

  const logout = () => {
    tokenStorage.clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
