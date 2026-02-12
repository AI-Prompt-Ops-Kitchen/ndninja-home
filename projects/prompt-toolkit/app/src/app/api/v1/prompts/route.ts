import { NextRequest, NextResponse } from 'next/server';
import { getPrompts, getPromptBySlug } from '@/lib/supabase/queries';

// GET /api/v1/prompts — List prompts with search/filter/pagination
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q') || '';
  const category = searchParams.get('category') || '';
  const difficulty = searchParams.get('difficulty') || '';
  const sort = searchParams.get('sort') || 'popular';
  const page = parseInt(searchParams.get('page') || '1');
  const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 50);
  const slug = searchParams.get('slug') || '';

  // Single prompt by slug
  if (slug) {
    const prompt = await getPromptBySlug(slug);
    if (!prompt) {
      return NextResponse.json({ error: 'Prompt not found' }, { status: 404 });
    }
    return NextResponse.json({ data: prompt });
  }

  // List prompts
  const { data, meta } = await getPrompts({
    category: category || undefined,
    search: query || undefined,
    skillLevel: difficulty || undefined,
    sort,
    page,
    limit,
  });

  return NextResponse.json({
    data,
    meta: {
      ...meta,
      query,
      category,
      difficulty,
      sort,
    },
  });
}

// POST /api/v1/prompts — Create a new prompt
export async function POST(request: NextRequest) {
  // TODO: Authenticate user
  // TODO: Validate with Zod
  // TODO: Insert into database

  try {
    const body = await request.json();

    return NextResponse.json(
      { message: 'Prompt created', data: body },
      { status: 201 }
    );
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body' },
      { status: 400 }
    );
  }
}
