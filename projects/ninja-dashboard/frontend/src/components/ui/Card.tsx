import { forwardRef } from 'react';
import type { HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  raised?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, raised = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl border border-white/5 p-4',
        raised ? 'bg-[#18182e]' : 'bg-[#111120]',
        className,
      )}
      {...props}
    />
  ),
);

Card.displayName = 'Card';
export { Card };
