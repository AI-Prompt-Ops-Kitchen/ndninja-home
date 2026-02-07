import { cn } from '@/lib/utils';
import { HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  glass?: boolean;
  glow?: boolean;
}

export function Card({ className, hover = false, glass = false, glow = false, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-gray-800 bg-gray-900/50',
        glass && 'glass',
        hover && 'transition-all duration-300 hover:border-gray-700 hover:bg-gray-900/80 hover:shadow-[0_8px_30px_rgba(0,0,0,0.3),0_0_20px_rgba(99,102,241,0.05)] hover:-translate-y-0.5',
        glow && 'border-indigo-600/30 shadow-[0_0_20px_rgba(99,102,241,0.1)]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-6 py-4 border-b border-gray-800', className)} {...props} />;
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-6 py-4', className)} {...props} />;
}

export function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-6 py-4 border-t border-gray-800', className)} {...props} />;
}
