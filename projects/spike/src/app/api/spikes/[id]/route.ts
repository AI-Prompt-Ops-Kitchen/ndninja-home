import { NextRequest, NextResponse } from 'next/server';
import sql from '@/lib/db';
import { getSession } from '@/lib/session';

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { id } = await params;
  const body = await req.json();
  const { duration_seconds } = body;

  await sql`
    UPDATE spikes SET duration_seconds = ${duration_seconds}
    WHERE id = ${id} AND user_id = ${user.id}
  `;

  return NextResponse.json({ ok: true });
}
