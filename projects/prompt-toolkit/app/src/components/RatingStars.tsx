'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RatingStarsProps {
  rating: number;
  maxRating?: number;
  size?: 'sm' | 'md' | 'lg';
  interactive?: boolean;
  onRate?: (rating: number) => void;
  showValue?: boolean;
  count?: number;
  className?: string;
}

export function RatingStars({
  rating,
  maxRating = 5,
  size = 'sm',
  interactive = false,
  onRate,
  showValue = false,
  count,
  className,
}: RatingStarsProps) {
  const [hoverRating, setHoverRating] = useState(0);
  const displayRating = hoverRating || rating;

  const sizeMap = {
    sm: 'h-3.5 w-3.5',
    md: 'h-4.5 w-4.5',
    lg: 'h-5.5 w-5.5',
  };

  return (
    <div className={cn('flex items-center gap-1', className)}>
      <div className="flex items-center gap-0.5">
        {Array.from({ length: maxRating }, (_, i) => {
          const starValue = i + 1;
          const isFilled = starValue <= Math.floor(displayRating);
          const isPartial = !isFilled && starValue === Math.ceil(displayRating) && displayRating % 1 > 0;
          const fillPercent = isPartial ? (displayRating % 1) * 100 : 0;

          return (
            <motion.button
              key={i}
              type="button"
              disabled={!interactive}
              className={cn(
                'relative',
                interactive && 'cursor-pointer hover:scale-110 transition-transform',
                !interactive && 'cursor-default'
              )}
              whileTap={interactive ? { scale: 0.85 } : {}}
              onMouseEnter={() => interactive && setHoverRating(starValue)}
              onMouseLeave={() => interactive && setHoverRating(0)}
              onClick={() => interactive && onRate?.(starValue)}
            >
              {/* Background star (empty) */}
              <Star className={cn(sizeMap[size], 'text-gray-700')} />
              {/* Filled overlay */}
              {(isFilled || isPartial) && (
                <Star
                  className={cn(
                    sizeMap[size],
                    'absolute inset-0 text-yellow-500 fill-yellow-500'
                  )}
                  style={isPartial ? { clipPath: `inset(0 ${100 - fillPercent}% 0 0)` } : {}}
                />
              )}
            </motion.button>
          );
        })}
      </div>
      {showValue && (
        <span className="text-sm font-medium text-gray-300 ml-1">
          {rating.toFixed(1)}
        </span>
      )}
      {count !== undefined && (
        <span className="text-xs text-gray-500 ml-0.5">
          ({count})
        </span>
      )}
    </div>
  );
}
