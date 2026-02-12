import { notFound } from 'next/navigation';
import { getPromptBySlug, getRelatedPrompts } from '@/lib/supabase/queries';
import { PromptDetailClient } from './prompt-detail-client';
import type { Metadata } from 'next';

interface PromptDetailPageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PromptDetailPageProps): Promise<Metadata> {
  const { slug } = await params;
  const prompt = await getPromptBySlug(slug);

  if (!prompt) {
    return { title: 'Prompt Not Found | Prompt Toolkit' };
  }

  return {
    title: `${prompt.title} | Prompt Toolkit`,
    description: prompt.description,
    openGraph: {
      title: prompt.title,
      description: prompt.description,
      type: 'article',
    },
  };
}

export default async function PromptDetailPage({ params }: PromptDetailPageProps) {
  const { slug } = await params;
  const prompt = await getPromptBySlug(slug);

  if (!prompt) {
    notFound();
  }

  const related = await getRelatedPrompts(prompt.category, slug, 3);

  return <PromptDetailClient prompt={prompt} related={related} />;
}
