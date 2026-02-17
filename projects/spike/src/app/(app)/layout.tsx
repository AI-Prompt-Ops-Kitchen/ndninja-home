'use client';

import { BottomNav } from '@/components/layout/bottom-nav';
import { useOnlineSync } from '@/hooks/use-online-sync';
import { motion } from 'framer-motion';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  useOnlineSync(); // Auto-sync offline spikes when online

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <main className="flex-1 pb-20 max-w-lg mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="p-4"
        >
          {children}
        </motion.div>
      </main>
      <BottomNav />
    </div>
  );
}
