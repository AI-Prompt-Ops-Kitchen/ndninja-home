import { useState, useRef, useEffect } from 'react';
import type { DragEvent, ChangeEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import { Card } from './ui/Card';

type UploadMode = 'general' | 'broll';

interface UploadedFile {
  name: string;
  time: number;
}

interface BrollClip {
  filename: string;
  size_mb: number;
  modified: string;
}

// ── B-roll library panel ──────────────────────────────────────────────────────
function BrollLibrary({ refreshTrigger }: { refreshTrigger: number }) {
  const [clips, setClips] = useState<BrollClip[]>([]);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/broll')
      .then(r => r.json())
      .then(setClips)
      .catch(() => {});
  }, [refreshTrigger]);

  async function handleDelete(filename: string) {
    setDeleting(filename);
    try {
      await fetch(`/api/broll/${encodeURIComponent(filename)}`, { method: 'DELETE' });
      setClips(prev => prev.filter(c => c.filename !== filename));
    } finally {
      setDeleting(null);
    }
  }

  if (clips.length === 0) {
    return (
      <p className="text-xs text-gray-600 text-center py-3">
        No B-roll clips yet — upload game footage below
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto scrollbar-thin">
      {clips.map(clip => (
        <div
          key={clip.filename}
          className="flex items-center gap-2 text-xs bg-[#18182e] rounded-lg px-3 py-2"
        >
          <span className="text-purple-400">🎬</span>
          <span className="truncate text-gray-300 flex-1 font-mono">{clip.filename}</span>
          <span className="text-gray-600 whitespace-nowrap shrink-0">{clip.size_mb}MB</span>
          <button
            onClick={() => handleDelete(clip.filename)}
            disabled={deleting === clip.filename}
            className="text-gray-700 hover:text-red-400 transition-colors shrink-0 ml-1"
            title="Remove from library"
          >
            {deleting === clip.filename ? '…' : '✕'}
          </button>
        </div>
      ))}
    </div>
  );
}

// ── YouTube Clip Form ────────────────────────────────────────────────────────
function YoutubeClipForm({ onClipped }: { onClipped: () => void }) {
  const [url, setUrl] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [clipping, setClipping] = useState(false);
  const [result, setResult] = useState<{ filename: string; size_mb: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleClip() {
    if (!url || !start || !end) return;
    setClipping(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.clipYoutube({ url, start, end });
      setResult(res);
      setUrl('');
      setStart('');
      setEnd('');
      onClipped();
    } catch (e) {
      setError(String(e));
    } finally {
      setClipping(false);
    }
  }

  return (
    <div className="rounded-xl border border-purple-900/50 bg-[#12121f] p-3 flex flex-col gap-2">
      <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
        Clip from YouTube
      </p>
      <input
        type="text"
        placeholder="YouTube URL"
        value={url}
        onChange={e => setUrl(e.target.value)}
        className="w-full rounded-lg bg-[#18182e] border border-gray-700 px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
      />
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Start (0:11)"
          value={start}
          onChange={e => setStart(e.target.value)}
          className="flex-1 rounded-lg bg-[#18182e] border border-gray-700 px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
        />
        <input
          type="text"
          placeholder="End (0:23)"
          value={end}
          onChange={e => setEnd(e.target.value)}
          className="flex-1 rounded-lg bg-[#18182e] border border-gray-700 px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
        />
      </div>
      <button
        onClick={handleClip}
        disabled={clipping || !url || !start || !end}
        className="w-full rounded-lg bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium py-1.5 transition-colors"
      >
        {clipping ? 'Clipping...' : 'Clip'}
      </button>
      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 rounded-lg px-3 py-1.5">{error}</p>
      )}
      {result && (
        <p className="text-xs text-green-400 bg-green-400/10 rounded-lg px-3 py-1.5">
          Clipped {result.filename} ({result.size_mb}MB)
        </p>
      )}
    </div>
  );
}

// ── Main UploadZone ────────────────────────────────────────────────────────────
export function UploadZone() {
  const [mode, setMode] = useState<UploadMode>('general');
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState<UploadedFile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [brollRefresh, setBrollRefresh] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        let result: { filename: string };
        if (mode === 'broll') {
          const form = new FormData();
          form.append('file', file);
          const r = await fetch('/api/broll/upload', { method: 'POST', body: form });
          if (!r.ok) throw new Error(`Upload failed: ${r.status}`);
          result = await r.json();
          setBrollRefresh(n => n + 1);
        } else {
          result = await api.uploadFile(file);
        }
        setUploaded(prev => [{ name: result.filename, time: Date.now() }, ...prev.slice(0, 4)]);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  function onDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(true);
  }

  function onDragLeave() { setDragging(false); }

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    handleFiles(e.target.files);
    e.target.value = '';
  }

  const isBroll = mode === 'broll';

  return (
    <Card className="flex flex-col gap-3">
      {/* Header + mode toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          {isBroll ? 'B-Roll Library' : 'File Upload'}
        </h2>
        <div className="flex rounded-xl overflow-hidden border border-gray-700">
          {(['general', 'broll'] as const).map(m => (
            <button
              key={m}
              onClick={() => { setMode(m); setUploaded([]); setError(null); }}
              className={[
                'px-3 py-1 text-xs font-medium transition-all',
                mode === m
                  ? m === 'broll'
                    ? 'bg-purple-500/20 text-purple-400 border-purple-500/40 border'
                    : 'bg-cyan-400/15 text-cyan-400'
                  : 'text-gray-500 hover:text-gray-300',
              ].join(' ')}
            >
              {m === 'general' ? '📁 General' : '🎬 B-Roll'}
            </button>
          ))}
        </div>
      </div>

      {/* B-roll library list */}
      {isBroll && <BrollLibrary refreshTrigger={brollRefresh} />}

      {/* YouTube clip form */}
      {isBroll && <YoutubeClipForm onClipped={() => setBrollRefresh(n => n + 1)} />}

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        className={[
          'rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer',
          'flex flex-col items-center justify-center gap-2 py-6 px-4 text-center select-none',
          dragging
            ? isBroll
              ? 'border-purple-400 bg-purple-400/5 text-purple-400'
              : 'border-cyan-400 bg-cyan-400/5 text-cyan-400'
            : isBroll
              ? 'border-purple-900 hover:border-purple-700 text-purple-600 hover:text-purple-400'
              : 'border-gray-700 hover:border-gray-500 text-gray-500 hover:text-gray-400',
        ].join(' ')}
      >
        <span className="text-2xl">
          {uploading ? '⏳' : dragging ? '📥' : isBroll ? '🎮' : '📁'}
        </span>
        <p className="text-sm font-medium">
          {uploading
            ? `Adding to ${isBroll ? 'B-roll library' : 'uploads'}…`
            : dragging
              ? 'Drop to upload'
              : isBroll
                ? 'Drop gameplay footage here'
                : 'Drag & drop or tap to browse'}
        </p>
        <p className="text-xs opacity-50">
          {isBroll
            ? 'MP4/MOV — saves to ~/output/broll/ · used automatically during generation'
            : 'Saves to ~/uploads/ — accessible from Tailscale'}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={isBroll ? 'video/*' : undefined}
          className="hidden"
          onChange={onChange}
        />
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-400/10 rounded-lg px-3 py-2">{error}</p>
      )}

      <AnimatePresence>
        {uploaded.map(f => (
          <motion.div
            key={f.time}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={[
              'flex items-center gap-2 text-xs rounded-lg px-3 py-2',
              isBroll
                ? 'text-purple-400 bg-purple-400/5'
                : 'text-green-400 bg-green-400/5',
            ].join(' ')}
          >
            <span>✅</span>
            <span className="truncate font-mono">{f.name}</span>
            <span className="ml-auto whitespace-nowrap opacity-50">
              {isBroll ? 'added to library' : 'saved'}
            </span>
          </motion.div>
        ))}
      </AnimatePresence>
    </Card>
  );
}
