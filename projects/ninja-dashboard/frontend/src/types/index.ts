export type JobStatus =
  | 'pending'
  | 'script_ready'
  | 'generating'
  | 'ready_for_review'
  | 'approved'
  | 'discarded'
  | 'error';

export interface Job {
  id: string;
  type: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  script_text: string | null;
  article_url: string | null;
  output_path: string | null;
  thumb_path: string | null;
  error_msg: string | null;
  retry_count: number;
  target_length_sec: number;
  broll_count: number;
  broll_duration: number;
}

export interface WSMessage {
  type: 'job_list' | 'job_created' | 'job_updated';
  data: Job | Job[];
}

// B-roll Wingman types
export type BrollSessionStatus = 'extracting' | 'searching' | 'presenting' | 'completed' | 'failed';
export type BrollSlotStatus = 'searching' | 'candidates_ready' | 'approved' | 'skipped';
export type BrollDownloadStatus = 'pending' | 'downloading' | 'ready' | 'failed';

export interface BrollCandidate {
  id: string;
  slot_id: string;
  source: 'pexels' | 'youtube' | 'local';
  source_url: string | null;
  title: string | null;
  preview_url: string | null;
  duration_sec: number | null;
  download_status: BrollDownloadStatus;
  local_path: string | null;
  file_size_mb: number | null;
  created_at: string;
}

export interface BrollSlot {
  id: string;
  session_id: string;
  slot_index: number;
  keyword: string;
  sentence: string | null;
  position: number;
  status: BrollSlotStatus;
  approved_candidate_id: string | null;
  candidates: BrollCandidate[];
  created_at: string;
}

export interface BrollSession {
  id: string;
  job_id: string;
  script_text: string;
  status: BrollSessionStatus;
  slot_count: number;
  slots: BrollSlot[];
  created_at: string;
  updated_at: string;
}
