'use client';

import { useEffect, useRef } from 'react';
import { createClient } from '@/lib/supabase/client';
import { syncPendingSpikes, getPendingSpikes } from '@/lib/offline-queue';

export function useOnlineSync() {
  const syncingRef = useRef(false);

  useEffect(() => {
    async function sync() {
      if (syncingRef.current) return;
      syncingRef.current = true;

      try {
        const pending = await getPendingSpikes();
        if (pending.length === 0) return;

        const supabase = createClient();
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const synced = await syncPendingSpikes(supabase, user.id);
        if (synced > 0) {
          console.log(`Synced ${synced} offline spike(s)`);
        }
      } catch (err) {
        console.error('Offline sync failed:', err);
      } finally {
        syncingRef.current = false;
      }
    }

    // Sync on mount
    sync();

    // Sync when coming back online
    window.addEventListener('online', sync);
    // Also sync periodically when online
    const interval = setInterval(() => {
      if (navigator.onLine) sync();
    }, 30000);

    return () => {
      window.removeEventListener('online', sync);
      clearInterval(interval);
    };
  }, []);
}
