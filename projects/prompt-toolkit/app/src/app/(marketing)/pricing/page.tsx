'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Navbar } from '@/components/layout/navbar';
import { Footer } from '@/components/layout/footer';
import { PricingCard } from '@/components/PricingCard';
import { FadeIn } from '@/components/PageTransition';
import { Sparkles, ChevronDown, ChevronUp } from 'lucide-react';

const PLANS = [
  {
    name: 'Free',
    price: '$0',
    annualPrice: '$0',
    period: 'forever',
    description: 'Perfect for getting started with better prompts.',
    features: [
      'Browse all public prompts',
      'Copy up to 10 prompts/day',
      'Save up to 20 favorites',
      'Community ratings & reviews',
      'Basic search & filters',
    ],
    cta: 'Get Started Free',
    href: '/auth/signup',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$9.99',
    annualPrice: '$7.99',
    period: '/month',
    description: 'For professionals who rely on AI prompts daily.',
    features: [
      'Everything in Free',
      'Unlimited prompt copies',
      'Unlimited favorites & collections',
      'Create & publish your own prompts',
      'Prompt DNA breakdowns',
      'Usage analytics dashboard',
      'Priority support',
      'Early access to new features',
    ],
    cta: 'Start 14-Day Free Trial',
    href: '/auth/signup?plan=pro',
    highlighted: true,
  },
  {
    name: 'Team',
    price: '$24.99',
    annualPrice: '$19.99',
    period: '/seat/month',
    description: 'Shared prompt library for teams and organizations.',
    features: [
      'Everything in Pro',
      'Up to 25 team members',
      'Shared prompt collections',
      'Team analytics & insights',
      'Custom categories & tags',
      'API access (10K req/mo)',
      'SSO / SAML authentication',
      'Dedicated support channel',
    ],
    cta: 'Start Team Trial',
    href: '/auth/signup?plan=team',
    highlighted: false,
  },
];

const FAQS = [
  {
    question: 'Can I try Pro for free?',
    answer: 'Absolutely! Every Pro plan starts with a 14-day free trial. No credit card required. If you don\'t upgrade, you\'ll automatically drop back to the Free tier — no charges, no surprises.',
  },
  {
    question: 'What counts as a "prompt copy"?',
    answer: 'Each time you click the Copy button on a prompt, that counts as one copy. The Free tier allows 10 copies per day. Pro and Team plans include unlimited copies.',
  },
  {
    question: 'Can I publish my own prompts on the Free plan?',
    answer: 'Publishing your own prompts is a Pro feature. On the Free plan, you can browse, copy, and favorite existing prompts. Upgrade to Pro to start sharing your creations with the community.',
  },
  {
    question: 'How does team billing work?',
    answer: 'Team plans are billed per seat. You only pay for active team members. Add or remove seats anytime — we prorate automatically. Volume discounts are available for teams of 10+.',
  },
  {
    question: 'What AI models do your prompts support?',
    answer: 'Our prompts are tested across ChatGPT (GPT-4, GPT-4o), Claude, Gemini, and Llama. Each prompt lists the specific models it\'s optimized for, so you always know what to expect.',
  },
  {
    question: 'Is there an API?',
    answer: 'Yes! Team plan includes API access with 10,000 requests per month. Use it to integrate PromptKit into your own tools, IDEs, or workflows. Pro users can request API access on a case-by-case basis.',
  },
  {
    question: 'Can I cancel anytime?',
    answer: 'Yes, cancel anytime with no penalties. You\'ll keep access until the end of your current billing period. All your data (favorites, created prompts) stays intact if you return later.',
  },
];

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
          {/* Header */}
          <FadeIn>
            <div className="text-center mb-12">
              <motion.div
                className="inline-flex items-center gap-2 rounded-full bg-indigo-600/10 border border-indigo-600/20 px-4 py-1.5 text-sm text-indigo-400 mb-6"
                whileHover={{ scale: 1.02 }}
              >
                <Sparkles className="h-4 w-4" />
                Simple, transparent pricing
              </motion.div>
              <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                Choose your plan
              </h1>
              <p className="text-gray-400 max-w-xl mx-auto text-lg">
                Start free. Upgrade when you need more. No hidden fees, cancel anytime.
              </p>
            </div>
          </FadeIn>

          {/* Billing Toggle */}
          <FadeIn delay={0.1}>
            <div className="flex items-center justify-center gap-4 mb-12">
              <span className={`text-sm ${!isAnnual ? 'text-white font-medium' : 'text-gray-500'}`}>Monthly</span>
              <button
                onClick={() => setIsAnnual(!isAnnual)}
                className={`relative h-7 w-14 rounded-full transition-colors ${
                  isAnnual ? 'bg-indigo-600' : 'bg-gray-700'
                }`}
              >
                <motion.span
                  className="absolute top-0.5 h-6 w-6 rounded-full bg-white shadow-md"
                  animate={{ left: isAnnual ? '30px' : '2px' }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                />
              </button>
              <span className={`text-sm ${isAnnual ? 'text-white font-medium' : 'text-gray-500'}`}>
                Annual
                <span className="ml-1.5 text-xs text-green-400 font-medium bg-green-500/10 px-1.5 py-0.5 rounded-full">
                  Save 20%
                </span>
              </span>
            </div>
          </FadeIn>

          {/* Plans */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-24">
            {PLANS.map((plan, i) => (
              <PricingCard
                key={plan.name}
                {...plan}
                isAnnual={isAnnual}
                delay={i * 0.1}
              />
            ))}
          </div>

          {/* FAQs */}
          <div className="max-w-2xl mx-auto">
            <FadeIn>
              <h2 className="text-2xl font-bold text-white text-center mb-8">
                Frequently Asked Questions
              </h2>
            </FadeIn>

            <div className="space-y-3">
              {FAQS.map((faq, i) => (
                <FadeIn key={i} delay={i * 0.03}>
                  <div className="rounded-xl border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors">
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full flex items-center justify-between p-4 text-left"
                    >
                      <span className="text-sm font-medium text-white pr-4">{faq.question}</span>
                      <motion.div
                        animate={{ rotate: openFaq === i ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ChevronDown className="h-4 w-4 text-gray-500 flex-shrink-0" />
                      </motion.div>
                    </button>
                    <AnimatePresence>
                      {openFaq === i && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="px-4 pb-4 text-sm text-gray-400 leading-relaxed">
                            {faq.answer}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
