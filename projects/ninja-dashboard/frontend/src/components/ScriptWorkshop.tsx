import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Job } from '../types';
import { api } from '../lib/api';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { BrollWingman } from './BrollWingman';

// ── Length selector presets ──────────────────────────────────────────────────
const LENGTH_PRESETS = [
  { label: '30s', value: 30, hint: 'Quick' },
  { label: '60s', value: 60, hint: 'Short' },
  { label: '75s', value: 75, hint: 'Sweet spot' },
  { label: '90s', value: 90, hint: 'Reels' },
  { label: '120s', value: 120, hint: 'Long' },
] as const;

// ── B-roll presets ────────────────────────────────────────────────────────────
const BROLL_DURATION_PRESETS = [
  { label: '3s', value: 3 },
  { label: '4s', value: 4 },
  { label: '6s', value: 6 },
  { label: '8s', value: 8 },
] as const;

const BROLL_COUNT_OPTIONS = [1, 2, 3, 4, 5] as const;

// ── Input form ───────────────────────────────────────────────────────────────
function ArticleForm({ onJobCreated }: { onJobCreated: (id: string) => void }) {
  const [mode, setMode] = useState<'url' | 'text'>('url');
  const [url, setUrl] = useState('');
  const [text, setText] = useState('');
  const [targetLength, setTargetLength] = useState(75);
  const [customLength, setCustomLength] = useState(75);
  const [useCustom, setUseCustom] = useState(false);
  const [brollCount, setBrollCount] = useState(3);
  const [brollDuration, setBrollDuration] = useState(4);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectiveLength = useCustom ? customLength : targetLength;

  async function handleSubmit() {
    const payload: Parameters<typeof api.submitArticle>[0] = {
      target_length_sec: effectiveLength,
      broll_count: brollCount,
      broll_duration: brollDuration,
    };
    if (mode === 'url') {
      if (!url.trim()) return;
      payload.url = url.trim();
    } else {
      if (!text.trim()) return;
      payload.text = text.trim();
    }

    setSubmitting(true);
    setError(null);
    try {
      const job = await api.submitArticle(payload);
      onJobCreated(job.id);
      setUrl('');
      setText('');
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Mode toggle */}
      <div className="flex rounded-xl overflow-hidden border border-gray-700 self-start">
        {(['url', 'text'] as const).map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={[
              'px-4 py-1.5 text-sm font-medium transition-all',
              mode === m
                ? 'bg-cyan-400 text-[#0a0a12]'
                : 'text-gray-400 hover:text-gray-200',
            ].join(' ')}
          >
            {m === 'url' ? '🔗 URL' : '📄 Text'}
          </button>
        ))}
      </div>

      {/* Input */}
      {mode === 'url' ? (
        <input
          type="url"
          placeholder="https://article.example.com/news-story"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          className="w-full rounded-xl bg-[#18182e] border border-gray-700 focus:border-cyan-500 outline-none
                     px-4 py-3 text-sm text-gray-200 placeholder-gray-600 transition-colors"
        />
      ) : (
        <textarea
          placeholder="Paste article text here…"
          value={text}
          onChange={e => setText(e.target.value)}
          rows={5}
          className="w-full rounded-xl bg-[#18182e] border border-gray-700 focus:border-cyan-500 outline-none
                     px-4 py-3 text-sm text-gray-200 placeholder-gray-600 transition-colors resize-none"
        />
      )}

      {/* Target length selector */}
      <div className="flex flex-col gap-2">
        <span className="text-xs text-gray-500 uppercase tracking-wider">Target Length</span>
        <div className="flex gap-2 flex-wrap">
          {LENGTH_PRESETS.map(p => (
            <button
              key={p.value}
              onClick={() => { setTargetLength(p.value); setUseCustom(false); }}
              className={[
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-all border',
                !useCustom && targetLength === p.value
                  ? 'bg-cyan-400/15 border-cyan-400/50 text-cyan-400'
                  : 'border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600',
              ].join(' ')}
            >
              <span>{p.label}</span>
              <span className="text-xs ml-1 opacity-60">{p.hint}</span>
            </button>
          ))}
          {/* Custom */}
          <button
            onClick={() => setUseCustom(true)}
            className={[
              'px-3 py-1.5 rounded-lg text-sm font-medium transition-all border',
              useCustom
                ? 'bg-cyan-400/15 border-cyan-400/50 text-cyan-400'
                : 'border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600',
            ].join(' ')}
          >
            Custom
          </button>
        </div>

        {useCustom && (
          <div className="flex items-center gap-3 mt-1">
            <input
              type="range"
              min={15}
              max={180}
              step={5}
              value={customLength}
              onChange={e => setCustomLength(Number(e.target.value))}
              className="flex-1 accent-cyan-400"
            />
            <span className="text-sm text-cyan-400 font-mono w-12 text-right">
              {customLength}s
            </span>
          </div>
        )}

        <p className="text-xs text-gray-600">
          ~{Math.round(effectiveLength / 60 * 155)} words · {effectiveLength}s target
        </p>
      </div>

      {/* B-roll settings */}
      <div className="flex flex-col gap-3 pt-1 border-t border-white/5">
        <div className="flex gap-6">
          {/* Clip duration */}
          <div className="flex flex-col gap-2 flex-1">
            <span className="text-xs text-gray-500 uppercase tracking-wider">B-roll Clip Length</span>
            <div className="flex gap-2 flex-wrap">
              {BROLL_DURATION_PRESETS.map(p => (
                <button
                  key={p.value}
                  onClick={() => setBrollDuration(p.value)}
                  className={[
                    'px-3 py-1.5 rounded-lg text-sm font-medium transition-all border',
                    brollDuration === p.value
                      ? 'bg-cyan-400/15 border-cyan-400/50 text-cyan-400'
                      : 'border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600',
                  ].join(' ')}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Clip count */}
          <div className="flex flex-col gap-2">
            <span className="text-xs text-gray-500 uppercase tracking-wider">B-roll Clips</span>
            <div className="flex gap-2">
              {BROLL_COUNT_OPTIONS.map(n => (
                <button
                  key={n}
                  onClick={() => setBrollCount(n)}
                  className={[
                    'w-8 h-8 rounded-lg text-sm font-medium transition-all border',
                    brollCount === n
                      ? 'bg-cyan-400/15 border-cyan-400/50 text-cyan-400'
                      : 'border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600',
                  ].join(' ')}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        </div>
        <p className="text-xs text-gray-600">
          {brollCount} clip{brollCount !== 1 ? 's' : ''} × {brollDuration}s ·
          ~{Math.round(brollCount * brollDuration)}s of B-roll in {effectiveLength}s video
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 rounded-lg px-3 py-2">{error}</p>
      )}

      <Button
        variant="primary"
        size="lg"
        onClick={handleSubmit}
        disabled={submitting || (mode === 'url' ? !url.trim() : !text.trim())}
        className="self-start"
      >
        {submitting ? '⏳ Submitting…' : '✨ Generate Script'}
      </Button>
    </div>
  );
}

// ── Script preview + edit ─────────────────────────────────────────────────────
function ScriptPreview({ job, onGenerateVideo }: { job: Job; onGenerateVideo: () => void }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(job.script_text || '');
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync draft if script changes externally
  useEffect(() => {
    if (!editing) setDraft(job.script_text || '');
  }, [job.script_text, editing]);

  async function handleSave() {
    setSaving(true);
    try {
      await api.editScript(job.id, draft);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerate() {
    setGenerating(true);
    try {
      await api.approveScript(job.id);
      onGenerateVideo();
    } finally {
      setGenerating(false);
    }
  }

  const wordCount = (job.script_text || '').split(/\s+/).filter(Boolean).length;
  const estimatedSec = Math.round(wordCount / 155 * 60);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-cyan-400 font-semibold uppercase tracking-wider">
          Script Preview
        </span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">{wordCount}w · ~{estimatedSec}s</span>
          {!editing ? (
            <Button variant="ghost" size="sm" onClick={() => { setEditing(true); setTimeout(() => textareaRef.current?.focus(), 50); }}>
              ✏️ Edit
            </Button>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => { setEditing(false); setDraft(job.script_text || ''); }}>
                Cancel
              </Button>
              <Button variant="secondary" size="sm" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : '💾 Save'}
              </Button>
            </>
          )}
        </div>
      </div>

      {editing ? (
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          rows={8}
          className="w-full rounded-xl bg-[#18182e] border border-cyan-500/50 outline-none
                     px-4 py-3 text-sm text-gray-200 resize-none font-mono leading-relaxed"
        />
      ) : (
        <div className="rounded-xl bg-[#18182e] border border-white/5 px-4 py-3">
          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
            {job.script_text}
          </p>
        </div>
      )}

      <Button
        variant="primary"
        size="lg"
        onClick={handleGenerate}
        disabled={generating || editing}
        className="self-start"
      >
        {generating ? '⏳ Starting generation…' : '🎬 Generate Video'}
      </Button>
    </div>
  );
}

// ── Main ScriptWorkshop component ─────────────────────────────────────────────
interface Props {
  jobs: Job[];
  currentJobId: string | null;
  onCurrentJobChange: (id: string | null) => void;
}

export function ScriptWorkshop({ jobs, currentJobId, onCurrentJobChange }: Props) {
  const currentJob = currentJobId ? jobs.find(j => j.id === currentJobId) ?? null : null;

  function handleJobCreated(id: string) {
    onCurrentJobChange(id);
  }

  function handleGenerateVideo() {
    // Script approved → video generation kicked off
    // Job panel will track it. Reset workshop after a brief moment.
    setTimeout(() => onCurrentJobChange(null), 2000);
  }

  // Determine what to show
  const showForm = !currentJob || ['approved', 'discarded'].includes(currentJob.status);
  const showPending = currentJob?.status === 'pending';
  const showScriptReady = currentJob?.status === 'script_ready';
  const showGenerating = currentJob?.status === 'generating';
  const showError = currentJob?.status === 'error';

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Script Workshop
        </h2>
        {currentJob && !showForm && (
          <button
            onClick={() => onCurrentJobChange(null)}
            className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
          >
            + New
          </button>
        )}
      </div>

      <AnimatePresence mode="wait">
        {showForm && (
          <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <ArticleForm onJobCreated={handleJobCreated} />
          </motion.div>
        )}

        {showPending && (
          <motion.div key="pending" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-3 py-8">
            <div className="flex gap-1.5">
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  className="w-2 h-2 rounded-full bg-cyan-400"
                  animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.1, 0.8] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
            </div>
            <p className="text-sm text-gray-400">Generating script with Claude…</p>
            <p className="text-xs text-gray-600">
              Target: {currentJob?.target_length_sec}s ·{' '}
              {currentJob?.broll_count ?? 3} B-roll × {currentJob?.broll_duration ?? 4}s
            </p>
          </motion.div>
        )}

        {showScriptReady && currentJob && (
          <motion.div key="script" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col gap-4">
            <ScriptPreview job={currentJob} onGenerateVideo={handleGenerateVideo} />
            <BrollWingman jobId={currentJob.id} />
          </motion.div>
        )}

        {showGenerating && (
          <motion.div key="generating" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col items-center gap-3 py-8">
            <motion.div
              className="w-10 h-10 rounded-full border-2 border-yellow-400 border-t-transparent"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
            <p className="text-sm text-yellow-400">Generating video…</p>
            <p className="text-xs text-gray-600">Kling Avatar is running (~5 min). Track in Jobs Panel.</p>
            <button
              onClick={() => onCurrentJobChange(null)}
              className="text-xs text-cyan-400 hover:underline mt-2"
            >
              + Start another script
            </button>
          </motion.div>
        )}

        {showError && currentJob && (
          <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col gap-3 py-4">
            <p className="text-sm text-red-400">Script generation failed</p>
            {currentJob.error_msg && (
              <p className="text-xs text-gray-600 bg-red-400/5 rounded-lg px-3 py-2 font-mono">
                {currentJob.error_msg}
              </p>
            )}
            <Button variant="secondary" size="sm" onClick={() => onCurrentJobChange(null)}>
              Try again
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
