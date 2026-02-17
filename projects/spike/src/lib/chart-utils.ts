import { Spike, SpikeType } from '@/types/spike';

// Colors matching our theme
export const COLORS = {
  anxiety: '#8b5cf6', // violet-500
  sadness: '#0ea5e9', // sky-500
  anxietyDim: 'rgba(139, 92, 246, 0.15)',
  sadnessDim: 'rgba(14, 165, 233, 0.15)',
  grid: 'rgba(255,255,255,0.06)',
  label: '#8080a0', // gray-500
  tooltip: '#16162a', // surface
};

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const HOUR_LABELS = Array.from({ length: 24 }, (_, i) => {
  if (i === 0) return '12a';
  if (i < 12) return `${i}a`;
  if (i === 12) return '12p';
  return `${i - 12}p`;
});

export interface DailyCount {
  date: string;
  anxiety: number;
  sadness: number;
  total: number;
}

export interface HourlyCount {
  hour: number;
  label: string;
  anxiety: number;
  sadness: number;
  total: number;
}

export interface HeatmapCell {
  day: number;
  dayLabel: string;
  hour: number;
  hourLabel: string;
  count: number;
}

export interface IntensityPoint {
  date: string;
  timestamp: number;
  intensity: number;
  type: SpikeType;
}

export interface TypeRatio {
  name: string;
  value: number;
  color: string;
}

export function spikesPerDay(spikes: Spike[]): DailyCount[] {
  const map = new Map<string, DailyCount>();

  for (const s of spikes) {
    const date = new Date(s.logged_at).toLocaleDateString('en-CA'); // YYYY-MM-DD
    const entry = map.get(date) || { date, anxiety: 0, sadness: 0, total: 0 };
    entry[s.type]++;
    entry.total++;
    map.set(date, entry);
  }

  return Array.from(map.values()).sort((a, b) => a.date.localeCompare(b.date));
}

export function spikesByHour(spikes: Spike[]): HourlyCount[] {
  const hours: HourlyCount[] = Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    label: HOUR_LABELS[i],
    anxiety: 0,
    sadness: 0,
    total: 0,
  }));

  for (const s of spikes) {
    const h = new Date(s.logged_at).getHours();
    hours[h][s.type]++;
    hours[h].total++;
  }

  return hours;
}

export function spikeHeatmap(spikes: Spike[]): HeatmapCell[] {
  const grid = new Map<string, number>();

  for (const s of spikes) {
    const d = new Date(s.logged_at);
    const key = `${d.getDay()}-${d.getHours()}`;
    grid.set(key, (grid.get(key) || 0) + 1);
  }

  const cells: HeatmapCell[] = [];
  for (let day = 0; day < 7; day++) {
    for (let hour = 0; hour < 24; hour++) {
      cells.push({
        day,
        dayLabel: DAY_LABELS[day],
        hour,
        hourLabel: HOUR_LABELS[hour],
        count: grid.get(`${day}-${hour}`) || 0,
      });
    }
  }

  return cells;
}

export function intensityOverTime(spikes: Spike[]): IntensityPoint[] {
  return spikes
    .map((s) => ({
      date: new Date(s.logged_at).toLocaleDateString('en-CA'),
      timestamp: new Date(s.logged_at).getTime(),
      intensity: s.intensity,
      type: s.type,
    }))
    .sort((a, b) => a.timestamp - b.timestamp);
}

export function typeRatio(spikes: Spike[]): TypeRatio[] {
  let anxiety = 0;
  let sadness = 0;
  for (const s of spikes) {
    if (s.type === 'anxiety') anxiety++;
    else sadness++;
  }
  return [
    { name: 'Anxiety', value: anxiety, color: COLORS.anxiety },
    { name: 'Sadness', value: sadness, color: COLORS.sadness },
  ];
}

export function formatShortDate(date: string): string {
  const d = new Date(date + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
