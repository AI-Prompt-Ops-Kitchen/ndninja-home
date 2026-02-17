'use client';

import { SpikeType } from '@/types/spike';

const DB_NAME = 'spike-offline';
const DB_VERSION = 1;
const STORE_NAME = 'pending-spikes';

export interface PendingSpike {
  id?: number; // IDB auto-increment key
  type: SpikeType;
  intensity: number;
  logged_at: string;
  created_at: string;
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueSpike(spike: Omit<PendingSpike, 'id'>): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).add(spike);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getPendingSpikes(): Promise<PendingSpike[]> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const request = tx.objectStore(STORE_NAME).getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function clearPendingSpike(id: number): Promise<void> {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function syncPendingSpikes(
  supabase: any,
  userId: string
): Promise<number> {
  const pending = await getPendingSpikes();
  if (pending.length === 0) return 0;

  let synced = 0;

  for (const spike of pending) {
    try {
      const { error } = await supabase.from('spikes').insert({
        user_id: userId,
        type: spike.type,
        intensity: spike.intensity,
        logged_at: spike.logged_at,
      });

      if (!error && spike.id) {
        await clearPendingSpike(spike.id);
        synced++;
      }
    } catch {
      // Stop syncing on error — will retry next time
      break;
    }
  }

  return synced;
}
