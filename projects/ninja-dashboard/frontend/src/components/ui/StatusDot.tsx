import { cn } from '../../lib/utils';
import type { JobStatus } from '../../types';

// dot classes: bg = iris/pupil, animation = 3 orbiting tomoe via box-shadow
const STATUS: Record<JobStatus, { label: string; dot: string }> = {
  pending:          { label: 'Pending',         dot: 'bg-gray-600' },
  script_ready:     { label: 'Script Ready',    dot: 'bg-cyan-400/20 animate-mangekyo-awakening' },
  generating:       { label: 'Generating',      dot: 'bg-yellow-400/20 animate-mangekyo-spin' },
  ready_for_review: { label: 'Ready to Review', dot: 'bg-green-400/20 animate-mangekyo-ready' },
  approved:         { label: 'Approved',        dot: 'bg-green-600' },
  discarded:        { label: 'Discarded',       dot: 'bg-gray-700' },
  error:            { label: 'Error',           dot: 'bg-red-400/20 animate-mangekyo-amaterasu' },
};

export function StatusDot({ status }: { status: JobStatus }) {
  const cfg = STATUS[status] ?? STATUS.pending;
  return (
    <span className="flex items-center gap-2 shrink-0">
      {/* Extra margin gives the orbiting tomoe box-shadows breathing room */}
      <span className={cn('w-2 h-2 rounded-full shrink-0 mx-1.5', cfg.dot)} />
      <span className="text-xs text-gray-400 whitespace-nowrap">{cfg.label}</span>
    </span>
  );
}
