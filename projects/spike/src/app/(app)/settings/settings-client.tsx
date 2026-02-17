'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { createClient } from '@/lib/supabase/client';
import { Profile } from '@/types/spike';
import { cn } from '@/lib/utils';
import { Save, Mail, Clock, LogOut, Check, Send } from 'lucide-react';

const TIMEZONES = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Anchorage',
  'Pacific/Honolulu',
  'Europe/London',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Australia/Sydney',
  'UTC',
];

function tzLabel(tz: string): string {
  try {
    const now = new Date();
    const offset = now.toLocaleString('en-US', { timeZone: tz, timeZoneName: 'short' }).split(' ').pop();
    return `${tz.replace(/_/g, ' ').split('/').pop()} (${offset})`;
  } catch {
    return tz;
  }
}

interface SettingsClientProps {
  profile: Profile | null;
  userEmail: string;
}

export function SettingsClient({ profile, userEmail }: SettingsClientProps) {
  const router = useRouter();
  const [doctorEmail, setDoctorEmail] = useState(profile?.doctor_email || '');
  const [timezone, setTimezone] = useState(profile?.timezone || 'America/New_York');
  const [dailyDigest, setDailyDigest] = useState(profile?.daily_digest || false);
  const [weeklyDigest, setWeeklyDigest] = useState(profile?.weekly_digest || false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = useCallback(async () => {
    if (!profile) return;
    setSaving(true);
    setSaved(false);

    try {
      const supabase = createClient();
      const { error } = await supabase
        .from('profiles')
        .update({
          doctor_email: doctorEmail.trim() || null,
          timezone,
          daily_digest: dailyDigest,
          weekly_digest: weeklyDigest,
          updated_at: new Date().toISOString(),
        })
        .eq('user_id', profile.user_id);

      if (error) throw error;
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setSaving(false);
    }
  }, [profile, doctorEmail, timezone, dailyDigest, weeklyDigest]);

  const handleSignOut = useCallback(async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push('/auth/login');
  }, [router]);

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-gray-100">Settings</h1>

      {/* Account */}
      <Card>
        <CardContent className="py-4 space-y-1">
          <span className="text-xs text-gray-500 uppercase tracking-wider">Account</span>
          <p className="text-sm text-gray-300">{userEmail}</p>
        </CardContent>
      </Card>

      {/* Doctor email */}
      <Card>
        <CardContent className="py-4 space-y-3">
          <div className="flex items-center gap-2">
            <Mail size={16} className="text-gray-500" />
            <span className="text-sm font-medium text-gray-300">Doctor&apos;s email</span>
          </div>
          <input
            type="email"
            value={doctorEmail}
            onChange={(e) => setDoctorEmail(e.target.value)}
            placeholder="doctor@example.com"
            className="w-full rounded-xl border border-gray-700 bg-gray-900 py-3 px-4 text-sm text-gray-200 placeholder:text-gray-600 focus:border-violet-600/50 focus:ring-2 focus:ring-violet-600/20 focus:outline-none transition-all"
          />
          <p className="text-xs text-gray-600">
            Reports will be sent to this email address
          </p>
        </CardContent>
      </Card>

      {/* Digest toggles */}
      <Card>
        <CardContent className="py-4 space-y-4">
          <span className="text-xs text-gray-500 uppercase tracking-wider">Email reports</span>

          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <p className="text-sm text-gray-300">Daily digest</p>
              <p className="text-xs text-gray-600">Sent every morning at 8 AM</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={dailyDigest}
              onClick={() => setDailyDigest(!dailyDigest)}
              className={cn(
                'relative w-11 h-6 rounded-full transition-colors',
                dailyDigest ? 'bg-violet-600' : 'bg-gray-700'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform',
                  dailyDigest && 'translate-x-5'
                )}
              />
            </button>
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <div>
              <p className="text-sm text-gray-300">Weekly digest</p>
              <p className="text-xs text-gray-600">Sent every Sunday at 9 AM</p>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={weeklyDigest}
              onClick={() => setWeeklyDigest(!weeklyDigest)}
              className={cn(
                'relative w-11 h-6 rounded-full transition-colors',
                weeklyDigest ? 'bg-violet-600' : 'bg-gray-700'
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform',
                  weeklyDigest && 'translate-x-5'
                )}
              />
            </button>
          </label>
        </CardContent>
      </Card>

      {/* Timezone */}
      <Card>
        <CardContent className="py-4 space-y-3">
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-500" />
            <span className="text-sm font-medium text-gray-300">Timezone</span>
          </div>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="w-full rounded-xl border border-gray-700 bg-gray-900 py-3 px-4 text-sm text-gray-200 focus:border-violet-600/50 focus:ring-2 focus:ring-violet-600/20 focus:outline-none transition-all appearance-none"
          >
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>{tzLabel(tz)}</option>
            ))}
          </select>
        </CardContent>
      </Card>

      {/* Save button */}
      <Button
        variant={saved ? 'success' : 'primary'}
        size="lg"
        className="w-full gap-2"
        onClick={handleSave}
        disabled={saving}
      >
        {saved ? (
          <>
            <Check size={18} />
            Saved
          </>
        ) : saving ? (
          'Saving...'
        ) : (
          <>
            <Save size={18} />
            Save settings
          </>
        )}
      </Button>

      {/* Test report */}
      {doctorEmail && (dailyDigest || weeklyDigest) && (
        <Button
          variant="secondary"
          size="md"
          className="w-full gap-2"
          onClick={async () => {
            try {
              await fetch('/api/send-test-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ report_type: 'daily' }),
              });
            } catch {}
          }}
        >
          <Send size={16} />
          Send test report
        </Button>
      )}

      {/* Sign out */}
      <Button
        variant="ghost"
        size="md"
        className="w-full gap-2 text-gray-500"
        onClick={handleSignOut}
      >
        <LogOut size={16} />
        Sign out
      </Button>
    </div>
  );
}
