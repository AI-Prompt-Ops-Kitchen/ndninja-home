import { useState, useEffect, useCallback } from 'react';
import type { BrollSession, BrollSlot, BrollCandidate } from '../types';
import { api } from '../lib/api';
import { wsEventBus } from './useWebSocket';

export function useBrollWingman(jobId: string | null) {
  const [session, setSession] = useState<BrollSession | null>(null);
  const [loading, setLoading] = useState(false);

  // Initial fetch
  useEffect(() => {
    if (!jobId) {
      setSession(null);
      return;
    }
    setLoading(true);
    api.getBrollSession(jobId)
      .then(({ session }) => setSession(session))
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  }, [jobId]);

  // WS event subscriptions
  useEffect(() => {
    if (!jobId) return;

    const unsubs = [
      wsEventBus.subscribe('broll_session_started', (data) => {
        const d = data as { job_id: string; session_id: string; status: string };
        if (d.job_id !== jobId) return;
        setSession(prev => prev
          ? { ...prev, status: d.status as BrollSession['status'] }
          : { id: d.session_id, job_id: d.job_id, script_text: '', status: 'extracting', slot_count: 3, slots: [], created_at: '', updated_at: '' }
        );
      }),

      wsEventBus.subscribe('broll_slots_ready', (data) => {
        const d = data as { job_id: string; session_id: string; slots: BrollSlot[] };
        if (d.job_id !== jobId) return;
        setSession(prev => prev ? {
          ...prev,
          status: 'searching',
          slots: d.slots.map(s => ({ ...s, candidates: s.candidates || [] })),
        } : prev);
      }),

      wsEventBus.subscribe('broll_candidate_found', (data) => {
        const d = data as { job_id: string; slot_id: string; candidates: BrollCandidate[] };
        if (d.job_id !== jobId) return;
        setSession(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            slots: prev.slots.map(s =>
              s.id === d.slot_id
                ? { ...s, status: 'candidates_ready' as const, candidates: [...s.candidates, ...d.candidates] }
                : s
            ),
          };
        });
      }),

      wsEventBus.subscribe('broll_session_updated', (data) => {
        const d = data as { job_id: string; session?: BrollSession; error?: string };
        if (d.job_id !== jobId) return;
        if (d.session) setSession(d.session);
        else if (d.error) setSession(prev => prev ? { ...prev, status: 'failed' } : prev);
      }),

      wsEventBus.subscribe('broll_slot_approved', (data) => {
        const d = data as { slot_id: string; candidate_id: string };
        setSession(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            slots: prev.slots.map(s =>
              s.id === d.slot_id
                ? { ...s, status: 'approved' as const, approved_candidate_id: d.candidate_id }
                : s
            ),
          };
        });
      }),

      wsEventBus.subscribe('broll_slot_skipped', (data) => {
        const d = data as { slot_id: string };
        setSession(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            slots: prev.slots.map(s =>
              s.id === d.slot_id ? { ...s, status: 'skipped' as const } : s
            ),
          };
        });
      }),

      wsEventBus.subscribe('broll_candidate_ready', (data) => {
        const d = data as { candidate_id: string; slot_id: string; local_path: string };
        setSession(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            slots: prev.slots.map(s =>
              s.id === d.slot_id
                ? {
                    ...s,
                    candidates: s.candidates.map(c =>
                      c.id === d.candidate_id
                        ? { ...c, download_status: 'ready' as const, local_path: d.local_path }
                        : c
                    ),
                  }
                : s
            ),
          };
        });
      }),

      wsEventBus.subscribe('broll_download_failed', (data) => {
        const d = data as { slot_id: string; candidate_id: string };
        setSession(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            slots: prev.slots.map(s =>
              s.id === d.slot_id
                ? {
                    ...s,
                    status: 'candidates_ready' as const,
                    approved_candidate_id: null,
                    candidates: s.candidates.map(c =>
                      c.id === d.candidate_id
                        ? { ...c, download_status: 'failed' as const }
                        : c
                    ),
                  }
                : s
            ),
          };
        });
      }),

      wsEventBus.subscribe('broll_session_completed', (data) => {
        const d = data as { job_id: string; session_id: string };
        if (d.job_id !== jobId) return;
        setSession(prev => prev ? { ...prev, status: 'completed' } : prev);
      }),
    ];

    return () => unsubs.forEach(u => u());
  }, [jobId]);

  const approveSlot = useCallback(async (slotId: string, candidateId: string) => {
    await api.approveBrollSlot(slotId, candidateId);
  }, []);

  const skipSlot = useCallback(async (slotId: string) => {
    await api.skipBrollSlot(slotId);
  }, []);

  const assignLocal = useCallback(async (slotId: string, filename: string) => {
    await api.assignLocalBroll(slotId, filename);
  }, []);

  const startDiscovery = useCallback(async () => {
    if (jobId) await api.startBrollDiscovery(jobId);
  }, [jobId]);

  const resolvedCount = session?.slots.filter(s => s.status === 'approved' || s.status === 'skipped').length ?? 0;
  const totalSlots = session?.slots.length ?? 0;

  return {
    session,
    loading,
    approveSlot,
    skipSlot,
    assignLocal,
    startDiscovery,
    resolvedCount,
    totalSlots,
  };
}
