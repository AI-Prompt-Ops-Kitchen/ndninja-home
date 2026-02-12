import { getPrompts } from '@/lib/supabase/queries';
import { BrowseClient } from './browse-client';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Browse Prompts | Prompt Toolkit',
  description: 'Discover battle-tested AI prompts for every use case — marketing, code, writing, research, and more.',
};

interface BrowsePageProps {
  searchParams: Promise<{
    q?: string;
    category?: string;
    difficulty?: string;
    sort?: string;
    page?: string;
  }>;
}

export default async function BrowsePage({ searchParams }: BrowsePageProps) {
  const params = await searchParams;
  const page = parseInt(params.page || '1');
  const sort = params.sort || 'popular';
  const category = params.category || 'all';
  const difficulty = params.difficulty || '';
  const search = params.q || '';

  const { data: prompts, meta } = await getPrompts({
    category: category !== 'all' ? category : undefined,
    search: search || undefined,
    skillLevel: difficulty || undefined,
    sort,
    page,
    limit: 20,
  });

  return (
    <BrowseClient
      initialPrompts={prompts}
      totalCount={meta.total}
      initialParams={{ search, category, difficulty, sort, page }}
    />
  );
}
