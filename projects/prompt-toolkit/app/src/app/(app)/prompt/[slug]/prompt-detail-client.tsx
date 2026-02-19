'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CopyButton } from '@/components/CopyButton';
import { RatingStars } from '@/components/RatingStars';
import { TagBadge } from '@/components/TagBadge';
import { FadeIn } from '@/components/PageTransition';
import {
  Heart,
  Share2,
  GitFork,
  Eye,
  ChevronLeft,
  Sparkles,
  CheckCircle,
  Dna,
  Lightbulb,
  Zap,
  MessageSquare,
  Star,
} from 'lucide-react';
import type { PromptDetailData, PromptCardData } from '@/types/ui';

interface PromptDetailClientProps {
  prompt: PromptDetailData;
  related: PromptCardData[];
}

export function PromptDetailClient({ prompt, related }: PromptDetailClientProps) {
  const [variableValues, setVariableValues] = useState<Record<string, string>>({});
  const [isFavorited, setIsFavorited] = useState(false);

  const escapeHtml = (str: string): string =>
    str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  const filledPrompt = prompt.content.replace(/\[(\w+)\]/g, (match, key) =>
    variableValues[key] || match
  );

  const highlightContent = (content: string) => {
    // Escape HTML first to prevent XSS, then insert safe <span> tags
    const escaped = escapeHtml(content);
    return escaped.replace(
      /\[(\w+)\]/g,
      '<span class="template-var">[$1]</span>'
    );
  };

  const handleShare = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title: prompt.title, url });
      } catch {
        // User cancelled share
      }
    } else {
      await navigator.clipboard.writeText(url);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-8">
        {/* Main content */}
        <div className="space-y-6 min-w-0">
          {/* Back link */}
          <FadeIn>
            <Link
              href="/browse"
              className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors group"
            >
              <ChevronLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
              Back to Browse
            </Link>
          </FadeIn>

          {/* Header */}
          <FadeIn delay={0.05}>
            <div className="space-y-4">
              <div className="flex items-center gap-2 flex-wrap">
                <TagBadge label={prompt.category} type="category" />
                <TagBadge label={prompt.difficulty} type="difficulty" />
                <Badge variant="default" size="sm">v{prompt.version}</Badge>
              </div>

              <h1 className="text-3xl font-bold text-white">{prompt.title}</h1>
              <p className="text-gray-400 leading-relaxed">{prompt.description}</p>

              {/* Meta row */}
              <div className="flex items-center gap-5 text-sm text-gray-500 flex-wrap">
                <span className="flex items-center gap-1.5">
                  <Eye className="h-4 w-4" /> {prompt.view_count.toLocaleString()} views
                </span>
                <span className="flex items-center gap-1.5">
                  <MessageSquare className="h-4 w-4" /> {prompt.copy_count.toLocaleString()} copies
                </span>
                <span className="flex items-center gap-1.5">
                  <Heart className="h-4 w-4" /> {prompt.favorite_count}
                </span>
                {prompt.rating_avg > 0 && (
                  <RatingStars rating={prompt.rating_avg} showValue count={prompt.rating_count} />
                )}
              </div>

              {/* Model tags */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-gray-500">Works with:</span>
                {prompt.ai_model_tags.map((tag) => (
                  <TagBadge key={tag} label={tag} type="model" />
                ))}
              </div>
            </div>
          </FadeIn>

          {/* Action Buttons */}
          <FadeIn delay={0.1}>
            <div className="flex items-center gap-3 flex-wrap">
              <CopyButton
                text={filledPrompt}
                label="Copy Prompt"
                variant="primary"
                size="md"
              />
              <Button
                variant={isFavorited ? 'primary' : 'secondary'}
                className="gap-2"
                onClick={() => setIsFavorited(!isFavorited)}
              >
                <Heart className={`h-4 w-4 ${isFavorited ? 'fill-current' : ''}`} />
                {isFavorited ? 'Favorited' : 'Favorite'}
              </Button>
              <Button variant="secondary" className="gap-2">
                <GitFork className="h-4 w-4" />
                Fork
              </Button>
              <Button variant="ghost" size="icon" onClick={handleShare}>
                <Share2 className="h-4 w-4" />
              </Button>
            </div>
          </FadeIn>

          {/* Template Variables */}
          {prompt.variables.length > 0 && (
            <FadeIn delay={0.15}>
              <Card glow>
                <CardContent className="p-5">
                  <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-indigo-400" />
                    Try It — Fill in Variables
                  </h2>
                  <div className="space-y-4">
                    {prompt.variables.map((v) => (
                      <div key={v.name}>
                        <label className="text-xs font-medium text-gray-400 block mb-1.5">
                          <span className="template-var">{`[${v.name}]`}</span>
                          <span className="ml-2 text-gray-500 font-normal">{v.description}</span>
                        </label>
                        {v.variable_type === 'textarea' ? (
                          <textarea
                            rows={4}
                            placeholder={v.placeholder || v.label}
                            value={variableValues[v.name] || ''}
                            onChange={(e) => setVariableValues({ ...variableValues, [v.name]: e.target.value })}
                            className="w-full rounded-lg border border-gray-800 bg-gray-950 py-2.5 px-3 text-sm text-gray-200 placeholder:text-gray-600 focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600 font-mono resize-y"
                          />
                        ) : v.variable_type === 'select' && v.suggestions ? (
                          <select
                            value={variableValues[v.name] || ''}
                            onChange={(e) => setVariableValues({ ...variableValues, [v.name]: e.target.value })}
                            className="w-full rounded-lg border border-gray-800 bg-gray-950 py-2.5 px-3 text-sm text-gray-200 focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600"
                          >
                            <option value="">Select {v.label}...</option>
                            {v.suggestions.map((s) => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="text"
                            placeholder={v.placeholder || v.label}
                            value={variableValues[v.name] || ''}
                            onChange={(e) => setVariableValues({ ...variableValues, [v.name]: e.target.value })}
                            className="w-full rounded-lg border border-gray-800 bg-gray-950 py-2.5 px-3 text-sm text-gray-200 placeholder:text-gray-600 focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </FadeIn>
          )}

          {/* Prompt Content */}
          <FadeIn delay={0.2}>
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-gray-400" />
                    Main Prompt
                  </h2>
                  <CopyButton text={filledPrompt} label="Copy" size="sm" variant="ghost" />
                </div>
                <pre
                  className="whitespace-pre-wrap text-sm text-gray-300 bg-gray-950 rounded-lg p-4 border border-gray-800 font-mono leading-relaxed overflow-x-auto"
                  dangerouslySetInnerHTML={{ __html: highlightContent(filledPrompt) }}
                />
              </CardContent>
            </Card>
          </FadeIn>

          {/* System Prompt */}
          {prompt.system_prompt && (
            <FadeIn delay={0.25}>
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      System Prompt
                    </h2>
                    <CopyButton text={prompt.system_prompt} label="Copy" size="sm" variant="ghost" />
                  </div>
                  <pre className="whitespace-pre-wrap text-sm text-gray-300 bg-gray-950 rounded-lg p-4 border border-gray-800 font-mono leading-relaxed">
                    {prompt.system_prompt}
                  </pre>
                </CardContent>
              </Card>
            </FadeIn>
          )}

          {/* Prompt DNA */}
          {prompt.dna && prompt.dna.length > 0 && (
            <FadeIn delay={0.3}>
              <Card>
                <CardContent className="p-5">
                  <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Dna className="h-4 w-4 text-purple-400" />
                    Prompt DNA — Why This Works
                  </h2>
                  <div className="space-y-3">
                    {prompt.dna.map((component, i) => (
                      <motion.div
                        key={`${component.component_type}-${i}`}
                        initial={{ opacity: 0, x: -10 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: i * 0.05 }}
                        className="flex items-start gap-3"
                      >
                        <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium border shrink-0 ${
                          component.color || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
                        }`}>
                          {component.label || component.component_type}
                        </span>
                        <span className="text-sm text-gray-400">{component.explanation}</span>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </FadeIn>
          )}

          {/* Example Output */}
          {prompt.example_output && (
            <FadeIn delay={0.35}>
              <Card>
                <CardContent className="p-5">
                  <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    Example Output
                  </h2>
                  <pre className="whitespace-pre-wrap text-sm text-gray-300 bg-gray-950 rounded-lg p-4 border border-gray-800 leading-relaxed">
                    {prompt.example_output}
                  </pre>
                </CardContent>
              </Card>
            </FadeIn>
          )}

          {/* Use Case */}
          {prompt.use_case && (
            <FadeIn delay={0.4}>
              <Card>
                <CardContent className="p-5">
                  <h2 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-yellow-400" />
                    When to Use This
                  </h2>
                  <p className="text-sm text-gray-400 leading-relaxed">{prompt.use_case}</p>
                </CardContent>
              </Card>
            </FadeIn>
          )}

          {/* Rating Widget */}
          <FadeIn delay={0.45}>
            <Card>
              <CardContent className="p-5 text-center">
                <h2 className="text-sm font-semibold text-white mb-3">Rate This Prompt</h2>
                <RatingStars
                  rating={0}
                  interactive
                  size="lg"
                  className="justify-center"
                  onRate={(r) => console.log('Rated:', r)}
                />
                <p className="text-xs text-gray-500 mt-2">Your rating helps the community find great prompts</p>
              </CardContent>
            </Card>
          </FadeIn>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Creator */}
          <FadeIn delay={0.1} direction="right">
            <Card>
              <CardContent className="p-4">
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Created by</h3>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-xs font-bold text-white">
                    {prompt.author.avatar}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{prompt.author.display_name}</div>
                    <div className="text-xs text-gray-500">Verified Creator</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </FadeIn>

          {/* Meta info */}
          <FadeIn delay={0.15} direction="right">
            <Card>
              <CardContent className="p-4 space-y-3">
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider">Details</h3>
                <div className="space-y-2.5 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">Version</span>
                    <span className="text-gray-300">{prompt.version}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">Created</span>
                    <span className="text-gray-300">{new Date(prompt.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">Updated</span>
                    <span className="text-gray-300">{new Date(prompt.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </FadeIn>

          {/* Related Prompts */}
          {related.length > 0 && (
            <FadeIn delay={0.2} direction="right">
              <Card>
                <CardContent className="p-4">
                  <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Related Prompts</h3>
                  <div className="space-y-3">
                    {related.map((r) => (
                      <Link key={r.slug} href={`/prompt/${r.slug}`}>
                        <div className="group p-2.5 -mx-1 rounded-lg hover:bg-gray-800/50 transition-colors">
                          <h4 className="text-sm font-medium text-gray-300 group-hover:text-indigo-300 transition-colors">
                            {r.title}
                          </h4>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500">{r.category}</span>
                            {r.rating > 0 && (
                              <span className="flex items-center gap-0.5 text-xs text-gray-400">
                                <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                                {r.rating}
                              </span>
                            )}
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </FadeIn>
          )}
        </div>
      </div>
    </div>
  );
}
