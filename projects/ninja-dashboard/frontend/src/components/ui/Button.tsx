import { forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'success' | 'danger' | 'warning';
  size?: 'sm' | 'md' | 'lg';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0a12]',
          'disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer active:scale-[0.96]',
          {
            'bg-cyan-400 text-[#0a0a12] hover:bg-cyan-300 focus-visible:ring-cyan-400 shadow-lg shadow-cyan-400/20':
              variant === 'primary',
            'bg-[#18182e] text-gray-200 hover:bg-[#1f1f3a] border border-gray-700 hover:border-gray-600 focus-visible:ring-gray-500':
              variant === 'secondary',
            'text-gray-400 hover:text-gray-200 hover:bg-white/5 focus-visible:ring-gray-500':
              variant === 'ghost',
            'bg-green-500/15 text-green-400 border border-green-500/30 hover:bg-green-500/25 hover:border-green-400/50 focus-visible:ring-green-400':
              variant === 'success',
            'bg-red-500/15 text-red-400 border border-red-500/30 hover:bg-red-500/25 hover:border-red-400/50 focus-visible:ring-red-400':
              variant === 'danger',
            'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/25 hover:border-yellow-400/50 focus-visible:ring-yellow-400':
              variant === 'warning',
          },
          {
            'text-xs px-3 py-1.5 gap-1.5': size === 'sm',
            'text-sm px-4 py-2.5 gap-2': size === 'md',
            'text-base px-6 py-3.5 gap-2.5': size === 'lg',
          },
          className,
        )}
        {...props}
      />
    );
  },
);

Button.displayName = 'Button';
export { Button };
export type { ButtonProps };
