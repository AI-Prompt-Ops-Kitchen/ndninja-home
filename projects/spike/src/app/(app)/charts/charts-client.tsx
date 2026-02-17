'use client';

import { useMemo, useState } from 'react';
import { Spike } from '@/types/spike';
import { cn } from '@/lib/utils';
import {
  spikesPerDay,
  spikesByHour,
  spikeHeatmap,
  intensityOverTime,
  typeRatio,
} from '@/lib/chart-utils';
import { SpikesPerDay } from '@/components/charts/spikes-per-day';
import { TimeOfDay } from '@/components/charts/time-of-day';
import { Heatmap } from '@/components/charts/heatmap';
import { IntensityTrend } from '@/components/charts/intensity-trend';
import { TypeRatio } from '@/components/charts/type-ratio';
import { hapticTap } from '@/lib/haptics';
import { exportCSV, exportPDF } from '@/lib/export';
import { BarChart3, Download, FileText } from 'lucide-react';

type Range = '7d' | '30d' | '90d' | 'all';

const RANGES: { key: Range; label: string }[] = [
  { key: '7d', label: '7 days' },
  { key: '30d', label: '30 days' },
  { key: '90d', label: '90 days' },
  { key: 'all', label: 'All' },
];

function filterByRange(spikes: Spike[], range: Range): Spike[] {
  if (range === 'all') return spikes;
  const days = range === '7d' ? 7 : range === '30d' ? 30 : 90;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  return spikes.filter((s) => new Date(s.logged_at) >= cutoff);
}

export function ChartsClient({ initialSpikes }: { initialSpikes: Spike[] }) {
  const [range, setRange] = useState<Range>('30d');

  const filtered = useMemo(() => filterByRange(initialSpikes, range), [initialSpikes, range]);

  const daily = useMemo(() => spikesPerDay(filtered), [filtered]);
  const hourly = useMemo(() => spikesByHour(filtered), [filtered]);
  const heatmapData = useMemo(() => spikeHeatmap(filtered), [filtered]);
  const intensityData = useMemo(() => intensityOverTime(filtered), [filtered]);
  const ratioData = useMemo(() => typeRatio(filtered), [filtered]);

  const avgIntensity = filtered.length > 0
    ? (filtered.reduce((sum, s) => sum + s.intensity, 0) / filtered.length).toFixed(1)
    : '—';

  if (initialSpikes.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-bold text-gray-100">Charts</h1>
        <div className="text-center py-16 space-y-3">
          <BarChart3 className="mx-auto text-gray-600" size={48} strokeWidth={1} />
          <p className="text-gray-500 text-sm">No data yet</p>
          <p className="text-gray-600 text-xs">Log some spikes and come back here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-100">Charts</h1>
        <span className="text-sm text-gray-500">{filtered.length} spikes</span>
      </div>

      {/* Range selector */}
      <div className="flex gap-2">
        {RANGES.map((r) => (
          <button
            key={r.key}
            onClick={() => setRange(r.key)}
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
              range === r.key
                ? 'bg-violet-600/20 text-violet-300 border border-violet-500/40'
                : 'bg-gray-800/50 text-gray-500 border border-transparent hover:border-gray-700'
            )}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl bg-surface border border-gray-800 px-4 py-3 text-center">
          <div className="text-2xl font-bold text-gray-100">{filtered.length}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
        <div className="rounded-xl bg-surface border border-gray-800 px-4 py-3 text-center">
          <div className="text-2xl font-bold text-gray-100">{avgIntensity}</div>
          <div className="text-xs text-gray-500">Avg intensity</div>
        </div>
        <div className="rounded-xl bg-surface border border-gray-800 px-4 py-3 text-center">
          <div className="text-2xl font-bold text-gray-100">{daily.length}</div>
          <div className="text-xs text-gray-500">Active days</div>
        </div>
      </div>

      {/* Export buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => { hapticTap(); exportCSV(filtered); }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 bg-gray-800/50 hover:bg-gray-800 border border-transparent hover:border-gray-700 transition-all"
        >
          <Download size={13} />
          Export CSV
        </button>
        <button
          onClick={() => { hapticTap(); exportPDF(filtered); }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 bg-gray-800/50 hover:bg-gray-800 border border-transparent hover:border-gray-700 transition-all"
        >
          <FileText size={13} />
          Print report
        </button>
      </div>

      {/* Charts */}
      <SpikesPerDay data={daily} />
      <TimeOfDay data={hourly} />
      <Heatmap data={heatmapData} />
      <IntensityTrend data={intensityData} />
      <TypeRatio data={ratioData} />
    </div>
  );
}
