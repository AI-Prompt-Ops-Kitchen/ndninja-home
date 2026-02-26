import type { Job, BrollSession, ThumbnailItem, LibraryListResponse, LibraryClip, TagCount, GameCount } from '../types';
import type { Summon } from '../types/summon';
import { basename } from './utils';

const BASE = '';

export const api = {
  async getJobs(): Promise<Job[]> {
    const r = await fetch(`${BASE}/api/jobs`);
    if (!r.ok) throw new Error(`getJobs: ${r.status}`);
    return r.json();
  },

  async submitArticle(payload: {
    url?: string;
    text?: string;
    target_length_sec?: number;
    broll_count?: number;
    broll_duration?: number;
    dual_anchor?: boolean;
  }): Promise<Job> {
    const r = await fetch(`${BASE}/api/jobs/article`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(`submitArticle: ${r.status}`);
    return r.json();
  },

  async editScript(id: string, script_text: string): Promise<Job> {
    const r = await fetch(`${BASE}/api/jobs/${id}/script-edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script_text }),
    });
    if (!r.ok) throw new Error(`editScript: ${r.status}`);
    return r.json();
  },

  async approveScript(id: string): Promise<Job> {
    const r = await fetch(`${BASE}/api/jobs/${id}/script-approve`, { method: 'POST' });
    if (!r.ok) throw new Error(`approveScript: ${r.status}`);
    return r.json();
  },

  async approveVideo(id: string): Promise<Job> {
    const r = await fetch(`${BASE}/api/jobs/${id}/approve`, { method: 'POST' });
    if (!r.ok) throw new Error(`approveVideo: ${r.status}`);
    return r.json();
  },

  async discardJob(id: string): Promise<Job> {
    const r = await fetch(`${BASE}/api/jobs/${id}/discard`, { method: 'POST' });
    if (!r.ok) throw new Error(`discardJob: ${r.status}`);
    return r.json();
  },

  async retryJob(id: string): Promise<Job> {
    const r = await fetch(`${BASE}/api/jobs/${id}/retry`, { method: 'POST' });
    if (!r.ok) throw new Error(`retryJob: ${r.status}`);
    return r.json();
  },

  async uploadToYouTube(id: string, payload: {
    title: string;
    description: string;
    tags: string[];
    privacy: 'private' | 'unlisted' | 'public';
  }): Promise<Job> {
    const r = await fetch(`${BASE}/api/jobs/${id}/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const text = await r.text();
      throw new Error(text || `uploadToYouTube: ${r.status}`);
    }
    return r.json();
  },

  async uploadFile(file: File): Promise<{ filename: string; path: string }> {
    const form = new FormData();
    form.append('file', file);
    const r = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form });
    if (!r.ok) throw new Error(`uploadFile: ${r.status}`);
    return r.json();
  },

  videoUrl(outputPath: string): string {
    return `${BASE}/api/video/${encodeURIComponent(basename(outputPath))}`;
  },

  thumbUrl(thumbPath: string): string {
    return `${BASE}/api/thumb/${encodeURIComponent(basename(thumbPath))}`;
  },

  downloadUrl(outputPath: string): string {
    return `${BASE}/api/download/${encodeURIComponent(basename(outputPath))}`;
  },

  // B-roll Wingman
  async getBrollSession(jobId: string): Promise<{ session: BrollSession | null }> {
    const r = await fetch(`${BASE}/api/broll-wingman/${jobId}`);
    if (!r.ok) throw new Error(`getBrollSession: ${r.status}`);
    return r.json();
  },

  async startBrollDiscovery(jobId: string): Promise<void> {
    const r = await fetch(`${BASE}/api/broll-wingman/${jobId}/start`, { method: 'POST' });
    if (!r.ok) throw new Error(`startBrollDiscovery: ${r.status}`);
  },

  async approveBrollSlot(slotId: string, candidateId: string): Promise<void> {
    const r = await fetch(`${BASE}/api/broll-wingman/slots/${slotId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_id: candidateId }),
    });
    if (!r.ok) throw new Error(`approveBrollSlot: ${r.status}`);
  },

  async skipBrollSlot(slotId: string): Promise<void> {
    const r = await fetch(`${BASE}/api/broll-wingman/slots/${slotId}/skip`, { method: 'POST' });
    if (!r.ok) throw new Error(`skipBrollSlot: ${r.status}`);
  },

  async assignLocalBroll(slotId: string, filename: string): Promise<{ approved: boolean; slot_id: string; candidate: any }> {
    const r = await fetch(`${BASE}/api/broll-wingman/slots/${slotId}/assign-local`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename }),
    });
    if (!r.ok) throw new Error(`assignLocalBroll: ${r.status}`);
    return r.json();
  },

  async listBroll(): Promise<{ filename: string; size_mb: number; modified: string }[]> {
    const r = await fetch(`${BASE}/api/broll`);
    if (!r.ok) throw new Error(`listBroll: ${r.status}`);
    return r.json();
  },

  brollPreviewUrl(candidateId: string): string {
    return `${BASE}/api/broll-wingman/preview/${candidateId}`;
  },

  async clipYoutube(payload: {
    url: string;
    start: string;
    end: string;
    filename?: string;
  }): Promise<{ filename: string; path: string; size_mb: number }> {
    const r = await fetch(`${BASE}/api/broll/clip-youtube`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const text = await r.text();
      throw new Error(text || `clipYoutube: ${r.status}`);
    }
    return r.json();
  },

  // Thumbnail Studio
  async generateThumbnail(payload: {
    topic: string;
    style?: string;
    aspect_ratio?: string;
    headline?: string;
  }): Promise<{ id: string; status: string }> {
    const r = await fetch(`${BASE}/api/thumbnail-studio/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(`generateThumbnail: ${r.status}`);
    return r.json();
  },

  async generateThumbnailFromImage(
    formData: FormData,
  ): Promise<{ id: string; status: string }> {
    const r = await fetch(`${BASE}/api/thumbnail-studio/generate-from-image`, {
      method: 'POST',
      body: formData,
    });
    if (!r.ok) throw new Error(`generateThumbnailFromImage: ${r.status}`);
    return r.json();
  },

  async getThumbnailGallery(): Promise<ThumbnailItem[]> {
    const r = await fetch(`${BASE}/api/thumbnail-studio/gallery`);
    if (!r.ok) throw new Error(`getThumbnailGallery: ${r.status}`);
    return r.json();
  },

  async deleteThumbnail(filename: string): Promise<void> {
    const r = await fetch(
      `${BASE}/api/thumbnail-studio/${encodeURIComponent(filename)}`,
      { method: 'DELETE' },
    );
    if (!r.ok) throw new Error(`deleteThumbnail: ${r.status}`);
  },

  async attachThumbnailToJob(filename: string, jobId: string): Promise<void> {
    const r = await fetch(
      `${BASE}/api/thumbnail-studio/attach/${encodeURIComponent(filename)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId }),
      },
    );
    if (!r.ok) throw new Error(`attachThumbnailToJob: ${r.status}`);
  },

  thumbnailImageUrl(filename: string): string {
    return `${BASE}/api/thumbnail-studio/image/${encodeURIComponent(filename)}`;
  },

  thumbnailDownloadUrl(filename: string): string {
    return `${BASE}/api/thumbnail-studio/download/${encodeURIComponent(filename)}`;
  },

  // B-roll Library
  async listLibrary(params: {
    page?: number;
    per_page?: number;
    game?: string;
    tag?: string;
    source?: string;
    permanent?: boolean;
    expiring_soon?: boolean;
    search?: string;
    sort?: string;
  } = {}): Promise<LibraryListResponse> {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
    }
    const r = await fetch(`${BASE}/api/broll/library?${qs}`);
    if (!r.ok) throw new Error(`listLibrary: ${r.status}`);
    return r.json();
  },

  async getLibraryClip(id: string): Promise<LibraryClip> {
    const r = await fetch(`${BASE}/api/broll/library/${id}`);
    if (!r.ok) throw new Error(`getLibraryClip: ${r.status}`);
    return r.json();
  },

  async updateLibraryClip(id: string, fields: Partial<Pick<LibraryClip, 'game' | 'tags' | 'permanent' | 'source' | 'source_url'>>): Promise<LibraryClip> {
    const r = await fetch(`${BASE}/api/broll/library/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fields),
    });
    if (!r.ok) throw new Error(`updateLibraryClip: ${r.status}`);
    return r.json();
  },

  async deleteLibraryClip(id: string): Promise<void> {
    const r = await fetch(`${BASE}/api/broll/library/${id}`, { method: 'DELETE' });
    if (!r.ok) throw new Error(`deleteLibraryClip: ${r.status}`);
  },

  async addClipTags(id: string, tags: string[]): Promise<LibraryClip> {
    const r = await fetch(`${BASE}/api/broll/library/${id}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags }),
    });
    if (!r.ok) throw new Error(`addClipTags: ${r.status}`);
    return r.json();
  },

  async removeClipTag(id: string, tag: string): Promise<LibraryClip> {
    const r = await fetch(`${BASE}/api/broll/library/${id}/tags/${encodeURIComponent(tag)}`, { method: 'DELETE' });
    if (!r.ok) throw new Error(`removeClipTag: ${r.status}`);
    return r.json();
  },

  async togglePermanent(id: string, permanent: boolean): Promise<LibraryClip> {
    const r = await fetch(`${BASE}/api/broll/library/${id}/permanent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ permanent }),
    });
    if (!r.ok) throw new Error(`togglePermanent: ${r.status}`);
    return r.json();
  },

  async getLibraryTags(): Promise<TagCount[]> {
    const r = await fetch(`${BASE}/api/broll/library/tags`);
    if (!r.ok) throw new Error(`getLibraryTags: ${r.status}`);
    return r.json();
  },

  async getLibraryGames(): Promise<GameCount[]> {
    const r = await fetch(`${BASE}/api/broll/library/games`);
    if (!r.ok) throw new Error(`getLibraryGames: ${r.status}`);
    return r.json();
  },

  async bulkAddTags(clipIds: string[], tags: string[]): Promise<{ updated: number }> {
    const r = await fetch(`${BASE}/api/broll/library/bulk/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_ids: clipIds, tags }),
    });
    if (!r.ok) throw new Error(`bulkAddTags: ${r.status}`);
    return r.json();
  },

  async bulkSetPermanent(clipIds: string[], permanent: boolean): Promise<{ updated: number }> {
    const r = await fetch(`${BASE}/api/broll/library/bulk/permanent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_ids: clipIds, permanent }),
    });
    if (!r.ok) throw new Error(`bulkSetPermanent: ${r.status}`);
    return r.json();
  },

  async bulkDeleteClips(clipIds: string[]): Promise<{ deleted: number }> {
    const r = await fetch(`${BASE}/api/broll/library/bulk/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_ids: clipIds }),
    });
    if (!r.ok) throw new Error(`bulkDeleteClips: ${r.status}`);
    return r.json();
  },

  libraryThumbUrl(clipId: string): string {
    return `${BASE}/api/broll/library/thumb/${clipId}`;
  },

  libraryPreviewUrl(clipId: string): string {
    return `${BASE}/api/broll/library/preview/${clipId}`;
  },

  libraryStreamUrl(clipId: string): string {
    return `${BASE}/api/broll/library/stream/${clipId}`;
  },

  // Summons (Kuchiyose)
  async getSummons(): Promise<Summon[]> {
    const r = await fetch(`${BASE}/api/summons`);
    if (!r.ok) throw new Error(`getSummons: ${r.status}`);
    return r.json();
  },
};
