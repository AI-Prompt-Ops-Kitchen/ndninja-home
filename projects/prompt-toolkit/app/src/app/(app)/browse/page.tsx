'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SearchBar } from '@/components/SearchBar';
import { PromptCard } from '@/components/PromptCard';
import {
  SlidersHorizontal,
  ArrowRight,
  TrendingUp,
  Clock,
  Star,
  Copy,
  X,
  ChevronDown,
} from 'lucide-react';

const CATEGORIES = [
  { name: 'All', slug: 'all' },
  { name: '✍️ Writing', slug: 'writing' },
  { name: '💻 Code', slug: 'code' },
  { name: '📊 Business', slug: 'business' },
  { name: '🎨 Creative', slug: 'creative' },
  { name: '📚 Education', slug: 'education' },
  { name: '🧠 Meta', slug: 'meta' },
  { name: '📈 Marketing', slug: 'marketing' },
  { name: '🔬 Data', slug: 'data' },
];

const MODELS = ['GPT-4', 'GPT-4o', 'Claude', 'Gemini', 'Llama'];
const DIFFICULTIES = ['beginner', 'intermediate', 'advanced', 'expert'];

const SORT_OPTIONS = [
  { label: 'Most Popular', value: 'popular', icon: TrendingUp },
  { label: 'Highest Rated', value: 'rated', icon: Star },
  { label: 'Most Copied', value: 'copied', icon: Copy },
  { label: 'Newest', value: 'newest', icon: Clock },
];

const MOCK_PROMPTS = [
  {
    slug: 'senior-code-reviewer',
    title: 'Senior Developer Code Review',
    description: 'Get expert-level code review feedback with actionable suggestions for improvement, security concerns, and best practices.',
    category: 'Code & Development',
    difficulty: 'advanced',
    models: ['GPT-4', 'Claude'],
    copies: 1247,
    favorites: 89,
    rating: 4.8,
    isPro: false,
  },
  {
    slug: 'blog-post-framework',
    title: 'Blog Post Framework Generator',
    description: 'Generate complete blog post outlines with SEO-optimized headers, hook intro, and compelling CTA structures.',
    category: 'Writing & Content',
    difficulty: 'beginner',
    models: ['GPT-4', 'Claude', 'Gemini'],
    copies: 2341,
    favorites: 156,
    rating: 4.9,
    isPro: false,
  },
  {
    slug: 'startup-pitch-deck',
    title: 'Startup Pitch Deck Builder',
    description: 'Create investor-ready pitch deck content with market analysis, competitive positioning, and financial projections.',
    category: 'Business & Strategy',
    difficulty: 'intermediate',
    models: ['GPT-4', 'Claude'],
    copies: 876,
    favorites: 67,
    rating: 4.6,
    isPro: true,
  },
  {
    slug: 'chain-of-thought-reasoner',
    title: 'Chain-of-Thought Reasoning Engine',
    description: 'A meta-prompt that forces step-by-step reasoning for complex problems. Reduces hallucination and improves accuracy.',
    category: 'AI & Meta-Prompting',
    difficulty: 'expert',
    models: ['GPT-4', 'Claude', 'Gemini'],
    copies: 3102,
    favorites: 234,
    rating: 4.9,
    isPro: false,
  },
  {
    slug: 'email-sequence-generator',
    title: 'Email Nurture Sequence',
    description: 'Build a 5-email nurture sequence with personalization tokens, subject line variants, and conversion-optimized CTAs.',
    category: 'Marketing & Sales',
    difficulty: 'intermediate',
    models: ['GPT-4'],
    copies: 654,
    favorites: 45,
    rating: 4.5,
    isPro: false,
  },
  {
    slug: 'data-analyst-assistant',
    title: 'Data Analysis Report Writer',
    description: 'Turn raw data descriptions into executive-ready analysis reports with insights, visualizations suggestions, and next steps.',
    category: 'Data & Analysis',
    difficulty: 'intermediate',
    models: ['GPT-4', 'Claude'],
    copies: 1089,
    favorites: 78,
    rating: 4.7,
    isPro: true,
  },
  {
    slug: 'ui-component-generator',
    title: 'React Component Generator',
    description: 'Generate production-ready React components with TypeScript, Tailwind CSS, accessibility, and unit test stubs.',
    category: 'Code & Development',
    difficulty: 'intermediate',
    models: ['GPT-4', 'Claude'],
    copies: 1893,
    favorites: 142,
    rating: 4.8,
    isPro: false,
  },
  {
    slug: 'creative-story-engine',
    title: 'Interactive Story Engine',
    description: 'Create branching narrative experiences with character development, plot twists, and reader choice points.',
    category: 'Creative & Design',
    difficulty: 'advanced',
    models: ['GPT-4', 'Claude'],
    copies: 567,
    favorites: 98,
    rating: 4.6,
    isPro: false,
  },
  {
    slug: 'lesson-plan-builder',
    title: 'Adaptive Lesson Plan Builder',
    description: 'Generate differentiated lesson plans aligned to learning standards with assessments, activities, and accommodations.',
    category: 'Education & Learning',
    difficulty: 'beginner',
    models: ['GPT-4', 'Gemini'],
    copies: 789,
    favorites: 56,
    rating: 4.7,
    isPro: false,
  },
];

export default function BrowsePage() {
  const [activeCategory, setActiveCategory] = useState('all');
  const [showFilters, setShowFilters] = useState(false);
  const [activeModels, setActiveModels] = useState<string[]>([]);
  const [activeDifficulty, setActiveDifficulty] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('popular');
  const [searchQuery, setSearchQuery] = useState('');

  const toggleModel = (model: string) => {
    setActiveModels((prev) =>
      prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]
    );
  };

  const activeFilterCount = activeModels.length + (activeDifficulty ? 1 : 0);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
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
          onChange={setSearchQuery}
          size="md"
        />
        <Button
          variant={showFilters ? 'primary' : 'secondary'}
          className="gap-2"
          onClick={() => setShowFilters(!showFilters)}
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500 text-xs text-white">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </div>

      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 space-y-4">
              {/* Model filters */}
              <div>
                <h3 className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">AI Model</h3>
                <div className="flex flex-wrap gap-2">
                  {MODELS.map((model) => (
                    <button
                      key={model}
                      onClick={() => toggleModel(model)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                        activeModels.includes(model)
                          ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-600/30'
                          : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
                      }`}
                    >
                      {model}
                    </button>
                  ))}
                </div>
              </div>

              {/* Difficulty filters */}
              <div>
                <h3 className="text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">Difficulty</h3>
                <div className="flex flex-wrap gap-2">
                  {DIFFICULTIES.map((diff) => (
                    <button
                      key={diff}
                      onClick={() => setActiveDifficulty(activeDifficulty === diff ? null : diff)}
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

              {/* Clear filters */}
              {activeFilterCount > 0 && (
                <button
                  onClick={() => { setActiveModels([]); setActiveDifficulty(null); }}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
                >
                  <X className="h-3 w-3" /> Clear all filters
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
            onClick={() => setActiveCategory(cat.slug)}
            className={`relative whitespace-nowrap rounded-full px-4 py-1.5 text-sm transition-all duration-200 ${
              activeCategory === cat.slug
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
          Showing <span className="text-gray-300 font-medium">{MOCK_PROMPTS.length}</span> prompts
        </p>
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
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
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {MOCK_PROMPTS.map((prompt, i) => (
          <PromptCard key={prompt.slug} prompt={prompt} index={i} />
        ))}
      </div>

      {/* Load more */}
      <div className="text-center pt-6 pb-4">
        <Button variant="secondary" size="lg" className="gap-2 px-8">
          Load More Prompts <ArrowRight className="h-4 w-4" />
        </Button>
        <p className="text-xs text-gray-600 mt-3">
          Showing 9 of 200+ prompts
        </p>
      </div>
    </div>
  );
}
