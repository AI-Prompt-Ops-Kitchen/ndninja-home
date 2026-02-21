import type { Job, BrollSession } from '../types';
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
    return `${BASE}/api/video/${encodeURIComponent(basename(outputPath))}/download`;
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

  async assignLocalBroll(slotId: string, filename: string): Promise<void> {
    const r = await fetch(`${BASE}/api/broll-wingman/slots/${slotId}/assign-local`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename }),
    });
    if (!r.ok) throw new Error(`assignLocalBroll: ${r.status}`);
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
};
