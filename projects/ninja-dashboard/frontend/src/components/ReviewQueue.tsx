import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import type { Job } from '../types';
import { api } from '../lib/api';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { timeAgo } from '../lib/utils';

interface Props {
  jobs: Job[];
}

function ReviewCard({ job }: { job: Job }) {
  const [showRejectOptions, setShowRejectOptions] = useState(false);
  const [busy, setBusy] = useState(false);

  const filename = job.output_path ? job.output_path.split('/').pop()! : '';
  const thumbFilename = job.thumb_path ? job.thumb_path.split('/').pop()! : '';

  async function handleApprove() {
    setBusy(true);
    try { await api.approveVideo(job.id); } finally { setBusy(false); }
  }

  async function handleDiscard() {
    setBusy(true);
    try { await api.discardJob(job.id); } finally { setBusy(false); }
  }

  async function handleRetry() {
    setBusy(true);
    setShowRejectOptions(false);
    try { await api.retryJob(job.id); } finally { setBusy(false); }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.25 }}
    >
      <Card className="flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-ready" />
            <span className="text-xs text-gray-400">Ready · {timeAgo(job.updated_at)}</span>
          </span>
          <span className="text-xs text-gray-600 font-mono">{filename.slice(0, 30)}</span>
        </div>

        {/* Video player — HTTP 206 byte-range via FastAPI */}
        {filename && (
          <video
            controls
            playsInline
            preload="metadata"
            className="w-full rounded-xl bg-black max-h-64 object-contain"
            src={api.videoUrl(job.output_path!)}
          />
        )}

        {/* Thumbnail */}
        {thumbFilename && (
          <div>
            <p className="text-xs text-gray-600 mb-1 uppercase tracking-wide">Thumbnail</p>
            <img
              src={api.thumbUrl(job.thumb_path!)}
              alt="Thumbnail"
              className="w-full rounded-lg border border-white/5 max-h-32 object-cover"
            />
          </div>
        )}

        {/* Actions */}
        <AnimatePresence mode="wait">
          {!showRejectOptions ? (
            <motion.div
              key="primary"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex gap-2"
            >
              <Button
                variant="success"
                size="lg"
                className="flex-1"
                onClick={handleApprove}
                disabled={busy}
              >
                ✅ Approve
              </Button>
              <Button
                variant="danger"
                size="lg"
                className="flex-1"
                onClick={() => setShowRejectOptions(true)}
                disabled={busy}
              >
                ❌ Reject
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="reject-options"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex gap-2"
            >
              <Button
                variant="secondary"
                size="md"
                onClick={() => setShowRejectOptions(false)}
                disabled={busy}
              >
                ← Back
              </Button>
              <Button
                variant="danger"
                size="md"
                className="flex-1"
                onClick={handleDiscard}
                disabled={busy}
              >
                🗑️ Discard
              </Button>
              <Button
                variant="warning"
                size="md"
                className="flex-1"
                onClick={handleRetry}
                disabled={busy}
              >
                🔄 Re-try
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}


function ApprovedCard({ job }: { job: Job }) {
  const [title, setTitle] = useState(() => {
    // Hook-first format: the first sentence IS the hook = best title
    if (job.script_text) {
      const first = job.script_text.split(/[.!?]/)[0]?.trim().slice(0, 100);
      if (first) return first;
    }
    return '';
  });
  const [description, setDescription] = useState(() => {
    // Pre-fill description from second sentence if available
    if (job.script_text) {
      const sentences = job.script_text.split(/[.!?]\s+/).filter(Boolean);
      if (sentences.length > 1) return sentences[1].trim().slice(0, 200);
    }
    return '';
  });
  const [tags, setTags] = useState(() => {
    const base = ['gaming', 'news'];
    if (job.dual_anchor) base.push('dual anchor', 'ninja and glitch');
    return base.join(',');
  });
  const [privacy, setPrivacy] = useState<'private' | 'unlisted' | 'public'>('private');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const filename = job.output_path ? job.output_path.split('/').pop()! : '';

  async function handleUpload() {
    if (!title.trim()) { setError('Title is required'); return; }
    setError('');
    setBusy(true);
    try {
      await api.uploadToYouTube(job.id, {
        title: title.trim(),
        description: description.trim(),
        tags: tags.split(',').map(t => t.trim()).filter(Boolean),
        privacy,
      });
    } catch (e: any) {
      setError(e.message || 'Upload failed');
    } finally {
      setBusy(false);
    }
  }

  const isUploading = job.status === 'uploading';
  const isUploaded = job.status === 'uploaded';

  const statusLabel = isUploading ? 'Uploading...' : isUploaded ? 'Uploaded' : 'Approved';
  const dotColor = isUploading ? 'bg-amber-400 animate-pulse' : isUploaded ? 'bg-blue-500' : 'bg-green-600';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.25 }}
    >
      <Card className="flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${dotColor}`} />
            <span className="text-xs text-gray-400">{statusLabel} · {timeAgo(job.updated_at)}</span>
          </span>
          <span className="text-xs text-gray-600 font-mono">{filename.slice(0, 30)}</span>
        </div>

        {/* Video player */}
        {filename && (
          <video
            controls
            playsInline
            preload="metadata"
            className="w-full rounded-xl bg-black max-h-64 object-contain"
            src={api.videoUrl(job.output_path!)}
          />
        )}

        {/* Download button */}
        {filename && (
          <a
            href={api.downloadUrl(job.output_path!)}
            download
            className="flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 hover:text-gray-100 transition-colors"
          >
            ⬇ Download Video
          </a>
        )}

        {/* Uploaded — show YouTube link */}
        {isUploaded && job.youtube_video_id && (
          <div className="flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-lg px-3 py-2">
            <span className="text-blue-400 text-sm">▶</span>
            <a
              href={`https://youtube.com/watch?v=${job.youtube_video_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-400 hover:text-blue-300 underline underline-offset-2 truncate"
            >
              youtube.com/watch?v={job.youtube_video_id}
            </a>
          </div>
        )}

        {/* Uploading — progress indicator */}
        {isUploading && (
          <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
            <span className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-amber-400">Uploading to YouTube...</span>
          </div>
        )}

        {/* Upload form — only for approved (not yet uploaded) */}
        {job.status === 'approved' && (
          <div className="flex flex-col gap-2">
            <input
              type="text"
              placeholder="Video title"
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full bg-[#0d0d1a] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-500/50 focus:outline-none"
            />

            {/* Advanced options — collapsed by default */}
            <button
              onClick={() => setShowAdvanced(v => !v)}
              className="text-xs text-gray-600 hover:text-gray-400 transition-colors self-start"
            >
              {showAdvanced ? '▲ Less options' : '+ Description, tags & privacy'}
            </button>

            {showAdvanced && (
              <div className="flex flex-col gap-2">
                <textarea
                  placeholder="Description (optional)"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  rows={2}
                  className="w-full bg-[#0d0d1a] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-500/50 focus:outline-none resize-none"
                />
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Tags (comma-separated)"
                    value={tags}
                    onChange={e => setTags(e.target.value)}
                    className="flex-1 bg-[#0d0d1a] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-500/50 focus:outline-none"
                  />
                  <select
                    value={privacy}
                    onChange={e => setPrivacy(e.target.value as typeof privacy)}
                    className="bg-[#0d0d1a] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:border-cyan-500/50 focus:outline-none"
                  >
                    <option value="private">Private</option>
                    <option value="unlisted">Unlisted</option>
                    <option value="public">Public</option>
                  </select>
                </div>
              </div>
            )}

            {error && <p className="text-xs text-red-400">{error}</p>}
            <Button
              variant="success"
              size="lg"
              onClick={handleUpload}
              disabled={busy}
            >
              {busy ? 'Uploading...' : '▶ Upload to YouTube'}
            </Button>
          </div>
        )}

        {/* Error with retry upload */}
        {job.status === 'error' && job.error_msg?.includes('upload') && (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-red-400">{job.error_msg}</p>
            <Button
              variant="warning"
              size="md"
              onClick={handleUpload}
              disabled={busy}
            >
              🔄 Retry Upload
            </Button>
          </div>
        )}
      </Card>
    </motion.div>
  );
}


export function ReviewQueue({ jobs }: Props) {
  const readyJobs = jobs.filter(j => j.status === 'ready_for_review');
  const approvedJobs = jobs.filter(j =>
    ['approved', 'uploading', 'uploaded'].includes(j.status)
    || (j.status === 'error' && j.youtube_title)
  );

  // Parent (App.tsx) handles visibility — don't render if nothing to show
  if (readyJobs.length === 0 && approvedJobs.length === 0) return null;

  return (
    <div className="flex flex-col gap-4">
      {readyJobs.length > 0 && (
        <>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider px-1">
            Review Queue
            <span className="ml-2 text-xs text-green-500">({readyJobs.length})</span>
          </h2>
          <AnimatePresence>
            {readyJobs.map(job => (
              <ReviewCard key={job.id} job={job} />
            ))}
          </AnimatePresence>
        </>
      )}

      {approvedJobs.length > 0 && (
        <>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider px-1">
            Approved
            <span className="ml-2 text-xs text-blue-400">({approvedJobs.length})</span>
          </h2>
          <AnimatePresence>
            {approvedJobs.map(job => (
              <ApprovedCard key={job.id} job={job} />
            ))}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}
