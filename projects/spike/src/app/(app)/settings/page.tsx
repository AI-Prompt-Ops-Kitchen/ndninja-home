import { SettingsClient } from './settings-client';
import { createClient } from '@/lib/supabase/server';

export default async function SettingsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  let profile = null;

  if (user) {
    const { data } = await supabase
      .from('profiles')
      .select('*')
      .eq('user_id', user.id)
      .single();

    profile = data;
  }

  return <SettingsClient profile={profile} userEmail={user?.email || ''} />;
}
