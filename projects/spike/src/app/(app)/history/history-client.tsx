'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Spike, SpikeType } from '@/types/spike';
import { cn, formatDuration, formatDateTime } from '@/lib/utils';
import { hapticTap } from '@/lib/haptics';
import { motion } from 'framer-motion';
import { Waves, CloudRain, Filter, MessageSquare } from 'lucide-react';

interface HistoryClientProps {
  initialSpikes: Spike[];
}

export function HistoryClient({ initialSpikes }: HistoryClientProps) {
  const [filter, setFilter] = useState<SpikeType | 'all'>('all');

  const filtered = filter === 'all'
    ? initialSpikes
    : initialSpikes.filter((s) => s.type === filter);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">History</h1>
        <span className="text-sm text-gray-500">{filtered.length} spikes</span>
      </div>

      {/* Filter chips */}
      <div className="flex gap-2">
        {(['all', 'anxiety', 'sadness'] as const).map((f) => (
          <button
            key={f}
            onClick={() => { hapticTap(); setFilter(f); }}
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
              filter === f
                ? f === 'anxiety'
                  ? 'bg-violet-600/20 text-violet-300 border border-violet-500/40'
                  : f === 'sadness'
                    ? 'bg-sky-600/20 text-sky-300 border border-sky-500/40'
                    : 'bg-gray-700 text-gray-200 border border-gray-600'
                : 'bg-gray-800/50 text-gray-500 border border-transparent hover:border-gray-700'
            )}
          >
            {f === 'all' ? 'All' : f === 'anxiety' ? 'Anxiety' : 'Sadness'}
          </button>
        ))}
      </div>

      {/* Spike list */}
      {filtered.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16 space-y-3"
        >
          <Filter className="mx-auto text-gray-600" size={48} strokeWidth={1} />
          <p className="text-gray-500 text-sm">No spikes logged yet</p>
          <p className="text-gray-600 text-xs">Head to Log to record your first one</p>
        </motion.div>
      ) : (
        <div className="space-y-2">
          {filtered.map((spike, i) => (
            <motion.div
              key={spike.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                duration: 0.25,
                delay: Math.min(i * 0.04, 0.5), // Gentle stagger, caps at 0.5s
                ease: [0.25, 0.46, 0.45, 0.94],
              }}
            >
              <SpikeRow spike={spike} />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

function SpikeRow({ spike }: { spike: Spike }) {
  const isAnxiety = spike.type === 'anxiety';

  return (
    <Card hover className="border-gray-800/80">
      <CardContent className="flex items-center gap-4 py-3">
        {/* Icon */}
        <div
          className={cn(
            'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
            isAnxiety ? 'bg-violet-600/15 text-violet-400' : 'bg-sky-600/15 text-sky-400'
          )}
        >
          {isAnxiety ? <Waves size={20} /> : <CloudRain size={20} />}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-200">
              {isAnxiety ? 'Anxiety' : 'Sadness'}
            </span>
            {spike.duration_seconds && (
              <span className="text-xs text-gray-500">
                {formatDuration(spike.duration_seconds)}
              </span>
            )}
            {spike.notes && (
              <MessageSquare size={12} className="text-gray-600" />
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">{formatDateTime(spike.logged_at)}</span>
            {spike.notes && (
              <span className="text-xs text-gray-600 truncate max-w-[140px]">{spike.notes}</span>
            )}
          </div>
        </div>

        {/* Intensity badge */}
        <div
          className={cn(
            'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold',
            isAnxiety ? 'bg-violet-600/20 text-violet-300' : 'bg-sky-600/20 text-sky-300'
          )}
        >
          {spike.intensity}
        </div>
      </CardContent>
    </Card>
  );
}
