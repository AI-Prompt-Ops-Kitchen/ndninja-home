import { NextRequest, NextResponse } from 'next/server';
import sql from '@/lib/db';
import { createSession } from '@/lib/session';
import crypto from 'crypto';

const PIN = process.env.SPIKE_PIN;

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { email, pin } = body;

  if (!email || !pin) {
    return NextResponse.json({ error: 'Email and PIN required' }, { status: 400 });
  }

  if (!PIN || pin !== PIN) {
    return NextResponse.json({ error: 'Invalid PIN' }, { status: 401 });
  }

  // Find or create user
  let rows = await sql`SELECT id, email FROM users WHERE email = ${email}`;

  if (rows.length === 0) {
    const pinHash = crypto.createHash('sha256').update(pin).digest('hex');
    rows = await sql`
      INSERT INTO users (email, pin_hash) VALUES (${email}, ${pinHash})
      RETURNING id, email
    `;
    // Auto-create profile
    await sql`INSERT INTO profiles (user_id) VALUES (${rows[0].id})`;
  }

  const user = rows[0];
  await createSession(user.id);

  return NextResponse.json({ user: { id: user.id, email: user.email } });
}
