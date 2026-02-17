import { ChartsClient } from './charts-client';
import { createClient } from '@/lib/supabase/server';

export default async function ChartsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  let spikes: any[] = [];

  if (user) {
    const { data } = await supabase
      .from('spikes')
      .select('*')
      .eq('user_id', user.id)
      .order('logged_at', { ascending: true });

    spikes = data || [];
  }

  return <ChartsClient initialSpikes={spikes} />;
}
