'use client';

import { motion } from 'framer-motion';
import { CheckCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import Link from 'next/link';

interface PricingCardProps {
  name: string;
  price: string;
  period: string;
  annualPrice?: string;
  description: string;
  features: string[];
  cta: string;
  href: string;
  highlighted?: boolean;
  isAnnual?: boolean;
  delay?: number;
  className?: string;
}

export function PricingCard({
  name,
  price,
  period,
  annualPrice,
  description,
  features,
  cta,
  href,
  highlighted = false,
  isAnnual = false,
  delay = 0,
  className,
}: PricingCardProps) {
  const displayPrice = isAnnual && annualPrice ? annualPrice : price;

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className={cn(
        'relative flex flex-col rounded-2xl border p-1',
        highlighted
          ? 'border-indigo-600/50 bg-gradient-to-b from-indigo-600/10 to-transparent shadow-[0_0_30px_rgba(99,102,241,0.1)]'
          : 'border-gray-800 bg-gray-900/50',
        className
      )}
    >
      {/* Popular badge */}
      {highlighted && (
        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-10">
          <span className="inline-flex items-center gap-1.5 bg-indigo-600 text-white text-xs font-semibold px-3 py-1 rounded-full shadow-lg shadow-indigo-600/30">
            <Sparkles className="h-3 w-3" />
            Most Popular
          </span>
        </div>
      )}

      <div className={cn(
        'flex flex-col h-full rounded-xl p-6',
        highlighted && 'bg-gray-900/80'
      )}>
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white">{name}</h3>
          <div className="flex items-baseline gap-1 mt-3">
            <span className="text-4xl font-bold text-white">{displayPrice}</span>
            <span className="text-sm text-gray-500">{period}</span>
          </div>
          {isAnnual && annualPrice && price !== '$0' && (
            <p className="text-xs text-green-400 mt-1">Save 20% with annual billing</p>
          )}
          <p className="text-sm text-gray-400 mt-3">{description}</p>
        </div>

        <ul className="space-y-3 mb-8 flex-1">
          {features.map((feature) => (
            <li key={feature} className="flex items-start gap-2.5 text-sm text-gray-300">
              <CheckCircle className={cn(
                'h-4 w-4 mt-0.5 flex-shrink-0',
                highlighted ? 'text-indigo-400' : 'text-gray-600'
              )} />
              {feature}
            </li>
          ))}
        </ul>

        <Link href={href}>
          <Button
            variant={highlighted ? 'glow' : 'secondary'}
            className="w-full"
            size="lg"
          >
            {cta}
          </Button>
        </Link>
      </div>
    </motion.div>
  );
}
