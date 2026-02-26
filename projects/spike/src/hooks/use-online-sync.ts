'use client';

import { useEffect, useRef } from 'react';
import { getPendingSpikes, clearPendingSpike } from '@/lib/offline-queue';

export function useOnlineSync() {
  const syncingRef = useRef(false);

  useEffect(() => {
    async function sync() {
      if (syncingRef.current) return;
      syncingRef.current = true;

      try {
        const pending = await getPendingSpikes();
        if (pending.length === 0) return;

        let synced = 0;
        for (const spike of pending) {
          try {
            const res = await fetch('/api/spikes', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                type: spike.type,
                intensity: spike.intensity,
                logged_at: spike.logged_at,
              }),
            });

            if (res.ok && spike.id) {
              await clearPendingSpike(spike.id);
              synced++;
            }
          } catch {
            break;
          }
        }

        if (synced > 0) {
          console.log(`Synced ${synced} offline spike(s)`);
        }
      } catch (err) {
        console.error('Offline sync failed:', err);
      } finally {
        syncingRef.current = false;
      }
    }

    sync();
    window.addEventListener('online', sync);
    const interval = setInterval(() => {
      if (navigator.onLine) sync();
    }, 30000);

    return () => {
      window.removeEventListener('online', sync);
      clearInterval(interval);
    };
  }, []);
}
