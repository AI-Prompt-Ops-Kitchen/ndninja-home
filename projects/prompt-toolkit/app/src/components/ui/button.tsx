'use client';

import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'glow';
  size?: 'sm' | 'md' | 'lg' | 'icon';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-950 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer',
          {
            'bg-indigo-600 text-white hover:bg-indigo-500 active:bg-indigo-700 focus-visible:ring-indigo-500 shadow-lg shadow-indigo-600/20 hover:shadow-indigo-500/30':
              variant === 'primary',
            'bg-gray-800 text-gray-200 hover:bg-gray-700 border border-gray-700 hover:border-gray-600 focus-visible:ring-gray-500':
              variant === 'secondary',
            'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60 focus-visible:ring-gray-500':
              variant === 'ghost',
            'bg-red-600/10 text-red-400 border border-red-600/20 hover:bg-red-600/20 hover:border-red-600/30 focus-visible:ring-red-500':
              variant === 'danger',
            'relative bg-indigo-600 text-white hover:bg-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] focus-visible:ring-indigo-500':
              variant === 'glow',
          },
          {
            'text-xs px-3 py-1.5 gap-1.5': size === 'sm',
            'text-sm px-4 py-2 gap-2': size === 'md',
            'text-base px-6 py-3 gap-2.5': size === 'lg',
            'h-9 w-9 p-0': size === 'icon',
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
