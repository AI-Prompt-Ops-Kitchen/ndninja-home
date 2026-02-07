import { NextRequest, NextResponse } from 'next/server';

// GET /api/v1/prompts — List prompts with search/filter/pagination
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q') || '';
  const category = searchParams.get('category') || '';
  const difficulty = searchParams.get('difficulty') || '';
  const sort = searchParams.get('sort') || 'popular';
  const page = parseInt(searchParams.get('page') || '1');
  const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 50);

  // TODO: Replace with actual Supabase query
  // const supabase = await createClient();
  // let query = supabase
  //   .from('prompts')
  //   .select('*, category:categories(*), author:users(id, display_name, avatar_url)')
  //   .eq('status', 'published')
  //   .eq('is_public', true);

  return NextResponse.json({
    data: [],
    meta: {
      page,
      limit,
      total: 0,
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
  // const supabase = await createClient();
  // const { data: { user } } = await supabase.auth.getUser();
  // if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  try {
    const body = await request.json();

    // TODO: Validate with Zod
    // TODO: Insert into database

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
