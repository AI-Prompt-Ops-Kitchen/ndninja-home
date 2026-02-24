import { cn } from '../lib/utils';
import type { Standard } from '../types';

interface Props {
  standards: Standard[];
  selected: string[];
  onToggle: (id: string) => void;
}

export default function StandardSelector({ standards, selected, onToggle }: Props) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-navy-700">Select Standards</label>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {standards.map((std) => (
          <button
            key={std.id}
            onClick={() => onToggle(std.id)}
            className={cn(
              'p-3 rounded-lg border text-left transition-all',
              selected.includes(std.id)
                ? 'border-accent bg-blue-50 ring-2 ring-accent/30'
                : 'border-navy-200 bg-white hover:border-navy-300',
            )}
          >
            <div className="font-medium text-sm">{std.name}</div>
            <div className="text-xs text-navy-500 mt-1">{std.code}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
