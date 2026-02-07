'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Sparkles, CheckCircle, ArrowRight } from 'lucide-react';

const BENEFITS = [
  'Browse 200+ battle-tested prompts',
  'Save favorites & build collections',
  'Rate and review prompts',
  'Create & share your own (Pro)',
];

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-950 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 mesh-gradient opacity-50" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-indigo-600/[0.06] rounded-full blur-3xl" />
      <div className="absolute bottom-[20%] left-[10%] w-72 h-72 bg-purple-600/[0.05] rounded-full blur-3xl" />
      <div className="absolute top-[30%] right-[5%] w-64 h-64 bg-cyan-600/[0.04] rounded-full blur-3xl" />

      {/* Grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.02)_1px,transparent_1px)] bg-[size:64px_64px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative w-full max-w-md space-y-6"
      >
        {/* Logo */}
        <div className="text-center">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <motion.div
              whileHover={{ rotate: 12 }}
              transition={{ type: 'spring', stiffness: 300, damping: 15 }}
              className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 shadow-xl shadow-indigo-600/20"
            >
              <Sparkles className="h-5 w-5 text-white" />
            </motion.div>
            <span className="text-2xl font-bold text-white">
              Prompt<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Kit</span>
            </span>
          </Link>
          <p className="text-sm text-gray-400 mt-3">Create your free account</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-gray-800 bg-gray-900/70 backdrop-blur-xl p-6 space-y-5 shadow-2xl shadow-black/20">
          {/* Benefits */}
          <div className="rounded-xl bg-gradient-to-r from-indigo-600/[0.07] to-purple-600/[0.07] border border-indigo-600/10 p-4 space-y-2.5">
            {BENEFITS.map((benefit, i) => (
              <motion.div
                key={benefit}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.08 }}
                className="flex items-center gap-2.5 text-sm text-gray-300"
              >
                <CheckCircle className="h-4 w-4 text-indigo-400 flex-shrink-0" />
                {benefit}
              </motion.div>
            ))}
          </div>

          {/* OAuth */}
          <div className="space-y-3">
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center justify-center gap-3 rounded-xl border border-gray-700 bg-gray-800/50 px-4 py-2.5 text-sm font-medium text-gray-200 hover:bg-gray-800 hover:border-gray-600 transition-all duration-200"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Sign up with Google
            </motion.button>
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              className="w-full flex items-center justify-center gap-3 rounded-xl border border-gray-700 bg-gray-800/50 px-4 py-2.5 text-sm font-medium text-gray-200 hover:bg-gray-800 hover:border-gray-600 transition-all duration-200"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              Sign up with GitHub
            </motion.button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-800" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-gray-900/70 px-3 text-gray-500">or continue with email</span>
            </div>
          </div>

          {/* Email form */}
          <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
            <div>
              <label className="text-xs font-medium text-gray-400 block mb-1.5">
                Display Name
              </label>
              <input
                type="text"
                placeholder="How should we call you?"
                className="w-full rounded-xl border border-gray-800 bg-gray-950/50 py-2.5 px-3.5 text-sm text-gray-200 placeholder:text-gray-600 focus:border-indigo-600/50 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 transition-all"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-400 block mb-1.5">
                Email
              </label>
              <input
                type="email"
                placeholder="you@example.com"
                className="w-full rounded-xl border border-gray-800 bg-gray-950/50 py-2.5 px-3.5 text-sm text-gray-200 placeholder:text-gray-600 focus:border-indigo-600/50 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 transition-all"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-400 block mb-1.5">
                Password
              </label>
              <input
                type="password"
                placeholder="Min 8 characters"
                className="w-full rounded-xl border border-gray-800 bg-gray-950/50 py-2.5 px-3.5 text-sm text-gray-200 placeholder:text-gray-600 focus:border-indigo-600/50 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 transition-all"
              />
            </div>
            <Button className="w-full shadow-lg shadow-indigo-600/20 gap-2" size="lg">
              Create Account <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <p className="text-xs text-gray-600 text-center">
            By signing up, you agree to our{' '}
            <Link href="#" className="text-gray-400 hover:text-gray-300 transition-colors">Terms</Link>
            {' '}and{' '}
            <Link href="#" className="text-gray-400 hover:text-gray-300 transition-colors">Privacy Policy</Link>
          </p>
        </div>

        <p className="text-center text-sm text-gray-500">
          Already have an account?{' '}
          <Link href="/auth/login" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
