import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get('token');
  if (token !== process.env.ADMIN_LOGIN_TOKEN) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const email = request.nextUrl.searchParams.get('email');
  if (!email) {
    return NextResponse.json({ error: 'email required' }, { status: 400 });
  }

  // Use service role to generate a magic link and extract the OTP
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;

  const res = await fetch(`${supabaseUrl}/auth/v1/admin/generate_link`, {
    method: 'POST',
    headers: {
      apikey: serviceKey!,
      Authorization: `Bearer ${serviceKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ type: 'magiclink', email }),
  });

  const data = await res.json();
  if (!data.email_otp) {
    return NextResponse.json({ error: 'failed to generate link', data }, { status: 500 });
  }

  // Now verify the OTP to create a session
  const cookieStore = await cookies();
  const supabase = createServerClient(
    supabaseUrl!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll(); },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        },
      },
    }
  );

  const { error } = await supabase.auth.verifyOtp({
    email,
    token: data.email_otp,
    type: 'email',
  });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // Build redirect using the host header so it works via Tailscale IP
  const host = request.headers.get('host') || 'localhost:3333';
  const proto = request.headers.get('x-forwarded-proto') || 'http';
  return NextResponse.redirect(`${proto}://${host}/log`);
}
