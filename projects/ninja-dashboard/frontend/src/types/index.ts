export type JobStatus =
  | 'pending'
  | 'script_ready'
  | 'generating'
  | 'ready_for_review'
  | 'approved'
  | 'uploading'
  | 'uploaded'
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
  youtube_video_id: string | null;
  youtube_title: string | null;
  youtube_privacy: string | null;
  dual_anchor: boolean;
}

export interface WSMessage {
  type: 'job_list' | 'job_created' | 'job_updated' | 'job_deleted'
    | 'summon_list' | 'summon_appeared' | 'summon_updated' | 'summon_dismissed';
  data: Job | Job[] | unknown;
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

// B-roll Library types
export interface LibraryClip {
  id: string;
  filename: string;
  filepath: string;
  file_size_mb: number | null;
  duration_sec: number | null;
  width: number | null;
  height: number | null;
  codec: string | null;
  source: string;
  source_url: string | null;
  game: string | null;
  tags: string[];
  permanent: boolean;
  thumb_path: string | null;
  preview_path: string | null;
  deleted_at: string | null;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

export interface LibraryListResponse {
  items: LibraryClip[];
  total: number;
  page: number;
  per_page: number;
}

export interface TagCount {
  tag: string;
  count: number;
}

export interface GameCount {
  game: string;
  count: number;
}

// Thumbnail Studio types
export interface ThumbnailItem {
  filename: string;
  size_kb: number;
  created_at: string;
  path: string;
}

export interface ThumbnailGeneration {
  id: string;
  status: 'queued' | 'generating' | 'ready' | 'error';
  topic: string;
  style: string;
  aspect_ratio: string;
  filename?: string;
  error?: string;
}
