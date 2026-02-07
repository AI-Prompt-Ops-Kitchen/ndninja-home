'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { StatsCard } from '@/components/StatsCard';
import { FadeIn, StaggerContainer, StaggerItem } from '@/components/PageTransition';
import {
  BarChart3,
  Copy,
  Heart,
  Eye,
  PlusCircle,
  Sparkles,
  ArrowRight,
  Flame,
  Search,
  Star,
  TrendingUp,
  Calendar,
  Zap,
} from 'lucide-react';

const QUICK_STATS = [
  { label: 'Total Copies', value: 1247, change: '+12%', changeType: 'positive' as const, icon: Copy },
  { label: 'Favorites', value: 89, change: '+5%', changeType: 'positive' as const, icon: Heart },
  { label: 'Views', value: 8432, change: '+23%', changeType: 'positive' as const, icon: Eye },
  { label: 'Day Streak', value: 14, change: 'Active', changeType: 'positive' as const, icon: Flame },
];

const RECENT_ACTIVITY = [
  { type: 'copy', prompt: 'Senior Developer Code Review', time: '2 hours ago', icon: Copy },
  { type: 'favorite', prompt: 'Blog Post Framework Generator', time: '5 hours ago', icon: Heart },
  { type: 'create', prompt: 'Custom API Documentation Writer', time: '1 day ago', icon: PlusCircle },
  { type: 'copy', prompt: 'Chain-of-Thought Reasoning Engine', time: '2 days ago', icon: Copy },
  { type: 'rating', prompt: 'Startup Pitch Deck Builder', time: '3 days ago', icon: Star },
];

const RECENT_PROMPTS = [
  {
    title: 'Senior Developer Code Review',
    status: 'published',
    copies: 342,
    rating: 4.8,
    updated: '2h ago',
    trend: '+18%',
  },
  {
    title: 'Marketing Email Sequence Generator',
    status: 'published',
    copies: 156,
    rating: 4.5,
    updated: '1d ago',
    trend: '+7%',
  },
  {
    title: 'Data Analysis Report Builder',
    status: 'draft',
    copies: 0,
    rating: 0,
    updated: '3d ago',
    trend: null,
  },
];

const WEEKLY_DATA = [
  { day: 'Mon', copies: 34, views: 120 },
  { day: 'Tue', copies: 45, views: 156 },
  { day: 'Wed', copies: 29, views: 98 },
  { day: 'Thu', copies: 67, views: 210 },
  { day: 'Fri', copies: 52, views: 178 },
  { day: 'Sat', copies: 38, views: 134 },
  { day: 'Sun', copies: 41, views: 145 },
];

export default function DashboardPage() {
  const maxViews = Math.max(...WEEKLY_DATA.map((d) => d.views));

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <FadeIn>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              Welcome back
              <motion.span
                animate={{ rotate: [0, 14, -8, 14, -4, 10, 0] }}
                transition={{ duration: 2.5, delay: 0.5 }}
                className="inline-block"
              >
                👋
              </motion.span>
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Here&apos;s how your prompts are performing this week.
            </p>
          </div>
          <Link href="/dashboard">
            <Button className="gap-2 shadow-lg shadow-indigo-600/20">
              <PlusCircle className="h-4 w-4" />
              New Prompt
            </Button>
          </Link>
        </div>
      </FadeIn>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {QUICK_STATS.map((stat, i) => (
          <StatsCard
            key={stat.label}
            label={stat.label}
            value={stat.value}
            change={stat.change}
            changeType={stat.changeType}
            icon={stat.icon}
          />
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Chart - takes 2 cols */}
        <FadeIn className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">Weekly Activity</h2>
                  <p className="text-xs text-gray-500 mt-0.5">Copies and views over the last 7 days</p>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-indigo-500" />
                    Views
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-purple-500" />
                    Copies
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <div className="flex items-end justify-between gap-2 h-40">
                {WEEKLY_DATA.map((day, i) => (
                  <div key={day.day} className="flex-1 flex flex-col items-center gap-1">
                    <div className="w-full flex flex-col items-center gap-1 flex-1 justify-end">
                      <motion.div
                        initial={{ height: 0 }}
                        whileInView={{ height: `${(day.views / maxViews) * 100}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: i * 0.05 }}
                        className="w-full max-w-[28px] bg-indigo-600/30 rounded-t-md relative group"
                      >
                        <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-gray-800 text-gray-300 text-xs px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                          {day.views}
                        </div>
                      </motion.div>
                    </div>
                    <div className="w-full flex flex-col items-center">
                      <motion.div
                        initial={{ height: 0 }}
                        whileInView={{ height: `${(day.copies / maxViews) * 100 * 1.5}px` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5, delay: i * 0.05 + 0.1 }}
                        className="w-full max-w-[28px] bg-purple-600/40 rounded-t-md"
                        style={{ minHeight: day.copies > 0 ? '4px' : '0' }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 mt-1">{day.day}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        {/* Recent Activity Feed */}
        <FadeIn delay={0.1}>
          <Card className="h-full">
            <CardHeader>
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                Recent Activity
              </h2>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-gray-800/50">
                {RECENT_ACTIVITY.map((activity, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-3 px-5 py-3 hover:bg-gray-800/20 transition-colors"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gray-800/80">
                      <activity.icon className="h-3.5 w-3.5 text-gray-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-300 truncate">{activity.prompt}</p>
                      <p className="text-xs text-gray-600">{activity.time}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </FadeIn>
      </div>

      {/* Your Prompts */}
      <FadeIn>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Your Prompts</h2>
              <Button variant="ghost" size="sm" className="gap-1.5 text-gray-400">
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-gray-800/50">
              {RECENT_PROMPTS.map((prompt, i) => (
                <motion.div
                  key={prompt.title}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-800/20 transition-colors cursor-pointer group"
                >
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-white truncate group-hover:text-indigo-300 transition-colors">
                      {prompt.title}
                    </h3>
                    <div className="flex items-center gap-3 mt-1.5">
                      <Badge
                        variant={prompt.status === 'published' ? 'success' : 'default'}
                      >
                        {prompt.status}
                      </Badge>
                      <span className="text-xs text-gray-500">Updated {prompt.updated}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-6 text-sm text-gray-400">
                    <span className="flex items-center gap-1.5">
                      <Copy className="h-3.5 w-3.5" />
                      {prompt.copies}
                    </span>
                    {prompt.rating > 0 && (
                      <span className="flex items-center gap-1">
                        <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" />
                        {prompt.rating}
                      </span>
                    )}
                    {prompt.trend && (
                      <span className="flex items-center gap-1 text-xs text-green-400">
                        <TrendingUp className="h-3 w-3" />
                        {prompt.trend}
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </FadeIn>

      {/* Quick Actions */}
      <StaggerContainer className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { icon: Search, emoji: '🔍', title: 'Browse Prompts', desc: 'Discover new prompts for your workflow', href: '/browse' },
          { icon: Heart, emoji: '❤️', title: 'My Favorites', desc: 'Quick access to saved prompts', href: '/dashboard' },
          { icon: Zap, emoji: '⚡', title: 'Upgrade to Pro', desc: 'Unlock unlimited prompts & analytics', href: '/pricing' },
        ].map((action) => (
          <StaggerItem key={action.title}>
            <Link href={action.href}>
              <motion.div
                whileHover={{ y: -2 }}
                className="p-5 rounded-xl border border-gray-800 bg-gray-900/50 cursor-pointer hover:border-gray-700 hover:bg-gray-900/80 transition-all duration-300 group"
              >
                <span className="text-2xl mb-2 block">{action.emoji}</span>
                <h3 className="text-sm font-medium text-white mb-1 group-hover:text-indigo-300 transition-colors">{action.title}</h3>
                <p className="text-xs text-gray-500">{action.desc}</p>
              </motion.div>
            </Link>
          </StaggerItem>
        ))}
      </StaggerContainer>
    </div>
  );
}
