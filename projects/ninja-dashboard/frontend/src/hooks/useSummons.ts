import { useState, useCallback, useEffect } from 'react';
import type { Summon } from '../types/summon';
import { api } from '../lib/api';
import { useWebSocket, wsEventBus } from './useWebSocket';

export function useSummons() {
  const [summons, setSummons] = useState<Summon[]>([]);

  const refresh = useCallback(async () => {
    try {
      const data = await api.getSummons();
      setSummons(data);
    } catch {
      /* endpoint may not exist yet — silent */
    }
  }, []);

  // Keep singleton WS alive
  useWebSocket();

  useEffect(() => {
    const unsubs = [
      wsEventBus.subscribe('summon_list', (data) => {
        setSummons(data as Summon[]);
      }),
      wsEventBus.subscribe('summon_appeared', (data) => {
        setSummons(prev => {
          const summon = data as Summon;
          const idx = prev.findIndex(s => s.summon_id === summon.summon_id);
          if (idx === -1) return [...prev, summon];
          const next = [...prev];
          next[idx] = summon;
          return next;
        });
      }),
      wsEventBus.subscribe('summon_updated', (data) => {
        setSummons(prev => {
          const summon = data as Summon;
          const idx = prev.findIndex(s => s.summon_id === summon.summon_id);
          if (idx === -1) return [...prev, summon];
          const next = [...prev];
          next[idx] = summon;
          return next;
        });
      }),
      wsEventBus.subscribe('summon_dismissed', (data) => {
        const summon = data as Summon;
        // Mark as done immediately for exit animation
        setSummons(prev =>
          prev.map(s =>
            s.summon_id === summon.summon_id ? { ...s, status: 'done' as const } : s,
          ),
        );
        // Remove after exit animation completes
        setTimeout(() => {
          setSummons(prev => prev.filter(s => s.summon_id !== summon.summon_id));
        }, 5000);
      }),
    ];

    refresh();
    return () => unsubs.forEach(u => u());
  }, [refresh]);

  const activeSummons = summons.filter(s => s.status !== 'done');

  return { summons, activeSummons };
}
