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

export function ReviewQueue({ jobs }: Props) {
  const readyJobs = jobs.filter(j => j.status === 'ready_for_review');

  if (readyJobs.length === 0) {
    return (
      <Card className="flex flex-col items-center justify-center gap-2 py-8">
        <span className="text-2xl">🥷</span>
        <p className="text-gray-600 text-sm">Nothing to review yet.</p>
        <p className="text-gray-700 text-xs">Videos appear here when generation completes.</p>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider px-1">
        Review Queue
        <span className="ml-2 text-xs text-green-500">({readyJobs.length})</span>
      </h2>
      <AnimatePresence>
        {readyJobs.map(job => (
          <ReviewCard key={job.id} job={job} />
        ))}
      </AnimatePresence>
    </div>
  );
}
