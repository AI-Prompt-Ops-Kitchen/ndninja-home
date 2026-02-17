'use client';

import { cn } from '@/lib/utils';
import { hapticTap } from '@/lib/haptics';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import { Timer, Square, X } from 'lucide-react';
import { SpikeType } from '@/types/spike';

interface TimerOverlayProps {
  running: boolean;
  elapsed: number;
  type: SpikeType;
  onStop: () => void;
  onDismiss: () => void;
  onStart: () => void;
  started: boolean;
}

function formatTimer(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function TimerOverlay({ running, elapsed, type, onStop, onDismiss, onStart, started }: TimerOverlayProps) {
  const isViolet = type === 'anxiety';

  if (!started) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        className="w-full mt-4"
      >
        <div
          className={cn(
            'rounded-2xl border p-4 space-y-3',
            isViolet
              ? 'border-violet-500/20 bg-violet-600/5'
              : 'border-sky-500/20 bg-sky-600/5'
          )}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Timer size={16} className={isViolet ? 'text-violet-400' : 'text-sky-400'} />
              <span className="text-sm text-gray-300">Track duration?</span>
            </div>
            <button onClick={() => { hapticTap(); onDismiss(); }} className="text-gray-600 hover:text-gray-400 transition-colors">
              <X size={18} />
            </button>
          </div>

          <div className="flex gap-2">
            <Button
              variant={isViolet ? 'anxiety' : 'sadness'}
              size="sm"
              className="flex-1"
              onClick={onStart}
            >
              Start timer
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { hapticTap(); onDismiss(); }}
            >
              Skip
            </Button>
          </div>
        </div>
      </motion.div>
    );
  }

  // Timer running — with breathing guide
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="w-full mt-4"
    >
      <div
        className={cn(
          'rounded-2xl border p-5 text-center space-y-4',
          isViolet
            ? 'border-violet-500/20 bg-violet-600/5'
            : 'border-sky-500/20 bg-sky-600/5'
        )}
      >
        <div className="flex items-center justify-center gap-2">
          <div className={cn(
            'w-2 h-2 rounded-full animate-gentle-pulse',
            isViolet ? 'bg-violet-400' : 'bg-sky-400'
          )} />
          <span className="text-xs text-gray-500 uppercase tracking-wider">Tracking</span>
        </div>

        {/* Timer + breathing guide side by side */}
        <div className="flex items-center justify-center gap-6 py-2">
          {/* Breathing guide circle — off to the left */}
          <div className="relative flex items-center justify-center w-20 h-20 shrink-0">
            <div
              className={cn(
                'absolute w-16 h-16 rounded-full animate-breathing-guide',
                isViolet
                  ? 'bg-violet-500/25 border border-violet-400/30 shadow-[0_0_20px_rgba(139,92,246,0.2)]'
                  : 'bg-sky-500/25 border border-sky-400/30 shadow-[0_0_20px_rgba(14,165,233,0.2)]'
              )}
            />
            <span className={cn(
              'relative text-[10px] font-medium uppercase tracking-wider',
              isViolet ? 'text-violet-400' : 'text-sky-400'
            )}>
              Breathe
            </span>
          </div>

          {/* Timer display */}
          <div className={cn(
            'text-4xl font-mono font-bold tabular-nums',
            isViolet ? 'text-violet-300' : 'text-sky-300'
          )}>
            {formatTimer(elapsed)}
          </div>
        </div>

        <div className="text-xs text-gray-600 space-y-1">
          <p>Follow the circle — inhale as it grows, exhale as it shrinks</p>
          <p className="text-gray-700">Auto-stops at 10:00</p>
        </div>

        <Button
          variant="secondary"
          size="md"
          onClick={() => { hapticTap(); onStop(); }}
          className="gap-2"
        >
          <Square size={14} />
          Stop
        </Button>
      </div>
    </motion.div>
  );
}
