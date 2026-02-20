import { useState, useCallback, useEffect } from 'react';
import type { Job } from '../types';
import { api } from '../lib/api';
import { useWebSocket, wsEventBus } from './useWebSocket';

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await api.getJobs();
      setJobs(data);
    } finally {
      setLoading(false);
    }
  }, []);

  // Keep singleton WS alive
  useWebSocket();

  useEffect(() => {
    const unsubs = [
      wsEventBus.subscribe('job_list', (data) => {
        setJobs(data as Job[]);
        setLoading(false);
      }),
      wsEventBus.subscribe('job_created', (data) => {
        setJobs(prev => {
          const updated = data as Job;
          const idx = prev.findIndex(j => j.id === updated.id);
          if (idx === -1) return [updated, ...prev];
          const next = [...prev];
          next[idx] = updated;
          return next;
        });
      }),
      wsEventBus.subscribe('job_updated', (data) => {
        setJobs(prev => {
          const updated = data as Job;
          const idx = prev.findIndex(j => j.id === updated.id);
          if (idx === -1) return [updated, ...prev];
          const next = [...prev];
          next[idx] = updated;
          return next;
        });
      }),
      wsEventBus.subscribe('job_deleted', (data) => {
        const { id } = data as { id: string };
        setJobs(prev => prev.filter(j => j.id !== id));
      }),
    ];

    refresh();
    return () => unsubs.forEach(u => u());
  }, [refresh]);

  return { jobs, loading };
}
