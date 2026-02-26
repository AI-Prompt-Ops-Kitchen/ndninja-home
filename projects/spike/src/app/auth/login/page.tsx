'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { motion } from 'framer-motion';
import { Zap, Mail, Check, KeyRound } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !pin.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), pin: pin.trim() }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed');

      setSuccess(true);
      setTimeout(() => router.push('/log'), 800);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      {/* Soft background glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-violet-600/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 left-1/3 w-64 h-64 bg-sky-600/5 rounded-full blur-[100px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-sm relative z-10"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-sky-600 mb-4">
            <Zap size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">Spike</h1>
          <p className="text-sm text-gray-500 mt-1">Mood spike tracker</p>
        </div>

        <Card className="border-gray-800">
          <CardContent className="py-6">
            {success ? (
              <div className="text-center space-y-4">
                <div className="mx-auto w-14 h-14 rounded-full bg-emerald-600/15 text-emerald-400 flex items-center justify-center animate-success">
                  <Check size={28} />
                </div>
                <p className="text-gray-200 font-medium">You&apos;re in!</p>
              </div>
            ) : (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-400 mb-2">
                    Email address
                  </label>
                  <div className="relative">
                    <Mail size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                      autoFocus
                      className="w-full rounded-xl border border-gray-800 bg-gray-950/50 py-3 pl-11 pr-4 text-gray-200 placeholder:text-gray-600 focus:border-violet-600/50 focus:ring-2 focus:ring-violet-600/20 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="pin" className="block text-sm font-medium text-gray-400 mb-2">
                    PIN
                  </label>
                  <div className="relative">
                    <KeyRound size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      id="pin"
                      type="password"
                      inputMode="numeric"
                      value={pin}
                      onChange={(e) => setPin(e.target.value)}
                      placeholder="Enter PIN"
                      required
                      className="w-full rounded-xl border border-gray-800 bg-gray-950/50 py-3 pl-11 pr-4 text-gray-200 text-center text-xl tracking-[0.2em] font-mono placeholder:text-gray-700 focus:border-violet-600/50 focus:ring-2 focus:ring-violet-600/20 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                {error && (
                  <p className="text-sm text-amber-400 bg-amber-600/10 px-3 py-2 rounded-lg">
                    {error}
                  </p>
                )}

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  className="w-full"
                  disabled={loading || !email.trim() || !pin.trim()}
                >
                  {loading ? 'Signing in...' : 'Sign in'}
                </Button>

                <p className="text-xs text-gray-600 text-center">
                  Personal app — PIN-protected access
                </p>
              </form>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
