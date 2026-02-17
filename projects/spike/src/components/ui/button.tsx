'use client';
import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'anxiety' | 'sadness' | 'success';
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-2xl font-semibold transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer active:scale-[0.97]',
          {
            'bg-violet-600 text-white hover:bg-violet-500 active:bg-violet-700 focus-visible:ring-violet-500 shadow-lg shadow-violet-600/20':
              variant === 'primary',
            'bg-gray-800 text-gray-200 hover:bg-gray-700 border border-gray-700 hover:border-gray-600 focus-visible:ring-gray-500':
              variant === 'secondary',
            'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 focus-visible:ring-gray-500':
              variant === 'ghost',
            'bg-violet-600/15 text-violet-300 border-2 border-violet-500/40 hover:bg-violet-600/25 hover:border-violet-500/60 focus-visible:ring-violet-500 shadow-[0_0_20px_rgba(139,92,246,0.15)]':
              variant === 'anxiety',
            'bg-sky-600/15 text-sky-300 border-2 border-sky-500/40 hover:bg-sky-600/25 hover:border-sky-500/60 focus-visible:ring-sky-500 shadow-[0_0_20px_rgba(14,165,233,0.15)]':
              variant === 'sadness',
            'bg-emerald-600/15 text-emerald-300 border-2 border-emerald-500/40 hover:bg-emerald-600/25 focus-visible:ring-emerald-500':
              variant === 'success',
          },
          {
            'text-xs px-3 py-1.5 gap-1.5': size === 'sm',
            'text-sm px-4 py-2.5 gap-2': size === 'md',
            'text-base px-6 py-3.5 gap-2.5': size === 'lg',
            'text-lg px-8 py-5 gap-3': size === 'xl',
          },
          className
        )}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';
export { Button };
export type { ButtonProps };
