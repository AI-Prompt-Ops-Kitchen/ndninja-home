import { NextResponse } from 'next/server';

// GET /api/v1/auth — Get current auth status
export async function GET() {
  // TODO: Implement with Supabase Auth
  // const supabase = await createClient();
  // const { data: { user } } = await supabase.auth.getUser();
  
  return NextResponse.json({
    authenticated: false,
    user: null,
    message: 'Auth endpoint placeholder — connect Supabase to activate',
  });
}
