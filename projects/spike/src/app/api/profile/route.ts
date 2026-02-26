import { NextRequest, NextResponse } from 'next/server';
import sql from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const rows = await sql`SELECT * FROM profiles WHERE user_id = ${user.id} LIMIT 1`;
  return NextResponse.json({ profile: rows[0] || null, email: user.email });
}

export async function PATCH(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await req.json();
  const { doctor_email, timezone, daily_digest, weekly_digest } = body;

  await sql`
    UPDATE profiles SET
      doctor_email = ${doctor_email ?? null},
      timezone = ${timezone ?? 'America/New_York'},
      daily_digest = ${daily_digest ?? false},
      weekly_digest = ${weekly_digest ?? false},
      updated_at = now()
    WHERE user_id = ${user.id}
  `;

  return NextResponse.json({ ok: true });
}
