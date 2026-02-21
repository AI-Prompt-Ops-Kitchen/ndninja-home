import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { BrollSlot, BrollCandidate } from '../types';
import { useBrollWingman } from '../hooks/useBrollWingman';
import { api } from '../lib/api';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';

// ---------------------------------------------------------------------------
// Candidate thumbnail card
// ---------------------------------------------------------------------------

function CandidateCard({
  candidate,
  isSelected,
  onSelect,
}: {
  candidate: BrollCandidate;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const [imgError, setImgError] = useState(false);
  const srcBadge = candidate.source === 'pexels' ? 'Pexels' : 'YT';

  return (
    <button
      onClick={onSelect}
      className={cn(
        'relative flex-shrink-0 w-28 h-20 rounded-lg overflow-hidden border-2 transition-all cursor-pointer',
        'hover:scale-105 active:scale-95',
        isSelected
          ? 'border-purple-400 shadow-lg shadow-purple-500/20'
          : 'border-white/10 hover:border-purple-400/50',
      )}
    >
      {candidate.preview_url && !imgError ? (
        <img
          src={candidate.preview_url}
          alt={candidate.title || ''}
          className="w-full h-full object-cover"
          onError={() => setImgError(true)}
          loading="lazy"
        />
      ) : (
        <div className="w-full h-full bg-[#1a1a30] flex items-center justify-center">
          <span className="text-xs text-gray-600">No preview</span>
        </div>
      )}

      {/* Source badge */}
      <span className={cn(
        'absolute top-1 left-1 px-1.5 py-0.5 rounded text-[10px] font-bold',
        candidate.source === 'pexels'
          ? 'bg-green-500/80 text-white'
          : 'bg-red-500/80 text-white',
      )}>
        {srcBadge}
      </span>

      {/* Duration */}
      {candidate.duration_sec && (
        <span className="absolute bottom-1 right-1 px-1 py-0.5 rounded bg-black/70 text-[10px] text-gray-300 font-mono">
          {Math.round(candidate.duration_sec)}s
        </span>
      )}

      {/* Download status indicator */}
      {candidate.download_status === 'downloading' && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <motion.div
            className="w-5 h-5 rounded-full border-2 border-purple-400 border-t-transparent"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
        </div>
      )}

      {candidate.download_status === 'ready' && (
        <div className="absolute top-1 right-1 w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
          <span className="text-[8px] text-white font-bold">OK</span>
        </div>
      )}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Single slot card
// ---------------------------------------------------------------------------

function LibraryPicker({
  onPick,
  onClose,
}: {
  onPick: (filename: string) => void;
  onClose: () => void;
}) {
  const [clips, setClips] = useState<{ filename: string; size_mb: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listBroll()
      .then(setClips)
      .catch(() => setClips([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mt-2 rounded-lg border border-purple-500/20 bg-[#0d0d1a] overflow-hidden"
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
        <span className="text-xs font-semibold text-purple-400">Local Library</span>
        <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-300">Close</button>
      </div>
      <div className="max-h-40 overflow-y-auto">
        {loading && <p className="text-xs text-gray-600 p-3">Loading...</p>}
        {!loading && clips.length === 0 && <p className="text-xs text-gray-600 p-3">No clips in library</p>}
        {clips.map(c => (
          <button
            key={c.filename}
            onClick={() => onPick(c.filename)}
            className="w-full flex items-center justify-between px-3 py-1.5 text-left hover:bg-purple-500/10 transition-colors cursor-pointer"
          >
            <span className="text-xs text-gray-300 truncate mr-2">{c.filename}</span>
            <span className="text-[10px] text-gray-600 flex-shrink-0">{c.size_mb} MB</span>
          </button>
        ))}
      </div>
    </motion.div>
  );
}

function SlotCard({
  slot,
  onApprove,
  onSkip,
  onAssignLocal,
}: {
  slot: BrollSlot;
  onApprove: (candidateId: string) => void;
  onSkip: () => void;
  onAssignLocal: (filename: string) => void;
}) {
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [showLibrary, setShowLibrary] = useState(false);
  const [editing, setEditing] = useState(false);
  const isResolved = slot.status === 'approved' || slot.status === 'skipped';
  const isSearching = slot.status === 'searching';

  // Find the approved candidate for display
  const approvedCandidate = isResolved && slot.approved_candidate_id
    ? slot.candidates.find(c => c.id === slot.approved_candidate_id)
    : null;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={cn(
        'rounded-xl border p-3 transition-all',
        isResolved && !editing
          ? 'border-white/5 bg-[#111120]'
          : 'border-purple-500/20 bg-[#14142a]',
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">
            Slot {slot.slot_index + 1}
          </span>
          <span className="text-sm font-medium text-gray-200">
            {slot.keyword}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {slot.status === 'approved' && !editing && (
            <>
              <span className="text-xs text-green-400 font-semibold">Approved</span>
              <button
                onClick={() => setEditing(true)}
                className="text-[10px] text-gray-600 hover:text-purple-400 transition-colors"
              >
                Edit
              </button>
            </>
          )}
          {slot.status === 'skipped' && !editing && (
            <>
              <span className="text-xs text-gray-500 font-semibold">Skipped</span>
              <button
                onClick={() => setEditing(true)}
                className="text-[10px] text-gray-600 hover:text-purple-400 transition-colors"
              >
                Edit
              </button>
            </>
          )}
          {isSearching && (
            <span className="flex items-center gap-1.5 text-xs text-purple-400">
              <motion.span
                className="inline-block w-1.5 h-1.5 rounded-full bg-purple-400"
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1, repeat: Infinity }}
              />
              Searching...
            </span>
          )}
        </div>
      </div>

      {/* Context sentence */}
      {slot.sentence && (
        <p className="text-xs text-gray-500 mb-2 leading-relaxed line-clamp-2">
          "{slot.sentence}"
        </p>
      )}

      {/* Approved selection summary (collapsed view) */}
      {isResolved && !editing && approvedCandidate && (
        <div className="flex items-center gap-2 mt-1">
          {approvedCandidate.preview_url ? (
            <img
              src={approvedCandidate.preview_url}
              alt={approvedCandidate.title || ''}
              className="w-16 h-11 rounded object-cover border border-white/10"
            />
          ) : (
            <div className="w-16 h-11 rounded bg-[#1a1a30] flex items-center justify-center border border-white/10">
              <span className="text-[8px] text-gray-600">Local</span>
            </div>
          )}
          <span className="text-xs text-gray-400 truncate">
            {approvedCandidate.title || approvedCandidate.local_path?.split('/').pop() || 'Selected clip'}
          </span>
        </div>
      )}

      {/* Candidate strip — show when not resolved OR when editing */}
      {(!isResolved || editing) && slot.candidates.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-2 mb-2 scrollbar-thin">
          {slot.candidates.map(c => (
            <CandidateCard
              key={c.id}
              candidate={c}
              isSelected={selectedCandidateId === c.id}
              onSelect={() => setSelectedCandidateId(c.id)}
            />
          ))}
        </div>
      )}

      {/* No candidates */}
      {(!isResolved || editing) && slot.status === 'candidates_ready' && slot.candidates.length === 0 && (
        <p className="text-xs text-gray-600 italic mb-2">No clips found for this keyword</p>
      )}

      {/* Action buttons — show when not resolved OR when editing */}
      {(!isResolved || editing) && (slot.status === 'candidates_ready' || editing) && (
        <div className="flex gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              if (selectedCandidateId) {
                onApprove(selectedCandidateId);
                setEditing(false);
              }
            }}
            disabled={!selectedCandidateId}
            className="!bg-purple-500 hover:!bg-purple-400 !shadow-purple-500/20"
          >
            Approve
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowLibrary(v => !v)}
            className={showLibrary ? '!text-purple-400' : ''}
          >
            Library
          </Button>
          <Button variant="ghost" size="sm" onClick={() => { onSkip(); setEditing(false); }}>
            Skip
          </Button>
          {editing && (
            <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          )}
        </div>
      )}

      {/* Library picker dropdown */}
      <AnimatePresence>
        {showLibrary && (!isResolved || editing) && (
          <LibraryPicker
            onPick={(filename) => {
              onAssignLocal(filename);
              setShowLibrary(false);
              setEditing(false);
            }}
            onClose={() => setShowLibrary(false)}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function BrollWingman({ jobId }: { jobId: string }) {
  const {
    session,
    loading,
    approveSlot,
    skipSlot,
    assignLocal,
    startDiscovery,
    resolvedCount,
    totalSlots,
  } = useBrollWingman(jobId);

  // Nothing to show yet
  if (!session && !loading) return null;

  const isExtracting = session?.status === 'extracting';
  const isSearching = session?.status === 'searching';
  const isCompleted = session?.status === 'completed';
  const isFailed = session?.status === 'failed';
  const hasSlots = (session?.slots.length ?? 0) > 0;

  return (
    <Card className="flex flex-col gap-3 !border-purple-500/10">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-purple-400 uppercase tracking-wider">
            B-roll Wingman
          </span>
          {totalSlots > 0 && (
            <span className="text-xs text-gray-600">
              {resolvedCount} of {totalSlots} resolved
            </span>
          )}
        </div>
        {isCompleted && (
          <span className="text-xs text-green-400 font-semibold">Done</span>
        )}
      </div>

      {/* Progress bar */}
      {totalSlots > 0 && !isCompleted && (
        <div className="h-1 rounded-full bg-white/5 overflow-hidden">
          <motion.div
            className="h-full bg-purple-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${(resolvedCount / totalSlots) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      )}

      <AnimatePresence mode="wait">
        {/* Loading / Extracting */}
        {(loading || isExtracting) && (
          <motion.div
            key="extracting"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-3 py-4"
          >
            <div className="flex gap-1">
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-purple-400"
                  animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.1, 0.8] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
            </div>
            <span className="text-sm text-gray-400">Extracting keywords from script...</span>
          </motion.div>
        )}

        {/* Searching */}
        {isSearching && !hasSlots && (
          <motion.div
            key="searching"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-3 py-4"
          >
            <motion.div
              className="w-5 h-5 rounded-full border-2 border-purple-400 border-t-transparent"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
            <span className="text-sm text-gray-400">Searching for clips...</span>
          </motion.div>
        )}

        {/* Slot cards */}
        {hasSlots && (
          <motion.div
            key="slots"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col gap-2"
          >
            {session!.slots.map(slot => (
              <SlotCard
                key={slot.id}
                slot={slot}
                onApprove={(candidateId) => approveSlot(slot.id, candidateId)}
                onSkip={() => skipSlot(slot.id)}
                onAssignLocal={(filename) => assignLocal(slot.id, filename)}
              />
            ))}
          </motion.div>
        )}

        {/* Failed */}
        {isFailed && (
          <motion.div
            key="failed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col gap-2 py-3"
          >
            <p className="text-sm text-red-400">Discovery failed</p>
            <Button variant="ghost" size="sm" onClick={startDiscovery}>
              Retry
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
