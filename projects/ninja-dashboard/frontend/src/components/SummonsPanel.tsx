import { useSummons } from '../hooks/useSummons';
import type { Summon, SummonAnimal } from '../types/summon';

const ANIMAL_EMOJI: Record<SummonAnimal, string> = {
  toad: '\u{1F438}',
  snake: '\u{1F40D}',
  slug: '\u{1F41B}',
  scroll: '\u{1F4DC}',
};

const COLOR_MAP: Record<string, string> = {
  'yellow-400': '#facc15',
  'orange-400': '#fb923c',
  'purple-400': '#c084fc',
  'green-400':  '#4ade80',
  'red-400':    '#f87171',
  'cyan-400':   '#22d3ee',
};

function StatusDot({ status }: { status: Summon['status'] }) {
  const base = 'w-1.5 h-1.5 rounded-full inline-block';
  switch (status) {
    case 'active':
      return <span className={`${base} bg-cyan-400 animate-mangekyo-awakening`} />;
    case 'thinking':
      return <span className={`${base} bg-yellow-400 animate-mangekyo-spin`} />;
    case 'done':
      return <span className={`${base} bg-gray-600`} />;
    case 'error':
      return <span className={`${base} bg-red-400 animate-mangekyo-amaterasu`} />;
    default:
      return <span className={`${base} bg-gray-500`} />;
  }
}

function elapsed(summoned_at: number): string {
  const s = Math.floor((Date.now() / 1000) - summoned_at);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

function SummonCard({ summon }: { summon: Summon }) {
  const color = COLOR_MAP[summon.color] || COLOR_MAP['cyan-400'];
  const emoji = ANIMAL_EMOJI[summon.animal] || '\u{1F4DC}';
  const isDone = summon.status === 'done';

  return (
    <div
      className={`
        flex items-center gap-3 px-3 py-2 rounded-lg border
        transition-all duration-500
        ${isDone
          ? 'bg-surface/30 border-white/3 opacity-40 blur-[0.5px]'
          : 'bg-surface border-white/5 animate-summon-poof'
        }
      `}
    >
      {/* Animal emoji */}
      <span className="text-lg leading-none select-none">{emoji}</span>

      {/* Info */}
      <div className="flex flex-col min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-semibold" style={{ color }}>
            {summon.name}
          </span>
          <StatusDot status={summon.status} />
        </div>
        <span className="text-xs text-gray-500 truncate">
          {summon.specialty}
        </span>
      </div>

      {/* Timer */}
      {!isDone && (
        <span className="text-[10px] text-gray-600 ml-auto tabular-nums">
          {elapsed(summon.summoned_at)}
        </span>
      )}
    </div>
  );
}

export function SummonsPanel() {
  const { summons } = useSummons();

  if (summons.length === 0) return null;

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Summons
        </span>
        <span className="text-[10px] text-gray-600">
          {summons.filter(s => s.status !== 'done').length} active
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {summons.map(s => (
          <SummonCard key={s.summon_id} summon={s} />
        ))}
      </div>
    </div>
  );
}
