import { NextRequest, NextResponse } from 'next/server';
import sql from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { spike_id, started_at, stopped_at } = await req.json();

  await sql`
    INSERT INTO timer_sessions (user_id, spike_id, started_at, stopped_at)
    VALUES (${user.id}, ${spike_id || null}, ${started_at}, ${stopped_at})
  `;

  return NextResponse.json({ ok: true });
}
