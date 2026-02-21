import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../lib/api';
import { Card } from './ui/Card';
import { wsEventBus } from '../hooks/useWebSocket';
import type { Job, ThumbnailItem } from '../types';

const STYLES = ['engaging', 'shocked', 'thinking', 'pointing', 'excited'] as const;
type ThumbStyle = (typeof STYLES)[number];

interface Props {
  jobs: Job[];
}

export function ThumbnailStudio({ jobs }: Props) {
  const [topic, setTopic] = useState('');
  const [headline, setHeadline] = useState('');
  const [style, setStyle] = useState<ThumbStyle>('engaging');
  const [aspectRatio, setAspectRatio] = useState<'9:16' | '16:9'>('9:16');
  const [inspirationFile, setInspirationFile] = useState<File | null>(null);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [gallery, setGallery] = useState<ThumbnailItem[]>([]);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [attachJobId, setAttachJobId] = useState<string>('');
  const [attaching, setAttaching] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Jobs with video output (for attach dropdown)
  const videoJobs = jobs.filter(j => j.output_path);

  // Load gallery on mount and after generation
  useEffect(() => {
    loadGallery();
  }, []);

  async function loadGallery() {
    try {
      const items = await api.getThumbnailGallery();
      setGallery(items);
    } catch {}
  }

  // Listen for WS thumbnail events
  useEffect(() => {
    const unsubs = [
      wsEventBus.subscribe('thumbnail_ready', (data) => {
        const d = data as { id: string; filename: string };
        setGenerating(false);
        setResult(d.filename);
        setError(null);
        loadGallery();
      }),
      wsEventBus.subscribe('thumbnail_error', (data) => {
        const d = data as { id: string; error: string };
        setGenerating(false);
        setError(d.error || 'Generation failed');
      }),
    ];
    return () => unsubs.forEach(u => u());
  }, []);

  async function handleGenerate() {
    if (!topic.trim()) return;
    setGenerating(true);
    setResult(null);
    setError(null);

    try {
      if (inspirationFile) {
        const formData = new FormData();
        formData.append('topic', topic.trim());
        formData.append('style', style);
        formData.append('aspect_ratio', aspectRatio);
        if (headline.trim()) formData.append('headline', headline.trim());
        formData.append('file', inspirationFile);
        await api.generateThumbnailFromImage(formData);
      } else {
        await api.generateThumbnail({
          topic: topic.trim(),
          style,
          aspect_ratio: aspectRatio,
          headline: headline.trim() || undefined,
        });
      }
      // Generation started — WS events will update state
    } catch (e) {
      setGenerating(false);
      setError(String(e));
    }
  }

  async function handleRegenerate() {
    await handleGenerate();
  }

  async function handleDelete(filename: string) {
    try {
      await api.deleteThumbnail(filename);
      setGallery(prev => prev.filter(t => t.filename !== filename));
      if (result === filename) setResult(null);
      if (previewImage === filename) setPreviewImage(null);
    } catch {}
  }

  async function handleAttach() {
    if (!result || !attachJobId) return;
    setAttaching(true);
    try {
      await api.attachThumbnailToJob(result, attachJobId);
      setAttaching(false);
      setAttachJobId('');
    } catch {
      setAttaching(false);
    }
  }

  return (
    <Card className="flex flex-col gap-3">
      {/* Header */}
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
        Thumbnail Studio
      </h2>

      {/* Topic input */}
      <textarea
        placeholder="Topic or description for the thumbnail..."
        value={topic}
        onChange={e => setTopic(e.target.value)}
        rows={2}
        className="w-full rounded-lg bg-[#18182e] border border-gray-700 px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-500 focus:outline-none resize-none"
      />

      {/* Headline */}
      <input
        type="text"
        placeholder="Headline (auto-generated if blank)"
        value={headline}
        onChange={e => setHeadline(e.target.value)}
        className="w-full rounded-lg bg-[#18182e] border border-gray-700 px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-500 focus:outline-none"
      />

      {/* Style presets */}
      <div className="flex flex-wrap gap-1.5">
        {STYLES.map(s => (
          <button
            key={s}
            onClick={() => setStyle(s)}
            className={[
              'px-3 py-1 rounded-full text-xs font-medium transition-all capitalize',
              style === s
                ? 'bg-cyan-400/20 text-cyan-400 border border-cyan-500/40'
                : 'bg-[#18182e] text-gray-500 border border-gray-700 hover:text-gray-300 hover:border-gray-500',
            ].join(' ')}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Aspect ratio + Inspiration row */}
      <div className="flex items-center gap-3">
        {/* Aspect ratio toggle */}
        <div className="flex rounded-xl overflow-hidden border border-gray-700">
          {(['9:16', '16:9'] as const).map(ar => (
            <button
              key={ar}
              onClick={() => setAspectRatio(ar)}
              className={[
                'px-3 py-1 text-xs font-medium transition-all',
                aspectRatio === ar
                  ? 'bg-cyan-400/15 text-cyan-400'
                  : 'text-gray-500 hover:text-gray-300',
              ].join(' ')}
            >
              {ar === '9:16' ? '9:16 Shorts' : '16:9 Standard'}
            </button>
          ))}
        </div>

        {/* Inspiration upload */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className={[
            'flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all border',
            inspirationFile
              ? 'bg-purple-500/15 text-purple-400 border-purple-500/40'
              : 'bg-[#18182e] text-gray-500 border-gray-700 hover:text-gray-300 hover:border-gray-500',
          ].join(' ')}
        >
          {inspirationFile ? `${inspirationFile.name.slice(0, 15)}...` : 'Reference image'}
        </button>
        {inspirationFile && (
          <button
            onClick={() => setInspirationFile(null)}
            className="text-gray-600 hover:text-red-400 text-xs transition-colors"
          >
            clear
          </button>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={e => {
            const f = e.target.files?.[0];
            if (f) setInspirationFile(f);
            e.target.value = '';
          }}
        />
      </div>

      {/* Generate button */}
      <button
        onClick={handleGenerate}
        disabled={generating || !topic.trim()}
        className="w-full rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-500 text-black font-semibold text-sm py-2.5 transition-colors"
      >
        {generating ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            Generating...
          </span>
        ) : (
          'Generate Thumbnail'
        )}
      </button>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-xs text-red-400 bg-red-400/10 rounded-lg px-3 py-2"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Result display */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-xl border border-cyan-900/50 bg-[#12121f] p-3 flex flex-col gap-2"
          >
            <img
              src={api.thumbnailImageUrl(result)}
              alt="Generated thumbnail"
              className="w-full rounded-lg"
            />
            <div className="flex gap-2">
              <a
                href={api.thumbnailDownloadUrl(result)}
                download
                className="flex-1 text-center rounded-lg bg-[#18182e] border border-gray-700 text-gray-300 hover:text-white text-xs font-medium py-1.5 transition-colors"
              >
                Download
              </a>
              <button
                onClick={handleRegenerate}
                disabled={generating}
                className="flex-1 rounded-lg bg-[#18182e] border border-gray-700 text-gray-300 hover:text-white text-xs font-medium py-1.5 transition-colors"
              >
                Regenerate
              </button>
            </div>

            {/* Attach to job */}
            {videoJobs.length > 0 && (
              <div className="flex gap-2 items-center">
                <select
                  value={attachJobId}
                  onChange={e => setAttachJobId(e.target.value)}
                  className="flex-1 rounded-lg bg-[#18182e] border border-gray-700 text-gray-300 text-xs px-2 py-1.5 focus:border-cyan-500 focus:outline-none"
                >
                  <option value="">Attach to job...</option>
                  {videoJobs.map(j => (
                    <option key={j.id} value={j.id}>
                      {j.id.slice(0, 8)} — {j.article_url?.slice(0, 30) || j.status}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleAttach}
                  disabled={!attachJobId || attaching}
                  className="rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 text-xs font-medium px-3 py-1.5 hover:bg-cyan-500/30 disabled:opacity-40 transition-colors"
                >
                  {attaching ? '...' : 'Attach'}
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Gallery */}
      {gallery.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Recent Thumbnails
          </p>
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
            {gallery.map(item => (
              <div
                key={item.filename}
                className="relative shrink-0 group cursor-pointer"
                onClick={() => setPreviewImage(previewImage === item.filename ? null : item.filename)}
              >
                <img
                  src={api.thumbnailImageUrl(item.filename)}
                  alt={item.filename}
                  className={[
                    'w-20 h-28 object-cover rounded-lg border-2 transition-all',
                    previewImage === item.filename
                      ? 'border-cyan-400'
                      : 'border-transparent hover:border-gray-600',
                  ].join(' ')}
                />
                <button
                  onClick={e => {
                    e.stopPropagation();
                    handleDelete(item.filename);
                  }}
                  className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] leading-none flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  x
                </button>
              </div>
            ))}
          </div>

          {/* Preview expanded */}
          <AnimatePresence>
            {previewImage && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <img
                  src={api.thumbnailImageUrl(previewImage)}
                  alt="Preview"
                  className="w-full rounded-lg"
                />
                <div className="flex gap-2 mt-2">
                  <a
                    href={api.thumbnailDownloadUrl(previewImage)}
                    download
                    className="flex-1 text-center rounded-lg bg-[#18182e] border border-gray-700 text-gray-300 hover:text-white text-xs font-medium py-1.5 transition-colors"
                  >
                    Download
                  </a>
                  <button
                    onClick={() => {
                      setResult(previewImage);
                      setPreviewImage(null);
                    }}
                    className="flex-1 rounded-lg bg-[#18182e] border border-gray-700 text-gray-300 hover:text-white text-xs font-medium py-1.5 transition-colors"
                  >
                    Use as Result
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </Card>
  );
}
