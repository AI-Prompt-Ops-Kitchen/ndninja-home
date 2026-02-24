import { cn } from '../lib/utils';

interface Props {
  value: 'standard' | 'enhanced';
  onChange: (tier: 'standard' | 'enhanced') => void;
}

const TIERS = [
  { value: 'standard' as const, label: 'Standard', desc: 'Core SOP content' },
  { value: 'enhanced' as const, label: 'Enhanced', desc: 'Includes traceability matrix & cross-references' },
];

export default function TierSelector({ value, onChange }: Props) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-navy-700">Content Tier</label>
      <div className="flex gap-3">
        {TIERS.map((tier) => (
          <button
            key={tier.value}
            onClick={() => onChange(tier.value)}
            className={cn(
              'flex-1 p-3 rounded-lg border text-left transition-all',
              value === tier.value
                ? 'border-accent bg-blue-50 ring-2 ring-accent/30'
                : 'border-navy-200 bg-white hover:border-navy-300',
            )}
          >
            <div className="font-medium text-sm">{tier.label}</div>
            <div className="text-xs text-navy-500 mt-1">{tier.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
