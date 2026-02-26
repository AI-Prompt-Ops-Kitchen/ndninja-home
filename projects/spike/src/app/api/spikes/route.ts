import { NextRequest, NextResponse } from 'next/server';
import sql from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const order = req.nextUrl.searchParams.get('order') || 'desc';
  const limit = Math.min(Number(req.nextUrl.searchParams.get('limit') || 100), 500);

  const spikes = order === 'asc'
    ? await sql`SELECT * FROM spikes WHERE user_id = ${user.id} ORDER BY logged_at ASC LIMIT ${limit}`
    : await sql`SELECT * FROM spikes WHERE user_id = ${user.id} ORDER BY logged_at DESC LIMIT ${limit}`;

  return NextResponse.json({ spikes });
}

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await req.json();
  const { type, intensity, notes, logged_at } = body;

  if (!type || !intensity) {
    return NextResponse.json({ error: 'type and intensity required' }, { status: 400 });
  }

  const rows = await sql`
    INSERT INTO spikes (user_id, type, intensity, notes, logged_at)
    VALUES (${user.id}, ${type}, ${intensity}, ${notes || null}, ${logged_at || new Date().toISOString()})
    RETURNING id
  `;

  return NextResponse.json({ id: rows[0].id });
}
