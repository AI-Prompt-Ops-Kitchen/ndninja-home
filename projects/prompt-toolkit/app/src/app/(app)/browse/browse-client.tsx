'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useTransition, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { SearchBar } from '@/components/SearchBar';
import { PromptCard } from '@/components/PromptCard';
import { Pagination } from '@/components/Pagination';
import {
  SlidersHorizontal,
  TrendingUp,
  Clock,
  Star,
  Copy,
  X,
  ChevronDown,
  Loader2,
} from 'lucide-react';
import type { PromptCardData } from '@/types/ui';

const CATEGORIES = [
  { name: 'All', slug: 'all' },
  { name: 'Marketing', slug: 'marketing' },
  { name: 'Code', slug: 'code' },
  { name: 'Writing', slug: 'writing' },
  { name: 'Research', slug: 'research' },
  { name: 'Personal', slug: 'personal' },
  { name: 'Business', slug: 'business' },
  { name: 'Education', slug: 'education' },
  { name: 'Creative', slug: 'creative' },
];

const DIFFICULTIES = ['beginner', 'intermediate', 'advanced', 'expert'];

const SORT_OPTIONS = [
  { label: 'Most Popular', value: 'popular', icon: TrendingUp },
  { label: 'Highest Rated', value: 'rated', icon: Star },
  { label: 'Most Copied', value: 'copied', icon: Copy },
  { label: 'Newest', value: 'newest', icon: Clock },
];

interface BrowseClientProps {
  initialPrompts: PromptCardData[];
  totalCount: number;
  initialParams: {
    search: string;
    category: string;
    difficulty: string;
    sort: string;
    page: number;
  };
}

export function BrowseClient({ initialPrompts, totalCount, initialParams }: BrowseClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const activeCategory = searchParams.get('category') || initialParams.category || 'all';
  const activeDifficulty = searchParams.get('difficulty') || initialParams.difficulty || '';
  const sortBy = searchParams.get('sort') || initialParams.sort || 'popular';
  const searchQuery = searchParams.get('q') || initialParams.search || '';
  const currentPage = parseInt(searchParams.get('page') || String(initialParams.page)) || 1;
  const showFilters = activeDifficulty !== '';

  const totalPages = Math.ceil(totalCount / 20);

  const updateParams = useCallback((updates: Record<string, string>) => {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    }
    // Reset to page 1 when filters change (unless we're explicitly setting page)
    if (!('page' in updates)) {
      params.delete('page');
    }
    startTransition(() => {
      router.push(`/browse?${params.toString()}`);
    });
  }, [router, searchParams, startTransition]);

  const handleSearch = useCallback((value: string) => {
    updateParams({ q: value });
  }, [updateParams]);

  const handleCategoryChange = useCallback((slug: string) => {
    updateParams({ category: slug === 'all' ? '' : slug });
  }, [updateParams]);

  const handleDifficultyChange = useCallback((diff: string) => {
    updateParams({ difficulty: activeDifficulty === diff ? '' : diff });
  }, [updateParams, activeDifficulty]);

  const handleSortChange = useCallback((value: string) => {
    updateParams({ sort: value });
  }, [updateParams]);

  const handlePageChange = useCallback((page: number) => {
    updateParams({ page: page > 1 ? String(page) : '' });
  }, [updateParams]);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Loading overlay */}
      {isPending && (
        <div className="fixed top-0 left-0 right-0 z-50">
          <div className="h-1 bg-indigo-600/30">
            <div className="h-full bg-indigo-500 animate-pulse w-2/3" />
          </div>
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Browse Prompts</h1>
        <p className="text-sm text-gray-400 mt-1">
          Discover battle-tested prompts for every use case
        </p>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <SearchBar
          className="flex-1"
          placeholder="Search prompts by name, category, or use case..."
          value={searchQuery}
          onSubmit={handleSearch}
          size="md"
        />
        <Button
          variant={showFilters ? 'primary' : 'secondary'}
          className="gap-2"
          onClick={() => {
            if (activeDifficulty) {
              updateParams({ difficulty: '' });
            }
          }}
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeDifficulty && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500 text-xs text-white">
              1
            </span>
          )}
        </Button>
      </div>

      {/* Filter Panel - Difficulty */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-4">
              <div>
                <h3 className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">Difficulty</h3>
                <div className="flex flex-wrap gap-2">
                  {DIFFICULTIES.map((diff) => (
                    <button
                      key={diff}
                      onClick={() => handleDifficultyChange(diff)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all duration-200 ${
                        activeDifficulty === diff
                          ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-600/30'
                          : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
                      }`}
                    >
                      {diff}
                    </button>
                  ))}
                </div>
              </div>

              {activeDifficulty && (
                <button
                  onClick={() => updateParams({ difficulty: '' })}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
                >
                  <X className="h-3 w-3" /> Clear filters
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Category tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.slug}
            onClick={() => handleCategoryChange(cat.slug)}
            className={`relative whitespace-nowrap rounded-full px-4 py-1.5 text-sm transition-all duration-200 ${
              activeCategory === cat.slug || (cat.slug === 'all' && !activeCategory)
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-800 hover:text-gray-200 border border-gray-800 hover:border-gray-700'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Results count + sort */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          {isPending ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading...
            </span>
          ) : (
            <>
              Showing <span className="text-gray-300 font-medium">{initialPrompts.length}</span> of{' '}
              <span className="text-gray-300 font-medium">{totalCount}</span> prompts
            </>
          )}
        </p>
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value)}
            className="appearance-none text-sm bg-gray-900/80 border border-gray-800 rounded-lg pl-3 pr-8 py-1.5 text-gray-400 focus:outline-none focus:border-indigo-600/50 hover:border-gray-700 transition-colors cursor-pointer"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500 pointer-events-none" />
        </div>
      </div>

      {/* Prompt Grid */}
      {initialPrompts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {initialPrompts.map((prompt, i) => (
            <PromptCard key={prompt.slug} prompt={prompt} index={i} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-gray-400 text-lg">No prompts found</p>
          <p className="text-gray-500 text-sm mt-2">Try adjusting your search or filters</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
