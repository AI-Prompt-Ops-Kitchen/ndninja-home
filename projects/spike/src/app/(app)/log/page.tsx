'use client';

import { useState, useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { IntensitySlider } from '@/components/ui/intensity-slider';
import { TimerOverlay } from '@/components/ui/timer-overlay';
import { useTimer } from '@/hooks/use-timer';
import { queueSpike } from '@/lib/offline-queue';
import { hapticTap, hapticSuccess } from '@/lib/haptics';
import { getAffirmation } from '@/lib/affirmations';
import { SpikeType } from '@/types/spike';
import { cn, formatDuration } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { Waves, CloudRain, Check, Clock, MessageSquare, ChevronDown } from 'lucide-react';

type LogState = 'select' | 'intensity' | 'success';

function toLocalDatetime(date: Date): string {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function formatDisplayTime(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  const isYesterday = d.toDateString() === yesterday.toDateString();

  const time = d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

  if (isToday) return `Today ${time}`;
  if (isYesterday) return `Yesterday ${time}`;
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true });
}

export default function LogPage() {
  const [state, setState] = useState<LogState>('select');
  const [type, setType] = useState<SpikeType | null>(null);
  const [intensity, setIntensity] = useState(3);
  const [notes, setNotes] = useState('');
  const [showNotes, setShowNotes] = useState(false);
  const [loggedAt, setLoggedAt] = useState(() => toLocalDatetime(new Date()));
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastSpikeId, setLastSpikeId] = useState<string | null>(null);
  const [timerStarted, setTimerStarted] = useState(false);
  const [showTimer, setShowTimer] = useState(false);
  const [savedDuration, setSavedDuration] = useState<number | null>(null);
  const [affirmation, setAffirmation] = useState('');

  const timer = useTimer({
    spikeId: lastSpikeId,
    onComplete: (duration) => {
      setSavedDuration(duration);
      setTimerStarted(false);
      hapticSuccess();
    },
  });

  const handleTypeSelect = useCallback((t: SpikeType) => {
    hapticTap();
    setType(t);
    setLoggedAt(toLocalDatetime(new Date()));
    setState('intensity');
  }, []);

  const handleLog = useCallback(async () => {
    if (!type) return;
    setLoading(true);

    try {
      if (!navigator.onLine) {
        await queueSpike({
          type,
          intensity,
          logged_at: new Date(loggedAt).toISOString(),
          created_at: new Date().toISOString(),
        });
        hapticSuccess();
        setAffirmation(getAffirmation());
        setState('success');
        setShowTimer(false);
        return;
      }

      const res = await fetch('/api/spikes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type,
          intensity,
          notes: notes.trim() || null,
          logged_at: new Date(loggedAt).toISOString(),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setLastSpikeId(data.id || null);
      hapticSuccess();
      setAffirmation(getAffirmation());
      setState('success');
      const logTime = new Date(loggedAt).getTime();
      setShowTimer(Math.abs(Date.now() - logTime) < 60000);
    } catch (err) {
      console.error('Failed to log spike:', err);
      hapticSuccess();
      setAffirmation(getAffirmation());
      setState('success');
      setShowTimer(false);
    } finally {
      setLoading(false);
    }
  }, [type, intensity, notes, loggedAt]);

  const handleReset = useCallback(() => {
    timer.dismiss();
    setState('select');
    setType(null);
    setIntensity(3);
    setNotes('');
    setShowNotes(false);
    setShowDatePicker(false);
    setLastSpikeId(null);
    setTimerStarted(false);
    setShowTimer(false);
    setSavedDuration(null);
    setAffirmation('');
  }, [timer]);

  const handleTimerStart = useCallback(() => {
    hapticTap();
    setTimerStarted(true);
    timer.start();
  }, [timer]);

  const handleTimerDismiss = useCallback(() => {
    timer.dismiss();
    setShowTimer(false);
    setTimerStarted(false);
  }, [timer]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)]">
      <AnimatePresence mode="wait">
        {state === 'select' && (
          <motion.div
            key="select"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className="w-full space-y-6"
          >
            <div className="text-center space-y-2">
              <h1 className="text-2xl font-bold text-gray-100">What are you feeling?</h1>
              <p className="text-sm text-gray-500">Tap to start logging</p>
            </div>

            <div className="flex gap-4">
              <motion.div
                className="flex-1"
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  variant="anxiety"
                  size="xl"
                  className="w-full flex-col h-32 rounded-3xl animate-breathe"
                  onClick={() => handleTypeSelect('anxiety')}
                >
                  <Waves size={32} className="mb-2" />
                  <span className="text-lg">Anxiety</span>
                </Button>
              </motion.div>

              <motion.div
                className="flex-1"
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  variant="sadness"
                  size="xl"
                  className="w-full flex-col h-32 rounded-3xl animate-breathe"
                  style={{ animationDelay: '4s' }}
                  onClick={() => handleTypeSelect('sadness')}
                >
                  <CloudRain size={32} className="mb-2" />
                  <span className="text-lg">Sadness</span>
                </Button>
              </motion.div>
            </div>
          </motion.div>
        )}

        {state === 'intensity' && (
          <motion.div
            key="intensity"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className="w-full space-y-5"
          >
            <div className="text-center space-y-2">
              <button
                onClick={() => { hapticTap(); setState('select'); }}
                className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
              >
                &larr; Back
              </button>
              <h1 className="text-2xl font-bold text-gray-100">How intense?</h1>
              <div
                className={cn(
                  'inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium',
                  type === 'anxiety'
                    ? 'bg-violet-600/15 text-violet-300'
                    : 'bg-sky-600/15 text-sky-300'
                )}
              >
                {type === 'anxiety' ? <Waves size={16} /> : <CloudRain size={16} />}
                {type === 'anxiety' ? 'Anxiety' : 'Sadness'}
              </div>
            </div>

            <Card className="border-gray-800">
              <CardContent className="py-6">
                <IntensitySlider
                  value={intensity}
                  onChange={setIntensity}
                  type={type}
                />
              </CardContent>
            </Card>

            {/* Optional notes — collapsible */}
            <button
              type="button"
              onClick={() => { setShowNotes(!showNotes); hapticTap(); }}
              className={cn(
                'w-full flex items-center justify-center gap-2 py-2 text-sm transition-all',
                showNotes ? 'text-gray-300' : 'text-gray-600 hover:text-gray-400'
              )}
            >
              <MessageSquare size={14} />
              <span>{showNotes ? 'Hide notes' : 'Add a note'}</span>
              <ChevronDown size={14} className={cn('transition-transform', showNotes && 'rotate-180')} />
            </button>

            <AnimatePresence>
              {showNotes && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="What triggered it? What helped? (optional)"
                    rows={3}
                    className="w-full rounded-xl border border-gray-700 bg-gray-900 py-3 px-4 text-sm text-gray-200 placeholder:text-gray-600 focus:border-violet-600/50 focus:ring-2 focus:ring-violet-600/20 focus:outline-none transition-all resize-none"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Date/time — defaults to now, tappable to change */}
            <button
              type="button"
              onClick={() => { setShowDatePicker(!showDatePicker); hapticTap(); }}
              className={cn(
                'w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm transition-all',
                showDatePicker
                  ? 'bg-gray-800 text-gray-200 border border-gray-700'
                  : 'text-gray-500 hover:text-gray-300'
              )}
            >
              <Clock size={15} />
              <span>{formatDisplayTime(loggedAt)}</span>
              {!showDatePicker && (
                <span className="text-xs text-gray-600 ml-1">tap to change</span>
              )}
            </button>

            {showDatePicker && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <Card className="border-gray-800">
                  <CardContent className="py-4 space-y-3">
                    <input
                      type="datetime-local"
                      value={loggedAt}
                      max={toLocalDatetime(new Date())}
                      onChange={(e) => setLoggedAt(e.target.value)}
                      className="w-full rounded-xl border border-gray-700 bg-gray-900 py-3 px-4 text-gray-200 focus:border-violet-600/50 focus:ring-2 focus:ring-violet-600/20 focus:outline-none transition-all [color-scheme:dark]"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        setLoggedAt(toLocalDatetime(new Date()));
                        setShowDatePicker(false);
                      }}
                      className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
                    >
                      Reset to now
                    </button>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            <motion.div whileTap={{ scale: 0.97 }}>
              <Button
                variant={type === 'anxiety' ? 'anxiety' : 'sadness'}
                size="xl"
                className="w-full rounded-3xl text-lg font-bold"
                onClick={handleLog}
                disabled={loading}
              >
                {loading ? 'Logging...' : 'Log it'}
              </Button>
            </motion.div>
          </motion.div>
        )}

        {state === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full text-center space-y-6"
          >
            {/* Exhale ring + check icon */}
            <div className="relative flex items-center justify-center">
              {/* Exhale ring — expanding and fading out */}
              <div
                className={cn(
                  'absolute w-20 h-20 rounded-full animate-exhale-ring',
                  type === 'anxiety'
                    ? 'bg-violet-500/20 shadow-[0_0_40px_rgba(139,92,246,0.3)]'
                    : 'bg-sky-500/20 shadow-[0_0_40px_rgba(14,165,233,0.3)]'
                )}
              />
              {/* Second ring, delayed */}
              <div
                className={cn(
                  'absolute w-20 h-20 rounded-full animate-exhale-ring',
                  type === 'anxiety'
                    ? 'bg-violet-500/10'
                    : 'bg-sky-500/10'
                )}
                style={{ animationDelay: '0.3s' }}
              />
              {/* Check icon — drops in */}
              <div
                className={cn(
                  'relative w-20 h-20 rounded-full flex items-center justify-center animate-drop-in',
                  type === 'anxiety'
                    ? 'bg-violet-600/20 text-violet-400'
                    : 'bg-sky-600/20 text-sky-400'
                )}
              >
                <Check size={40} strokeWidth={3} />
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-gray-100">Logged</h2>
              <p className="text-sm text-gray-500">
                {type === 'anxiety' ? 'Anxiety' : 'Sadness'} &middot; Intensity {intensity}/5
              </p>
              <p className="text-xs text-gray-600">{formatDisplayTime(loggedAt)}</p>
              {savedDuration !== null && (
                <p className="text-xs text-gray-500">
                  Duration: {formatDuration(savedDuration)}
                </p>
              )}
            </div>

            {/* Affirmation — fades up gently */}
            {affirmation && (
              <p className="text-sm text-gray-400 italic animate-fade-up px-4">
                &ldquo;{affirmation}&rdquo;
              </p>
            )}

            {/* Timer overlay — only for real-time spikes */}
            {showTimer && type && !savedDuration && (
              <AnimatePresence>
                <TimerOverlay
                  running={timer.running}
                  elapsed={timer.elapsed}
                  type={type}
                  onStop={timer.stop}
                  onDismiss={handleTimerDismiss}
                  onStart={handleTimerStart}
                  started={timerStarted}
                />
              </AnimatePresence>
            )}

            <Button
              variant="ghost"
              size="lg"
              className="mx-auto"
              onClick={handleReset}
            >
              Log another
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
