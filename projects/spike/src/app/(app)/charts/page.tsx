import { ChartsClient } from './charts-client';
import { getSession } from '@/lib/session';
import sql from '@/lib/db';
import { redirect } from 'next/navigation';

export default async function ChartsPage() {
  const user = await getSession();
  if (!user) redirect('/auth/login');

  const spikes = await sql`
    SELECT * FROM spikes
    WHERE user_id = ${user.id}
    ORDER BY logged_at ASC
  `;

  return <ChartsClient initialSpikes={spikes as any[]} />;
}
