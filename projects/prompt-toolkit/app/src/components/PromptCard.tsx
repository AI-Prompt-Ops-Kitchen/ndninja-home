'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Copy, Heart, Star, Zap } from 'lucide-react';
import { TagBadge } from './TagBadge';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface PromptCardData {
  slug: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  models: string[];
  copies: number;
  favorites: number;
  rating: number;
  isPro?: boolean;
  author?: string;
}

interface PromptCardProps {
  prompt: PromptCardData;
  index?: number;
  className?: string;
}

export function PromptCard({ prompt, index = 0, className }: PromptCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
    >
      <Link href={`/prompt/${prompt.slug}`}>
        <div
          className={cn(
            'group relative h-full rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden',
            'transition-all duration-300',
            'hover:border-gray-700 hover:bg-gray-900/80',
            'hover:shadow-[0_8px_30px_rgba(0,0,0,0.3),0_0_20px_rgba(99,102,241,0.05)]',
            'hover:-translate-y-0.5',
            className
          )}
        >
          {/* Top accent line */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-600/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

          <div className="p-5 flex flex-col h-full">
            {/* Tags row */}
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <TagBadge label={prompt.category} type="category" />
              <TagBadge label={prompt.difficulty} type="difficulty" />
              {prompt.isPro && (
                <Badge variant="pro" size="sm">
                  <Zap className="h-3 w-3 mr-0.5" />
                  PRO
                </Badge>
              )}
            </div>

            {/* Title */}
            <h3 className="text-base font-semibold text-white mb-2 line-clamp-2 group-hover:text-indigo-300 transition-colors duration-200">
              {prompt.title}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-400 mb-4 line-clamp-2 flex-1 leading-relaxed">
              {prompt.description}
            </p>

            {/* Model tags */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {prompt.models.map((model) => (
                <TagBadge key={model} label={model} type="model" />
              ))}
            </div>

            {/* Footer stats */}
            <div className="flex items-center gap-4 text-xs text-gray-500 pt-3 border-t border-gray-800/80">
              <span className="flex items-center gap-1 hover:text-gray-300 transition-colors">
                <Copy className="h-3.5 w-3.5" />
                {prompt.copies.toLocaleString()}
              </span>
              <span className="flex items-center gap-1 hover:text-gray-300 transition-colors">
                <Heart className="h-3.5 w-3.5" />
                {prompt.favorites}
              </span>
              <span className="flex items-center gap-1 ml-auto">
                <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" />
                <span className="text-gray-300 font-medium">{prompt.rating}</span>
              </span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
