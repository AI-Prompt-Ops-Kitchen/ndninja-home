import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Use service role to bypass RLS for waitlist inserts
// (anon role only has INSERT, not SELECT — so we can't get the position back)
function getServiceClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) throw new Error('Supabase env vars missing');
  return createClient(url, key);
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => null);
    if (!body || typeof body.email !== 'string') {
      return NextResponse.json({ error: 'Email is required' }, { status: 400 });
    }

    const email = body.email.trim().toLowerCase();
    if (!isValidEmail(email)) {
      return NextResponse.json({ error: 'Invalid email address' }, { status: 400 });
    }

    const source = typeof body.source === 'string' ? body.source.slice(0, 50) : 'landing';
    const referrer = req.headers.get('referer') || null;

    // Extract UTM params from body metadata
    const metadata: Record<string, string> = {};
    if (body.utm_source) metadata.utm_source = String(body.utm_source).slice(0, 100);
    if (body.utm_medium) metadata.utm_medium = String(body.utm_medium).slice(0, 100);
    if (body.utm_campaign) metadata.utm_campaign = String(body.utm_campaign).slice(0, 100);

    const supabase = getServiceClient();

    const { data, error } = await supabase
      .from('waitlist')
      .insert({ email, source, referrer, metadata })
      .select('position')
      .single();

    if (error) {
      // Duplicate email → already signed up
      if (error.code === '23505') {
        const { data: existing } = await supabase
          .from('waitlist')
          .select('position')
          .eq('email', email)
          .single();
        return NextResponse.json({
          success: true,
          already: true,
          position: existing?.position || null,
          message: "You're already on the waitlist!",
        });
      }
      console.error('waitlist insert error:', error);
      return NextResponse.json({ error: 'Failed to join waitlist' }, { status: 500 });
    }

    // Get total count for social proof
    const { count } = await supabase
      .from('waitlist')
      .select('id', { count: 'exact', head: true });

    return NextResponse.json({
      success: true,
      position: data?.position,
      total: count || 1,
      message: `You're #${data?.position} on the waitlist!`,
    });
  } catch (err) {
    console.error('waitlist route error:', err);
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}

export async function GET() {
  // Public count endpoint for social proof display
  try {
    const supabase = getServiceClient();
    const { count } = await supabase
      .from('waitlist')
      .select('id', { count: 'exact', head: true });
    return NextResponse.json({ count: count || 0 });
  } catch {
    return NextResponse.json({ count: 0 });
  }
}
