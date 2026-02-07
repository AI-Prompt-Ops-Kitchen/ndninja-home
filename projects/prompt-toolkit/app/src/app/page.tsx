'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/layout/navbar';
import { Footer } from '@/components/layout/footer';
import { Button } from '@/components/ui/button';
import { FeatureCard } from '@/components/FeatureCard';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { FadeIn, StaggerContainer, StaggerItem } from '@/components/PageTransition';
import {
  Sparkles,
  Zap,
  GitFork,
  Link2,
  Shield,
  Globe,
  ArrowRight,
  Copy,
  Star,
  Users,
  Dna,
  FlaskConical,
  Workflow,
  Quote,
  CheckCircle,
} from 'lucide-react';

const STATS = [
  { label: 'Battle-tested Prompts', value: 200, suffix: '+', icon: Sparkles },
  { label: 'Active Users', value: 2500, suffix: '+', icon: Users },
  { label: 'Copies Made', value: 50000, suffix: '+', icon: Copy },
  { label: 'Average Rating', value: 4.8, suffix: '/5', icon: Star, decimals: 1 },
];

const TESTIMONIALS = [
  {
    quote: "PromptKit cut my prompt iteration time by 80%. I used to spend hours tweaking prompts — now I grab a template and customize it in minutes.",
    author: 'Sarah Chen',
    role: 'Senior ML Engineer at Vercel',
    avatar: 'SC',
  },
  {
    quote: "The Prompt DNA feature is genius. Being able to see why a prompt works — not just that it works — has made me a 10x better prompt engineer.",
    author: 'Marcus Johnson',
    role: 'Content Director at HubSpot',
    avatar: 'MJ',
  },
  {
    quote: "We replaced our team's messy Notion doc with PromptKit. Shared collections + version control = no more 'which prompt should I use?' Slack messages.",
    author: 'Priya Patel',
    role: 'Head of AI Ops at Stripe',
    avatar: 'PP',
  },
];

const CATEGORIES = [
  { name: 'Writing & Content', icon: '✍️', count: 48, slug: 'writing' },
  { name: 'Code & Development', icon: '💻', count: 35, slug: 'code' },
  { name: 'Business & Strategy', icon: '📊', count: 29, slug: 'business' },
  { name: 'Creative & Design', icon: '🎨', count: 22, slug: 'creative' },
  { name: 'Education & Learning', icon: '📚', count: 31, slug: 'education' },
  { name: 'AI & Meta-Prompting', icon: '🧠', count: 18, slug: 'meta' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden">
      <Navbar />

      {/* ============ HERO ============ */}
      <section className="relative overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 mesh-gradient" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[700px] bg-indigo-600/[0.07] rounded-full blur-3xl" />
        <div className="absolute top-20 right-[10%] w-72 h-72 bg-purple-600/[0.05] rounded-full blur-3xl animate-float" />
        <div className="absolute top-40 left-[10%] w-64 h-64 bg-cyan-600/[0.04] rounded-full blur-3xl animate-float" style={{ animationDelay: '3s' }} />

        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:64px_64px]" />

        <div className="relative mx-auto max-w-7xl px-4 pt-24 pb-20 sm:px-6 lg:px-8 text-center">
          {/* Badge */}
          <FadeIn delay={0}>
            <motion.div
              className="inline-flex items-center gap-2 rounded-full bg-indigo-600/10 border border-indigo-600/20 px-4 py-1.5 text-sm text-indigo-400 mb-8"
              whileHover={{ scale: 1.02 }}
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
              </span>
              Now in public beta — 200+ prompts and growing
            </motion.div>
          </FadeIn>

          {/* Headline */}
          <FadeIn delay={0.1}>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-white tracking-tight mb-6 leading-[1.05]">
              Craft AI prompts{' '}
              <br className="hidden sm:block" />
              <span className="gradient-text">
                that actually work
              </span>
            </h1>
          </FadeIn>

          {/* Subheadline */}
          <FadeIn delay={0.2}>
            <p className="mx-auto max-w-2xl text-lg sm:text-xl text-gray-400 mb-10 leading-relaxed">
              Stop guessing. Browse battle-tested prompt templates for ChatGPT, Claude, Gemini, and more.
              Copy, customize, and deploy — from the toolkit built by prompt engineers.
            </p>
          </FadeIn>

          {/* CTA Buttons */}
          <FadeIn delay={0.3}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/browse">
                <Button variant="glow" size="lg" className="text-base px-8">
                  Browse Prompts <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
              <Link href="/auth/signup">
                <Button variant="secondary" size="lg" className="text-base px-8">
                  Create Free Account
                </Button>
              </Link>
            </div>
          </FadeIn>

          {/* Stats */}
          <FadeIn delay={0.5}>
            <div className="mt-20 grid grid-cols-2 sm:grid-cols-4 gap-8 max-w-3xl mx-auto">
              {STATS.map((stat) => (
                <div key={stat.label} className="text-center">
                  <stat.icon className="h-5 w-5 text-indigo-400 mx-auto mb-2" />
                  <AnimatedCounter
                    end={stat.value}
                    suffix={stat.suffix}
                    decimals={stat.decimals || 0}
                    className="text-3xl font-bold text-white block"
                  />
                  <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ============ FEATURE TRIO ============ */}
      <section className="relative border-t border-gray-800/50">
        <div className="absolute inset-0 bg-gradient-to-b from-gray-900/30 to-transparent" />
        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
          <FadeIn>
            <div className="text-center mb-16">
              <span className="text-sm font-medium text-indigo-400 mb-3 block">Core Features</span>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Your AI prompt superpower
              </h2>
              <p className="text-gray-400 max-w-xl mx-auto">
                Three powerful tools that transform how you work with AI.
              </p>
            </div>
          </FadeIn>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon={Dna}
              title="Prompt DNA"
              description="See the anatomy of what makes a prompt work. Our DNA view breaks down system prompts, role definitions, constraints, and output formatting — so you learn the patterns, not just the templates."
              gradient="from-indigo-600/10 to-blue-600/10"
              delay={0}
            />
            <FeatureCard
              icon={FlaskConical}
              title="Prompt Lab"
              description="Test and iterate in real-time. Fill in template variables, preview the assembled prompt, tweak parameters, and compare outputs across GPT-4, Claude, and Gemini — all from one interface."
              gradient="from-purple-600/10 to-pink-600/10"
              delay={0.1}
            />
            <FeatureCard
              icon={Workflow}
              title="Prompt Chains"
              description="Link prompts together into powerful workflows. Feed the output of one prompt into the next to build multi-step AI pipelines — perfect for content creation, code review, and data processing."
              gradient="from-cyan-600/10 to-teal-600/10"
              delay={0.2}
            />
          </div>
        </div>
      </section>

      {/* ============ CATEGORIES ============ */}
      <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <FadeIn>
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Browse by Category</h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Organized prompts for every use case. Find what you need in seconds.
            </p>
          </div>
        </FadeIn>

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {CATEGORIES.map((cat) => (
            <StaggerItem key={cat.slug}>
              <Link href={`/browse?category=${cat.slug}`}>
                <motion.div
                  whileHover={{ y: -2, transition: { duration: 0.2 } }}
                  className="group flex items-center gap-4 rounded-xl border border-gray-800 bg-gray-900/50 p-5 hover:border-gray-700 hover:bg-gray-900/80 transition-all duration-300"
                >
                  <span className="text-3xl">{cat.icon}</span>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors">{cat.name}</h3>
                    <p className="text-xs text-gray-500">{cat.count} prompts</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-gray-600 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
                </motion.div>
              </Link>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </section>

      {/* ============ SECONDARY FEATURES ============ */}
      <section className="border-t border-gray-800/50 bg-gray-900/20">
        <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
          <FadeIn>
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Built for Prompt Engineers</h2>
              <p className="text-gray-400 max-w-xl mx-auto">
                Every feature designed around the workflow of crafting and deploying AI prompts.
              </p>
            </div>
          </FadeIn>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Zap, title: 'One-Click Copy', desc: 'Copy any prompt to your clipboard instantly. Variables highlighted and customizable before you paste.' },
              { icon: Shield, title: 'Battle-Tested', desc: 'Every prompt reviewed, rated, and refined by the community. No fluff — just results.' },
              { icon: GitFork, title: 'Fork & Remix', desc: 'Like a prompt but want it different? Fork it, remix the template, and publish your version.' },
              { icon: Globe, title: 'Works Everywhere', desc: 'Web, iOS, Android. Access your prompt library from any device. Offline support for Pro.' },
            ].map((feature, i) => (
              <FadeIn key={feature.title} delay={i * 0.1}>
                <div className="group p-5 rounded-xl border border-gray-800 bg-gray-900/30 hover:border-gray-700 hover:bg-gray-900/50 transition-all duration-300">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600/10 mb-4 group-hover:bg-indigo-600/20 transition-colors">
                    <feature.icon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-xs text-gray-400 leading-relaxed">{feature.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ============ TESTIMONIALS ============ */}
      <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <FadeIn>
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Loved by Prompt Engineers</h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              See what professionals are saying about PromptKit.
            </p>
          </div>
        </FadeIn>

        <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TESTIMONIALS.map((t) => (
            <StaggerItem key={t.author}>
              <div className="relative rounded-2xl border border-gray-800 bg-gray-900/50 p-6 h-full hover:border-gray-700 transition-colors duration-300">
                <Quote className="h-8 w-8 text-indigo-600/30 mb-4" />
                <p className="text-sm text-gray-300 leading-relaxed mb-6">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-xs font-bold text-white">
                    {t.avatar}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-white">{t.author}</div>
                    <div className="text-xs text-gray-500">{t.role}</div>
                  </div>
                </div>
              </div>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </section>

      {/* ============ PRICING PREVIEW ============ */}
      <section className="border-t border-gray-800/50 bg-gray-900/20">
        <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
          <FadeIn>
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Simple, Transparent Pricing</h2>
              <p className="text-gray-400 max-w-xl mx-auto">
                Start free. Upgrade when you need more. No hidden fees.
              </p>
            </div>
          </FadeIn>

          <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              { name: 'Free', price: '$0', period: 'forever', features: ['Browse all prompts', '10 copies/day', '20 favorites', 'Community ratings'], highlighted: false },
              { name: 'Pro', price: '$9.99', period: '/month', features: ['Unlimited copies', 'Create & publish prompts', 'Analytics dashboard', 'Priority support'], highlighted: true },
              { name: 'Team', price: '$24.99', period: '/seat/mo', features: ['Everything in Pro', 'Shared collections', 'Team analytics', 'API access'], highlighted: false },
            ].map((plan) => (
              <StaggerItem key={plan.name}>
                <div
                  className={`relative rounded-2xl border p-6 ${plan.highlighted
                    ? 'border-indigo-600/50 bg-gradient-to-b from-indigo-600/10 to-transparent shadow-[0_0_30px_rgba(99,102,241,0.08)]'
                    : 'border-gray-800 bg-gray-900/50'
                  }`}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="inline-flex items-center gap-1 bg-indigo-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                        <Sparkles className="h-3 w-3" /> Most Popular
                      </span>
                    </div>
                  )}
                  <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mt-2 mb-4">
                    <span className="text-3xl font-bold text-white">{plan.price}</span>
                    <span className="text-sm text-gray-500">{plan.period}</span>
                  </div>
                  <ul className="space-y-2.5 mb-6">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2 text-sm text-gray-300">
                        <CheckCircle className="h-4 w-4 text-indigo-400 flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Link href="/pricing">
                    <Button variant={plan.highlighted ? 'glow' : 'secondary'} className="w-full">
                      {plan.highlighted ? 'Start Pro Trial' : 'Get Started'}
                    </Button>
                  </Link>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>

          <FadeIn delay={0.3}>
            <p className="text-center text-sm text-gray-500 mt-8">
              All plans include access to our full prompt library.{' '}
              <Link href="/pricing" className="text-indigo-400 hover:text-indigo-300 transition-colors">
                See full comparison →
              </Link>
            </p>
          </FadeIn>
        </div>
      </section>

      {/* ============ FINAL CTA ============ */}
      <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <FadeIn>
          <div className="relative rounded-3xl border border-gray-800 overflow-hidden">
            {/* Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/15 via-gray-900 to-purple-600/15" />
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />

            <div className="relative p-12 sm:p-16 text-center">
              <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 shadow-2xl shadow-indigo-600/30 mb-8"
              >
                <Sparkles className="h-8 w-8 text-white" />
              </motion.div>

              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Ready to level up your prompts?
              </h2>
              <p className="text-gray-400 max-w-md mx-auto mb-8 text-lg">
                Join thousands of professionals using PromptKit to get better results from AI — starting today.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/auth/signup">
                  <Button variant="glow" size="lg" className="text-base px-8">
                    Start Free — No Credit Card <ArrowRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
              <p className="text-xs text-gray-600 mt-4">
                Free forever plan available. Upgrade anytime.
              </p>
            </div>
          </div>
        </FadeIn>
      </section>

      <Footer />
    </div>
  );
}
