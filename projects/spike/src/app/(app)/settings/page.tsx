import { SettingsClient } from './settings-client';
import { getSession } from '@/lib/session';
import sql from '@/lib/db';
import { redirect } from 'next/navigation';

export default async function SettingsPage() {
  const user = await getSession();
  if (!user) redirect('/auth/login');

  const rows = await sql`SELECT * FROM profiles WHERE user_id = ${user.id} LIMIT 1`;
  const profile = rows[0] || null;

  return <SettingsClient profile={profile as any} userEmail={user.email} />;
}
