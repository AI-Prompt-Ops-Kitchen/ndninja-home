'use client';

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, CheckCircle, Loader2, Mail } from 'lucide-react';

interface WaitlistFormProps {
  source?: string;
  className?: string;
  compact?: boolean;
}

export function WaitlistForm({ source = 'landing', className = '', compact = false }: WaitlistFormProps) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'already' | 'error'>('idle');
  const [position, setPosition] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || status === 'loading') return;

    setStatus('loading');
    setErrorMsg('');

    try {
      const res = await fetch('/api/v1/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), source }),
      });
      const data = await res.json();

      if (!res.ok) {
        setErrorMsg(data.error || 'Something went wrong. Try again.');
        setStatus('error');
        return;
      }

      setPosition(data.position);
      setStatus(data.already ? 'already' : 'success');
    } catch {
      setErrorMsg('Network error. Please try again.');
      setStatus('error');
    }
  }, [email, source, status]);

  if (status === 'success' || status === 'already') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`flex flex-col items-center gap-3 text-center ${className}`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-600/20 border border-green-600/30">
          <CheckCircle className="h-6 w-6 text-green-400" />
        </div>
        <div>
          <p className="font-semibold text-white">
            {status === 'already' ? "You're already on the list!" : "You're on the list!"}
          </p>
          {position && (
            <p className="text-sm text-gray-400 mt-1">
              You&apos;re <span className="text-indigo-400 font-medium">#{position}</span> in line.
              We&apos;ll email you when beta opens.
            </p>
          )}
          {!position && (
            <p className="text-sm text-gray-400 mt-1">
              We&apos;ll email you when beta opens.
            </p>
          )}
        </div>
      </motion.div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={`w-full ${className}`}>
      <div className={`flex ${compact ? 'flex-row gap-2' : 'flex-col sm:flex-row gap-3'} w-full`}>
        <div className="relative flex-1">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 pointer-events-none" />
          <input
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (status === 'error') setStatus('idle');
            }}
            placeholder="your@email.com"
            required
            className="w-full rounded-xl border border-gray-700 bg-gray-900/80 pl-10 pr-4 py-3 text-sm text-white placeholder:text-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={status === 'loading' || !email.trim()}
          className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 px-6 py-3 text-sm font-semibold text-white transition-all duration-200 shadow-lg shadow-indigo-600/25 hover:shadow-indigo-500/30 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {status === 'loading' ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Joining...
            </>
          ) : (
            <>
              Join Waitlist
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </div>

      <AnimatePresence>
        {status === 'error' && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-2 text-xs text-red-400"
          >
            {errorMsg}
          </motion.p>
        )}
      </AnimatePresence>

      {!compact && (
        <p className="mt-3 text-xs text-gray-600 text-center">
          No spam. Just a heads-up when beta opens. Unsubscribe anytime.
        </p>
      )}
    </form>
  );
}
