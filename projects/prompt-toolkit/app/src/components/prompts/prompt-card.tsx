import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Heart, Copy, Star } from 'lucide-react';
import { formatNumber } from '@/lib/utils';
import type { Prompt } from '@/types';

interface PromptCardProps {
  prompt: Prompt;
}

export function PromptCard({ prompt }: PromptCardProps) {
  return (
    <Link href={`/prompt/${prompt.slug}`}>
      <Card hover className="h-full">
        <CardContent className="p-5 flex flex-col h-full">
          {/* Category & Difficulty */}
          <div className="flex items-center gap-2 mb-3">
            {prompt.category && (
              <Badge variant="info">{prompt.category.name}</Badge>
            )}
            <Badge>{prompt.difficulty}</Badge>
            {prompt.is_pro_only && (
              <Badge variant="warning">PRO</Badge>
            )}
          </div>

          {/* Title & Description */}
          <h3 className="text-base font-semibold text-white mb-2 line-clamp-2">
            {prompt.title}
          </h3>
          <p className="text-sm text-gray-400 mb-4 line-clamp-2 flex-1">
            {prompt.description}
          </p>

          {/* AI Models */}
          {prompt.ai_model_tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-4">
              {prompt.ai_model_tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Stats */}
          <div className="flex items-center gap-4 text-xs text-gray-500 pt-3 border-t border-gray-800">
            <span className="flex items-center gap-1">
              <Copy className="h-3.5 w-3.5" />
              {formatNumber(prompt.copy_count)}
            </span>
            <span className="flex items-center gap-1">
              <Heart className="h-3.5 w-3.5" />
              {formatNumber(prompt.favorite_count)}
            </span>
            {prompt.rating_count > 0 && (
              <span className="flex items-center gap-1">
                <Star className="h-3.5 w-3.5 text-yellow-500" />
                {prompt.rating_avg.toFixed(1)}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
