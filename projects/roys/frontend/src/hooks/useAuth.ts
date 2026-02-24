import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import type { User } from '../types';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('roys_token');
    if (!token) {
      setLoading(false);
      return;
    }
    api.me().then(setUser).catch(() => {
      localStorage.removeItem('roys_token');
    }).finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password);
    localStorage.setItem('roys_token', access_token);
    const u = await api.me();
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('roys_token');
    setUser(null);
  }, []);

  return { user, loading, login, logout, isAdmin: user?.role === 'admin' };
}
