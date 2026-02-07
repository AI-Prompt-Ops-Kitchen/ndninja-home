import { Navbar } from '@/components/layout/navbar';
import { Footer } from '@/components/layout/footer';
import { Card, CardContent } from '@/components/ui/card';
import { Sparkles, Target, Users, Zap } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1">
        <div className="mx-auto max-w-4xl px-4 py-20 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-16">
            <h1 className="text-4xl font-bold text-white mb-4">
              About PromptKit
            </h1>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              We believe the gap between &quot;meh AI output&quot; and &quot;holy shit that&apos;s good&quot;
              is almost always the prompt. PromptKit closes that gap.
            </p>
          </div>

          {/* Story */}
          <div className="prose prose-invert max-w-none mb-16">
            <div className="space-y-6 text-gray-400 leading-relaxed">
              <p>
                PromptKit started as a personal Notion database — a collection of prompts
                that actually worked, refined through hundreds of hours of testing across
                ChatGPT, Claude, Gemini, and others.
              </p>
              <p>
                Friends kept asking for access. Then their teams did. Then strangers on
                Twitter. It became clear that most people struggle with the same thing:
                knowing what to tell AI to get the output they actually want.
              </p>
              <p>
                So we built PromptKit — a curated, searchable, community-rated library
                of prompts for every use case. Each prompt is battle-tested, version-controlled,
                and designed to work across multiple AI models.
              </p>
            </div>
          </div>

          {/* Values */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            {[
              {
                icon: Target,
                title: 'Quality Over Quantity',
                description:
                  'Every prompt is tested and refined. We\'d rather have 200 prompts that work than 10,000 that don\'t.',
              },
              {
                icon: Users,
                title: 'Community-Driven',
                description:
                  'Ratings, reviews, and contributions from thousands of prompt engineers make the toolkit better every day.',
              },
              {
                icon: Zap,
                title: 'Practical First',
                description:
                  'No theory papers. No academic jargon. Just prompts you can copy, customize, and use in 30 seconds.',
              },
            ].map((value) => (
              <Card key={value.title}>
                <CardContent className="p-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600/10 mb-4">
                    <value.icon className="h-5 w-5 text-indigo-400" />
                  </div>
                  <h3 className="text-base font-semibold text-white mb-2">{value.title}</h3>
                  <p className="text-sm text-gray-400">{value.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Tech stack callout */}
          <Card className="border-indigo-600/20">
            <CardContent className="p-8 text-center">
              <Sparkles className="h-8 w-8 text-indigo-400 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-white mb-2">Built with Modern Tech</h2>
              <p className="text-sm text-gray-400 max-w-lg mx-auto">
                Next.js, PostgreSQL, Supabase, and Capacitor. Open-source tools, battle-tested
                infrastructure. Available on web, iOS, and Android.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>

      <Footer />
    </div>
  );
}
