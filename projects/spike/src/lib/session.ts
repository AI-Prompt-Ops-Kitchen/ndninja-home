import { cookies } from 'next/headers';
import sql from './db';

const SESSION_COOKIE = 'spike_session';
const SESSION_MAX_AGE = 60 * 60 * 24 * 90; // 90 days

export interface SessionUser {
  id: string;
  email: string;
}

export async function getSession(): Promise<SessionUser | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;
  if (!token) return null;

  const rows = await sql`
    SELECT id, email FROM users
    WHERE session_token = ${token}
      AND session_expires_at > now()
    LIMIT 1
  `;

  if (rows.length === 0) return null;
  return { id: rows[0].id, email: rows[0].email };
}

export async function createSession(userId: string): Promise<string> {
  const token = crypto.randomUUID() + '-' + crypto.randomUUID();
  const expiresAt = new Date(Date.now() + SESSION_MAX_AGE * 1000);

  await sql`
    UPDATE users SET
      session_token = ${token},
      session_expires_at = ${expiresAt}
    WHERE id = ${userId}
  `;

  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: false, // local server
    sameSite: 'lax',
    maxAge: SESSION_MAX_AGE,
    path: '/',
  });

  return token;
}

export async function destroySession(): Promise<void> {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE)?.value;

  if (token) {
    await sql`UPDATE users SET session_token = NULL, session_expires_at = NULL WHERE session_token = ${token}`;
  }

  cookieStore.set(SESSION_COOKIE, '', { maxAge: 0, path: '/' });
}
