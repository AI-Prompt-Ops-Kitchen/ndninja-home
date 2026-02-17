export type SpikeType = 'anxiety' | 'sadness';

export interface Spike {
  id: string;
  user_id: string;
  type: SpikeType;
  intensity: number; // 1-5
  duration_seconds: number | null;
  notes: string | null;
  logged_at: string;
  created_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  doctor_email: string | null;
  timezone: string;
  daily_digest: boolean;
  weekly_digest: boolean;
  created_at: string;
  updated_at: string;
}

export interface TimerSession {
  id: string;
  user_id: string;
  spike_id: string | null;
  started_at: string;
  stopped_at: string | null;
}
