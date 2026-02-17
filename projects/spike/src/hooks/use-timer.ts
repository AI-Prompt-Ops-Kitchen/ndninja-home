'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { createClient } from '@/lib/supabase/client';

const MAX_DURATION = 600; // 10 minutes

interface UseTimerOptions {
  spikeId: string | null;
  onComplete?: (durationSeconds: number) => void;
}

export function useTimer({ spikeId, onComplete }: UseTimerOptions) {
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const start = useCallback(() => {
    startTimeRef.current = Date.now();
    setElapsed(0);
    setRunning(true);
  }, []);

  const stop = useCallback(async () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    const duration = Math.round((Date.now() - startTimeRef.current) / 1000);
    setRunning(false);

    // Save duration to spike
    if (spikeId && duration > 0) {
      try {
        const supabase = createClient();
        await supabase
          .from('spikes')
          .update({ duration_seconds: duration })
          .eq('id', spikeId);

        // Also save timer session
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
          const now = new Date();
          await supabase.from('timer_sessions').insert({
            user_id: user.id,
            spike_id: spikeId,
            started_at: new Date(now.getTime() - duration * 1000).toISOString(),
            stopped_at: now.toISOString(),
          });
        }
      } catch (err) {
        console.error('Failed to save timer:', err);
      }
    }

    onComplete?.(duration);
  }, [spikeId, onComplete]);

  const dismiss = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setRunning(false);
    setElapsed(0);
  }, []);

  // Tick
  useEffect(() => {
    if (!running) return;

    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const secs = Math.round((now - startTimeRef.current) / 1000);
      setElapsed(secs);

      // Auto-stop at max duration
      if (secs >= MAX_DURATION) {
        stop();
      }
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [running, stop]);

  return { running, elapsed, start, stop, dismiss };
}
