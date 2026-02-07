'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Search,
  Heart,
  User,
  Sparkles,
  PlusCircle,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/browse', label: 'Browse', icon: Search },
  { href: '/dashboard', label: 'My Prompts', icon: Sparkles },
  { href: '/dashboard', label: 'Favorites', icon: Heart },
  { href: '/dashboard', label: 'Analytics', icon: BarChart3 },
  { href: '/profile', label: 'Profile', icon: User },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'hidden lg:flex lg:flex-col border-r border-gray-800 bg-gray-950/50 min-h-[calc(100vh-4rem)] transition-all duration-300 relative',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-6 z-10 flex h-6 w-6 items-center justify-center rounded-full border border-gray-700 bg-gray-900 text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
      >
        {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
      </button>

      <div className="flex-1 px-3 py-4 space-y-1">
        {/* New Prompt button */}
        <Link
          href="/dashboard"
          className={cn(
            'flex items-center rounded-xl bg-gradient-to-r from-indigo-600/10 to-purple-600/10 border border-indigo-600/20 text-sm font-medium text-indigo-400 hover:from-indigo-600/20 hover:to-purple-600/20 transition-all duration-200 mb-4',
            collapsed ? 'justify-center px-2 py-2.5' : 'gap-3 px-3 py-2.5'
          )}
        >
          <PlusCircle className="h-4 w-4 flex-shrink-0" />
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden whitespace-nowrap"
              >
                New Prompt
              </motion.span>
            )}
          </AnimatePresence>
        </Link>

        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                'flex items-center rounded-xl text-sm transition-all duration-200 relative group',
                collapsed ? 'justify-center px-2 py-2.5' : 'gap-3 px-3 py-2.5',
                isActive
                  ? 'bg-gray-800/80 text-white shadow-sm'
                  : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200'
              )}
            >
              {/* Active indicator */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-indigo-500 rounded-r-full"
                  transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                />
              )}

              <item.icon className="h-4 w-4 flex-shrink-0" />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className="overflow-hidden whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>

              {/* Tooltip for collapsed state */}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-gray-800 text-gray-200 text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 border border-gray-700">
                  {item.label}
                </div>
              )}
            </Link>
          );
        })}
      </div>

      {/* Bottom section */}
      <div className="border-t border-gray-800 px-3 py-4 space-y-1">
        {/* Pro upgrade card - only when expanded */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="rounded-xl bg-gradient-to-br from-indigo-600/10 to-purple-600/10 border border-indigo-600/20 p-3 mb-3 overflow-hidden"
            >
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-4 w-4 text-indigo-400" />
                <span className="text-sm font-medium text-white">Upgrade to Pro</span>
              </div>
              <p className="text-xs text-gray-400 mb-2">Unlock unlimited prompts & analytics</p>
              <Link
                href="/pricing"
                className="block text-center text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors py-1.5 rounded-lg border border-indigo-600/20 hover:bg-indigo-600/10"
              >
                View Plans
              </Link>
            </motion.div>
          )}
        </AnimatePresence>

        <Link
          href="/profile"
          className={cn(
            'flex items-center rounded-xl text-sm text-gray-400 hover:bg-gray-800/40 hover:text-gray-200 transition-all duration-200',
            collapsed ? 'justify-center px-2 py-2.5' : 'gap-3 px-3 py-2.5'
          )}
        >
          <Settings className="h-4 w-4 flex-shrink-0" />
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="overflow-hidden whitespace-nowrap"
              >
                Settings
              </motion.span>
            )}
          </AnimatePresence>
        </Link>
      </div>
    </aside>
  );
}
