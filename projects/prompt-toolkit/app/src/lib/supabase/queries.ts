import { createClient } from './server';
import type { PromptCardData, PromptDetailData, PaginationMeta } from '@/types/ui';

// =============================================================================
// DB → UI Mappers
// =============================================================================

const CATEGORY_DISPLAY: Record<string, string> = {
  marketing: 'Marketing & Sales',
  code: 'Code & Development',
  writing: 'Writing & Content',
  research: 'Research & Analysis',
  personal: 'Personal & Productivity',
  business: 'Business & Strategy',
  education: 'Education & Learning',
  creative: 'Creative & Design',
};

const MODEL_DISPLAY: Record<string, string[]> = {
  universal: ['GPT-4', 'Claude', 'Gemini'],
  gpt4: ['GPT-4'],
  claude: ['Claude'],
  gemini: ['Gemini'],
  llama: ['Llama'],
};

const DNA_LABELS: Record<string, string> = {
  persona: 'Role Definition',
  context: 'Context Setting',
  constraints: 'Constraints',
  format: 'Output Format',
  examples: 'Examples',
  variables: 'Variables',
};

const DNA_COLORS: Record<string, string> = {
  persona: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  context: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  constraints: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  format: 'bg-green-500/20 text-green-400 border-green-500/30',
  examples: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  variables: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function dbRowToCardData(row: any): PromptCardData {
  return {
    slug: row.slug,
    title: row.title,
    description: row.description,
    category: CATEGORY_DISPLAY[row.category] || row.category,
    difficulty: row.skill_level,
    models: MODEL_DISPLAY[row.ai_model] || [row.ai_model],
    copies: row.usage_count || 0,
    favorites: 0,
    rating: row.avg_rating ? parseFloat(row.avg_rating) : 0,
    isPro: false,
    author: row.author_name || undefined,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function dbDetailsToDetailData(prompt: any, variables: any[], dna: any[], author: any): PromptDetailData {
  return {
    title: prompt.title,
    slug: prompt.slug,
    description: prompt.description,
    content: prompt.template,
    system_prompt: null,
    example_output: null,
    use_case: null,
    variables: variables.map((v) => ({
      name: v.name,
      label: v.label,
      description: v.helper_text || v.label,
      placeholder: v.placeholder || '',
      default_value: v.default_value,
      suggestions: v.suggestions,
      required: v.required,
      variable_type: v.variable_type,
    })),
    difficulty: prompt.skill_level,
    category: CATEGORY_DISPLAY[prompt.category] || prompt.category,
    ai_model_tags: MODEL_DISPLAY[prompt.ai_model] || [prompt.ai_model],
    author: {
      display_name: author?.name || 'Unknown',
      avatar: (author?.name || 'U').slice(0, 2).toUpperCase(),
    },
    copy_count: prompt.usage_count || 0,
    favorite_count: 0,
    rating_avg: prompt.avg_rating ? parseFloat(prompt.avg_rating) : 0,
    rating_count: 0,
    view_count: prompt.usage_count || 0,
    version: prompt.version || 1,
    created_at: prompt.created_at,
    updated_at: prompt.updated_at,
    dna: dna.map((d) => ({
      component_type: d.component_type,
      highlight_start: d.highlight_start,
      highlight_end: d.highlight_end,
      explanation: d.explanation,
      why_it_works: d.why_it_works,
      label: DNA_LABELS[d.component_type] || d.component_type,
      color: DNA_COLORS[d.component_type] || 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    })),
  };
}

// =============================================================================
// Sort mapping
// =============================================================================

type SortKey = 'popular' | 'rated' | 'copied' | 'newest';

function getSortColumn(sort: string): { column: string; ascending: boolean } {
  const map: Record<SortKey, { column: string; ascending: boolean }> = {
    popular: { column: 'usage_count', ascending: false },
    rated: { column: 'avg_rating', ascending: false },
    copied: { column: 'usage_count', ascending: false },
    newest: { column: 'created_at', ascending: false },
  };
  return map[sort as SortKey] || map.popular;
}

// =============================================================================
// Query Functions
// =============================================================================

interface GetPromptsParams {
  category?: string;
  search?: string;
  skillLevel?: string;
  sort?: string;
  page?: number;
  limit?: number;
}

export async function getPrompts({
  category,
  search,
  skillLevel,
  sort = 'popular',
  page = 1,
  limit = 20,
}: GetPromptsParams = {}): Promise<{ data: PromptCardData[]; meta: PaginationMeta }> {
  const supabase = await createClient();
  const offset = (page - 1) * limit;
  const { column, ascending } = getSortColumn(sort);

  // If there's a search query, use text search
  if (search && search.trim()) {
    return searchPrompts({ query: search, category, skillLevel, sort, page, limit });
  }

  // Build the query on prompts_with_author view
  let query = supabase
    .from('prompts_with_author')
    .select('*', { count: 'exact' })
    .eq('status', 'published');

  if (category && category !== 'all') {
    query = query.eq('category', category);
  }
  if (skillLevel) {
    query = query.eq('skill_level', skillLevel);
  }

  query = query
    .order(column, { ascending, nullsFirst: false })
    .range(offset, offset + limit - 1);

  const { data, error, count } = await query;

  if (error) {
    console.error('getPrompts error:', error);
    return { data: [], meta: { page, limit, total: 0 } };
  }

  return {
    data: (data || []).map(dbRowToCardData),
    meta: { page, limit, total: count || 0 },
  };
}

interface SearchPromptsParams {
  query: string;
  category?: string;
  skillLevel?: string;
  sort?: string;
  page?: number;
  limit?: number;
}

export async function searchPrompts({
  query,
  category,
  skillLevel,
  sort = 'popular',
  page = 1,
  limit = 20,
}: SearchPromptsParams): Promise<{ data: PromptCardData[]; meta: PaginationMeta }> {
  const supabase = await createClient();
  const offset = (page - 1) * limit;
  const { column, ascending } = getSortColumn(sort);

  let dbQuery = supabase
    .from('prompts_with_author')
    .select('*', { count: 'exact' })
    .eq('status', 'published')
    .textSearch('search_vector', query, { type: 'websearch' });

  if (category && category !== 'all') {
    dbQuery = dbQuery.eq('category', category);
  }
  if (skillLevel) {
    dbQuery = dbQuery.eq('skill_level', skillLevel);
  }

  dbQuery = dbQuery
    .order(column, { ascending, nullsFirst: false })
    .range(offset, offset + limit - 1);

  const { data, error, count } = await dbQuery;

  if (error) {
    console.error('searchPrompts error:', error);
    return { data: [], meta: { page, limit, total: 0 } };
  }

  return {
    data: (data || []).map(dbRowToCardData),
    meta: { page, limit, total: count || 0 },
  };
}

export async function getPromptBySlug(slug: string): Promise<PromptDetailData | null> {
  const supabase = await createClient();

  // Call the get_prompt_details RPC function
  const { data, error } = await supabase.rpc('get_prompt_details', {
    prompt_slug: slug,
  });

  if (error) {
    console.error('getPromptBySlug error:', error);
    return null;
  }

  if (!data || !data.prompt) {
    return null;
  }

  return dbDetailsToDetailData(
    data.prompt,
    data.variables || [],
    data.dna || [],
    data.author
  );
}

export async function getRelatedPrompts(
  category: string,
  excludeSlug: string,
  limit: number = 3
): Promise<PromptCardData[]> {
  const supabase = await createClient();

  // Reverse-map display name back to enum
  const categoryEnum = Object.entries(CATEGORY_DISPLAY).find(
    ([, display]) => display === category
  )?.[0] || category;

  const { data, error } = await supabase
    .from('prompts_with_author')
    .select('*')
    .eq('status', 'published')
    .eq('category', categoryEnum)
    .neq('slug', excludeSlug)
    .order('usage_count', { ascending: false })
    .limit(limit);

  if (error) {
    console.error('getRelatedPrompts error:', error);
    return [];
  }

  return (data || []).map(dbRowToCardData);
}

// Re-export for convenience
export { CATEGORY_DISPLAY, DNA_LABELS, DNA_COLORS };
