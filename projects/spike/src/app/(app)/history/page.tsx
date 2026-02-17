import { HistoryClient } from './history-client';
import { createClient } from '@/lib/supabase/server';

export default async function HistoryPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  let spikes: any[] = [];

  if (user) {
    const { data } = await supabase
      .from('spikes')
      .select('*')
      .eq('user_id', user.id)
      .order('logged_at', { ascending: false })
      .limit(100);

    spikes = data || [];
  }

  return <HistoryClient initialSpikes={spikes} />;
}
