'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { StatsCard } from '@/components/StatsCard';
import { FadeIn, StaggerContainer, StaggerItem } from '@/components/PageTransition';
import {
  User,
  Mail,
  Shield,
  Calendar,
  Edit3,
  Crown,
  Copy,
  Heart,
  Star,
  Bell,
  Palette,
  CreditCard,
  ExternalLink,
  Camera,
  Check,
  Sparkles,
} from 'lucide-react';

const MOCK_USER = {
  display_name: 'Alex Rivera',
  email: 'alex@promptengineer.dev',
  bio: 'Building better AI interactions, one prompt at a time. Specializing in code generation and data analysis prompts.',
  role: 'pro' as const,
  avatar: 'AR',
  created_at: '2024-06-15T00:00:00Z',
  stats: {
    prompts_created: 14,
    total_copies: 4520,
    total_favorites: 234,
    avg_rating: 4.7,
  },
};

const CREATED_PROMPTS = [
  { title: 'Senior Code Reviewer', copies: 1247, rating: 4.8 },
  { title: 'Email Sequence Generator', copies: 654, rating: 4.5 },
  { title: 'API Doc Writer', copies: 432, rating: 4.6 },
  { title: 'Unit Test Generator', copies: 367, rating: 4.7 },
];

const FAVORITED_PROMPTS = [
  { title: 'Chain-of-Thought Engine', author: 'PromptKit Team', rating: 4.9 },
  { title: 'Blog Post Framework', author: 'ContentCraft', rating: 4.9 },
  { title: 'Pitch Deck Builder', author: 'StartupGPT', rating: 4.6 },
];

export default function ProfilePage() {
  const user = MOCK_USER;
  const [activeTab, setActiveTab] = useState<'created' | 'favorites' | 'settings'>('created');

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <FadeIn>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">Profile</h1>
          <Button variant="secondary" size="sm" className="gap-2">
            <Edit3 className="h-4 w-4" />
            Edit Profile
          </Button>
        </div>
      </FadeIn>

      {/* Profile Card */}
      <FadeIn delay={0.05}>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-5">
              {/* Avatar */}
              <div className="relative group">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 text-2xl font-bold text-white shadow-xl shadow-indigo-600/20">
                  {user.avatar}
                </div>
                <button className="absolute inset-0 flex items-center justify-center rounded-2xl bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Camera className="h-5 w-5 text-white" />
                </button>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1 flex-wrap">
                  <h2 className="text-xl font-bold text-white">{user.display_name}</h2>
                  <Badge variant="pro" size="md">
                    <Crown className="h-3 w-3 mr-1" />
                    PRO
                  </Badge>
                </div>

                <p className="text-sm text-gray-400 mb-3 leading-relaxed">{user.bio}</p>

                <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
                  <span className="flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5" />
                    {user.email}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5" />
                    Joined June 2024
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                    Verified Creator
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </FadeIn>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatsCard label="Prompts Created" value={user.stats.prompts_created} icon={Sparkles} />
        <StatsCard label="Total Copies" value={user.stats.total_copies} icon={Copy} />
        <StatsCard label="Total Favorites" value={user.stats.total_favorites} icon={Heart} />
        <StatsCard label="Avg Rating" value={user.stats.avg_rating} icon={Star} decimals={1} />
      </div>

      {/* Tabs */}
      <FadeIn delay={0.1}>
        <div className="flex items-center gap-1 border-b border-gray-800 pb-px">
          {[
            { id: 'created' as const, label: 'Created Prompts', count: CREATED_PROMPTS.length },
            { id: 'favorites' as const, label: 'Favorites', count: FAVORITED_PROMPTS.length },
            { id: 'settings' as const, label: 'Settings' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative px-4 py-2.5 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-white'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-1.5 text-xs text-gray-500">({tab.count})</span>
              )}
              {activeTab === tab.id && (
                <motion.div
                  layoutId="profile-tab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 rounded-full"
                  transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                />
              )}
            </button>
          ))}
        </div>
      </FadeIn>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'created' && (
          <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {CREATED_PROMPTS.map((prompt) => (
              <StaggerItem key={prompt.title}>
                <Card hover className="p-4 cursor-pointer">
                  <h3 className="text-sm font-medium text-white mb-2">{prompt.title}</h3>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Copy className="h-3.5 w-3.5" /> {prompt.copies.toLocaleString()} copies
                    </span>
                    <span className="flex items-center gap-1">
                      <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" /> {prompt.rating}
                    </span>
                  </div>
                </Card>
              </StaggerItem>
            ))}
          </StaggerContainer>
        )}

        {activeTab === 'favorites' && (
          <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {FAVORITED_PROMPTS.map((prompt) => (
              <StaggerItem key={prompt.title}>
                <Card hover className="p-4 cursor-pointer">
                  <h3 className="text-sm font-medium text-white mb-1">{prompt.title}</h3>
                  <p className="text-xs text-gray-500 mb-2">by {prompt.author}</p>
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" /> {prompt.rating}
                  </div>
                </Card>
              </StaggerItem>
            ))}
          </StaggerContainer>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Account */}
            <Card>
              <CardHeader>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <User className="h-4 w-4 text-gray-400" />
                  Account
                </h2>
              </CardHeader>
              <CardContent className="space-y-4 p-6">
                <div>
                  <label className="text-xs font-medium text-gray-400 block mb-1.5">Display Name</label>
                  <input
                    type="text"
                    defaultValue={user.display_name}
                    className="w-full rounded-lg border border-gray-800 bg-gray-950 py-2.5 px-3 text-sm text-gray-200 focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 block mb-1.5">Bio</label>
                  <textarea
                    defaultValue={user.bio}
                    rows={3}
                    className="w-full rounded-lg border border-gray-800 bg-gray-950 py-2.5 px-3 text-sm text-gray-200 focus:border-indigo-600 focus:outline-none focus:ring-1 focus:ring-indigo-600 resize-none"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Preferences */}
            <Card>
              <CardHeader>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Palette className="h-4 w-4 text-gray-400" />
                  Preferences
                </h2>
              </CardHeader>
              <CardContent className="space-y-4 p-6">
                {[
                  { label: 'Dark Mode', desc: 'Use dark theme (recommended)', enabled: true },
                  { label: 'Email Notifications', desc: 'Receive updates about your prompts', enabled: true },
                  { label: 'Weekly Digest', desc: 'Get a summary of trending prompts', enabled: false },
                ].map((pref) => (
                  <div key={pref.label} className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-white">{pref.label}</h3>
                      <p className="text-xs text-gray-500">{pref.desc}</p>
                    </div>
                    <button
                      className={`relative h-6 w-11 rounded-full transition-colors ${
                        pref.enabled ? 'bg-indigo-600' : 'bg-gray-700'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
                          pref.enabled ? 'left-[22px]' : 'left-0.5'
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Subscription */}
            <Card>
              <CardHeader>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <CreditCard className="h-4 w-4 text-gray-400" />
                  Subscription
                </h2>
              </CardHeader>
              <CardContent className="p-6">
                <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-indigo-600/10 to-purple-600/10 border border-indigo-600/20">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-white">Pro Plan</h3>
                      <Badge variant="pro" size="sm">Active</Badge>
                    </div>
                    <p className="text-xs text-gray-400">$9.99/month · Renews Feb 15, 2025</p>
                  </div>
                  <Button variant="secondary" size="sm" className="gap-1.5">
                    Manage <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end pt-2">
              <Button className="gap-2">
                <Check className="h-4 w-4" />
                Save Changes
              </Button>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
