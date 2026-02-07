import { cn } from '@/lib/utils';
import { HTMLAttributes } from 'react';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'info' | 'purple' | 'cyan' | 'error' | 'pro';
  size?: 'sm' | 'md';
}

export function Badge({ className, variant = 'default', size = 'sm', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium',
        {
          'bg-gray-800 text-gray-300 border border-gray-700': variant === 'default',
          'bg-green-500/10 text-green-400 border border-green-500/20': variant === 'success',
          'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20': variant === 'warning',
          'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20': variant === 'info',
          'bg-purple-500/10 text-purple-400 border border-purple-500/20': variant === 'purple',
          'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20': variant === 'cyan',
          'bg-red-500/10 text-red-400 border border-red-500/20': variant === 'error',
          'bg-gradient-to-r from-indigo-600/20 to-purple-600/20 text-indigo-300 border border-indigo-500/30': variant === 'pro',
        },
        {
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-3 py-1 text-sm': size === 'md',
        },
        className
      )}
      {...props}
    />
  );
}
