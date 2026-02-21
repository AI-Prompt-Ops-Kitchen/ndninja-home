import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import type { Job } from '../types';
import { Card } from './ui/Card';
import { StatusDot } from './ui/StatusDot';
import { timeAgo } from '../lib/utils';

const DELETABLE = new Set(['error', 'approved', 'uploaded', 'discarded']);

async function deleteJob(id: string) {
  const r = await fetch(`/api/jobs/${id}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(`Delete failed: ${r.status}`);
}

interface Props {
  jobs: Job[];
  loading: boolean;
  currentJobId: string | null;
  onSelectJob: (id: string) => void;
}

function jobTitle(job: Job): string {
  if (job.script_text) {
    // First sentence of the script body (skip the intro)
    const stripped = job.script_text.replace(/^What's up my fellow Ninjas[^.]*\.\s*/i, '');
    return stripped.split(/[.!?]/)[0]?.trim().slice(0, 80) || 'Untitled';
  }
  if (job.article_url) return job.article_url.slice(0, 70);
  return 'New job';
}

export function JobsPanel({ jobs, loading, currentJobId, onSelectJob }: Props) {
  const [deleting, setDeleting] = useState<string | null>(null);

  async function handleDelete(id: string) {
    setDeleting(id);
    try { await deleteJob(id); } finally { setDeleting(null); }
  }

  if (loading) {
    return (
      <Card className="flex items-center justify-center h-40">
        <span className="text-gray-500 text-sm">Connecting…</span>
      </Card>
    );
  }

  const visible = jobs;

  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
        Jobs
        {visible.length > 0 && (
          <span className="ml-2 text-xs text-gray-600">({visible.length})</span>
        )}
      </h2>

      {visible.length === 0 ? (
        <p className="text-gray-600 text-sm py-4 text-center">
          No active jobs. Submit an article to get started.
        </p>
      ) : (
        <ul className="flex flex-col gap-2 max-h-96 overflow-y-auto scrollbar-thin pr-1">
          <AnimatePresence initial={false}>
            {visible.map(job => (
              <motion.li
                key={job.id}
                layout
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ duration: 0.2 }}
              >
                <div
                  onClick={() => onSelectJob(job.id)}
                  className={[
                    'rounded-xl bg-[#18182e] border px-3 py-2.5 flex items-start gap-3 cursor-pointer transition-colors',
                    currentJobId === job.id
                      ? 'border-cyan-500/50 bg-cyan-400/5'
                      : 'border-white/5 hover:border-white/10',
                  ].join(' ')}
                >
                  <StatusDot status={job.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200 truncate">{jobTitle(job)}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-600">{timeAgo(job.updated_at)}</span>
                      {job.retry_count > 0 && (
                        <span className="text-xs text-yellow-600">retry #{job.retry_count}</span>
                      )}
                      <span className="text-xs text-gray-700">{job.target_length_sec}s</span>
                    </div>
                    {job.status === 'error' && job.error_msg && (
                      <p className="text-xs text-red-400 mt-1 line-clamp-2">
                        {job.error_msg}
                      </p>
                    )}
                  </div>
                  {DELETABLE.has(job.status) && (
                    <button
                      onClick={() => handleDelete(job.id)}
                      disabled={deleting === job.id}
                      title="Delete job"
                      className="shrink-0 text-gray-700 hover:text-red-400 transition-colors text-xs mt-0.5"
                    >
                      {deleting === job.id ? '…' : '✕'}
                    </button>
                  )}
                </div>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      )}
    </Card>
  );
}
