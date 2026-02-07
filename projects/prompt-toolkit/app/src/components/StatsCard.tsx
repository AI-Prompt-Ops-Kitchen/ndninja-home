'use client';

import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import { AnimatedCounter } from './AnimatedCounter';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  label: string;
  value: number;
  prefix?: string;
  suffix?: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: LucideIcon;
  decimals?: number;
  className?: string;
}

export function StatsCard({
  label,
  value,
  prefix,
  suffix,
  change,
  changeType = 'positive',
  icon: Icon,
  decimals = 0,
  className,
}: StatsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4 }}
      className={cn(
        'rounded-xl border border-gray-800 bg-gray-900/50 p-5 hover:border-gray-700 transition-all duration-300',
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600/10">
          <Icon className="h-4 w-4 text-indigo-400" />
        </div>
        {change && (
          <span
            className={cn(
              'flex items-center gap-1 text-xs font-medium rounded-full px-2 py-0.5',
              {
                'text-green-400 bg-green-500/10': changeType === 'positive',
                'text-red-400 bg-red-500/10': changeType === 'negative',
                'text-gray-400 bg-gray-800': changeType === 'neutral',
              }
            )}
          >
            {changeType === 'positive' && '↑'}
            {changeType === 'negative' && '↓'}
            {change}
          </span>
        )}
      </div>
      <AnimatedCounter
        end={value}
        prefix={prefix}
        suffix={suffix}
        decimals={decimals}
        className="text-2xl font-bold text-white block"
      />
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </motion.div>
  );
}
