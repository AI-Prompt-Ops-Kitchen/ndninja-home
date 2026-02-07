# Product Design: Prompt Toolkit SaaS

> **Shadow Council — Product Designer**
> **Date:** 2025-02-05
> **Status:** Initial Design Spec
> **Platforms:** iOS, Android, Web

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Competitive Landscape & White Space](#competitive-landscape--white-space)
3. [Core Features (MVP)](#core-features-mvp)
4. [Standout Features](#standout-features)
5. [UX Flows](#ux-flows)
6. [Gamification & Engagement](#gamification--engagement)
7. [AI-Powered Features](#ai-powered-features)
8. [Accessibility & Neurodivergent Design](#accessibility--neurodivergent-design)
9. [Community Features](#community-features)
10. [Monetization & Pricing Strategy](#monetization--pricing-strategy)
11. [Technical Considerations](#technical-considerations)
12. [Open Questions](#open-questions)

---

## Executive Summary

Every existing prompt tool is either a **static library** (God of Prompt, AIPRM), a **marketplace** (PromptBase), or a **community dump** (FlowGPT). None of them actually *teach you to prompt better*. None of them *learn from your usage*. None of them feel like a tool you'd reach for every single day.

**Our thesis:** The winning prompt app isn't a library — it's a **personal prompting co-pilot** that gets smarter the more you use it. It's the difference between a cookbook and a chef who learns your taste.

**The product in one sentence:**
> *A personal AI prompting co-pilot that helps you find, customize, test, and improve prompts — then learns what works for you.*

---

## Competitive Landscape & White Space

### What Exists

| Product | Model | Strength | Weakness |
|---------|-------|----------|----------|
| God of Prompt | Static library (30K+ prompts, Notion) | Massive catalog, lifetime pricing | No intelligence, no personalization, no native app |
| PromptBase | Marketplace (buy/sell) | Creator economy, specificity | One-off purchases, no improvement loop |
| PromptHero | Freemium library | Text + image, community | Shallow features, no analytics |
| AIPRM | Browser extension | Inline with ChatGPT | Locked to one platform, no mobile |
| FlowGPT | Community platform | Free, community-driven | Quality control nightmare, no curation |

### The White Space (Where We Win)

1. **No one does personalization.** Every tool gives everyone the same prompts. Nobody adapts to *your* use case, industry, or writing style.
2. **No one measures prompt performance.** You use a prompt, get results, and... that's it. No feedback loop. No "this prompt works 3x better than that one."
3. **No one teaches *why*.** They give you fish. Nobody teaches you to fish. There's no "prompt anatomy" or "here's why this works."
4. **No native mobile experience.** It's all web-first. Nobody has a great iOS/Android app that feels native.
5. **No neurodivergent-first design.** ADHD/Autism users are *power users* of AI tools. Nobody designs for them.
6. **No cross-model testing.** Nobody lets you test the same prompt across GPT-4, Claude, Gemini, etc. and compare results side by side.

---

## Core Features (MVP)

These are **non-negotiable at launch**. Without these, we don't ship.

### 1. Smart Prompt Library
- **Organized by domain** (marketing, code, writing, research, education, personal, etc.)
- **Organized by AI model** (ChatGPT, Claude, Gemini, Midjourney, Stable Diffusion, etc.)
- **Organized by skill level** (beginner, intermediate, advanced, expert)
- **Full-text search** with semantic understanding (not just keyword matching)
- **Tags + filters** that actually work (task type, output format, tone, length, industry)

### 2. Prompt Customizer (Fill-in-the-Blanks)
- Every prompt has **customizable variables** highlighted in the template
- Users fill in their specifics (brand name, tone, audience, etc.) via guided form fields
- **Live preview** of the assembled prompt before copying
- Variables have **smart defaults** and **example values** so users aren't staring at blank fields

### 3. One-Tap Copy & Deep Links
- Copy assembled prompt to clipboard in one tap
- **Deep links** to open the prompt directly in ChatGPT, Claude, Gemini web apps
- **Share links** — send a prompt (with or without your customizations) to anyone

### 4. Prompt Collections (Personal Folders)
- Users save favorites into custom collections
- "Recently Used" and "Most Used" auto-collections
- Pin frequently used prompts to a quick-access bar

### 5. Cross-Platform Sync
- Real-time sync across iOS, Android, and web
- Offline access to saved/favorited prompts (mobile)
- Account-based, not device-based

### 6. User Accounts & Profiles
- Sign up with email, Google, Apple
- Profile with bio, industry, preferred AI models
- Privacy-first: no public profile required

---

## Standout Features

These are the features that make someone say *"Oh, this is different."*

### 🧬 1. Prompt DNA (The Anatomy Engine)

**Every prompt in the library is deconstructed.**

Instead of just giving users a prompt to copy, we show them *why it works*:

- **Role Assignment** — highlighted in blue. "You are a senior marketing strategist..."
- **Context Layer** — highlighted in green. "For a B2B SaaS company targeting..."
- **Instruction Core** — highlighted in orange. "Create a 5-step email sequence..."
- **Output Constraints** — highlighted in purple. "Format as a table with columns for..."
- **Tone/Style Modifiers** — highlighted in yellow. "Write in a conversational, witty tone..."

Users can toggle "Prompt DNA" view on any prompt. Over time, they internalize the pattern. **They stop needing the library because they learned the skill.**

This is our moat. Everyone else sells fish. We teach fishing.

### 🔬 2. Prompt Lab (Test & Compare)

A built-in environment where users can:

- **A/B test prompts** — run two variants against the same model, compare outputs side-by-side
- **Cross-model test** — run the same prompt against GPT-4, Claude, Gemini simultaneously (via API keys or our proxy)
- **Version history** — every edit to a prompt is tracked, so you can see how tweaks changed the output
- **Performance scoring** — rate outputs on relevance, quality, and usefulness; the app tracks which prompt versions score highest

**Why this matters:** Nobody else does this. Currently, prompt improvement is entirely vibes-based. We make it data-driven.

### 🎯 3. Prompt Radar (Personalized Recommendations)

After a user has used 10+ prompts, the app starts learning:

- What industries they work in
- What types of outputs they prefer (long-form, bullets, tables, code)
- What AI models they use most
- What time of day they prompt (workflow patterns)

**Prompt Radar** surfaces personalized recommendations:
- "Based on your marketing prompts, you might love this competitor analysis template"
- "You've been writing a lot of blog intros — here's a full content calendar prompt"
- "This prompt was just published by a creator in your industry"

### 🔗 4. Prompt Chains (Multi-Step Workflows)

Many real tasks require **sequences** of prompts, not a single shot. We let users build and share chains:

- **Step 1:** Research prompt → feeds into...
- **Step 2:** Outline prompt → feeds into...
- **Step 3:** Draft prompt → feeds into...
- **Step 4:** Edit/polish prompt

Each step can pass context forward. Users can build chains visually (node-based editor on web, simplified list view on mobile).

**Pre-built chains** for common workflows:
- Blog Post Pipeline (research → outline → draft → SEO optimize → social snippets)
- Product Launch (market research → positioning → copy → email sequence → ad variants)
- Code Review (analyze → refactor suggestions → documentation → test generation)

### 🪄 5. Prompt Remix

Users can take *any* prompt and "remix" it:

- Fork it into their own version
- The original author gets credit (and notification)
- Remixes are linked back to the original, creating **prompt family trees**
- Popular remixes can overtake the original in search rankings
- "Most remixed" becomes a prestige metric for creators

This creates a living, evolving library instead of a static one.

### 📊 6. Prompt Analytics Dashboard

For power users and teams:

- Which prompts you use most
- Average quality rating of outputs
- Time saved estimates (based on task type benchmarks)
- Prompt improvement trends over time
- "Your prompting skill level" based on usage patterns (see Gamification)

---

## UX Flows

### Flow 1: New User Onboarding (< 90 seconds)

```
Welcome Screen
  → "What do you use AI for?" (multi-select: Writing, Marketing, Code, Research, Creative, Personal)
  → "Which AI tools?" (multi-select: ChatGPT, Claude, Gemini, Midjourney, Other)
  → "How would you rate your prompting skills?" (Beginner / Getting There / Advanced)
  → "Here's your personalized starting kit!" (5-8 curated prompts based on answers)
  → First prompt auto-opens in Customizer view
  → Tooltip: "Tap any highlighted section to see why it's there" (Prompt DNA teaser)
  → CTA: "Copy to clipboard" or "Open in [ChatGPT]"
```

**Key principle:** No empty states. The user has value in their hands within 60 seconds of signing up.

**ADHD consideration:** Maximum 4 screens. Progress dots visible. Each screen has ONE decision. Skip button always available.

### Flow 2: Finding a Prompt

```
Home Screen
  → Search bar (prominent, always visible) OR browse categories
  → Search: semantic + keyword hybrid ("help me write better emails" finds email prompts even without "email" in title)
  → Results show: Title, category badge, skill level, ⭐ rating, usage count, "DNA preview" (colored dots showing which prompt components are present)
  → Tap result → Prompt Detail View
    → Full prompt with Prompt DNA highlighting (toggleable)
    → Variable fields pre-filled with smart defaults
    → "Use This Prompt" → copies to clipboard
    → "Customize" → opens Customizer
    → "Add to Collection" → save for later
    → "Remix" → fork your own version
    → "Try in Lab" → open in Prompt Lab for testing
```

**ADHD consideration:** Search results show *visual richness* (badges, colored dots, ratings) so the eye can scan quickly without reading every description. Recent searches persist. Voice search supported.

### Flow 3: Customizing a Prompt

```
Customizer View
  → Prompt template displayed with [variable] fields highlighted
  → Each variable has:
    - Label (e.g., "Your Industry")
    - Helper text (e.g., "e.g., B2B SaaS, e-commerce, healthcare")
    - Smart default (pre-filled based on profile)
    - Dropdown suggestions (based on common values)
  → Live preview panel updates in real-time as variables are filled
  → "Enhance with AI" button → AI suggests improvements to the assembled prompt
  → "Save as My Version" → stores in personal library with custom values
  → "Copy" → clipboard
  → "Open in..." → deep link to AI tool
```

**ADHD consideration:** Variables are visually distinct (colored chips, not just brackets). Progress indicator shows "3 of 5 fields filled." Optional "Fill all with AI" button for when executive function is low.

### Flow 4: Building a Prompt Chain

```
Chain Builder (Web: Visual / Mobile: List)
  → "New Chain" or browse pre-built chains
  → Add steps: search library or write custom
  → Connect steps: define what context passes forward
  → Each step shows input/output preview
  → "Run Chain" → executes in sequence (via Prompt Lab or manual copy flow)
  → Save chain to library or share publicly
```

### Flow 5: Returning User Daily Flow

```
Open App
  → "Good morning! Here's your prompt of the day" (personalized)
  → Quick-access bar: 3-5 most-used prompts
  → "New for you" section: recently added prompts matching their interests
  → Streak indicator (if engaged with gamification)
  → "Continue where you left off" (last chain, last customization)
```

---

## Gamification & Engagement

### The Prompt Mastery System

**Core loop:** Use prompts → Rate outputs → Earn XP → Level up → Unlock features

#### XP Sources
| Action | XP |
|--------|----|
| Use a prompt | +5 |
| Customize a prompt | +10 |
| Rate an output | +5 |
| Complete a chain | +25 |
| Submit a prompt | +50 |
| Get a prompt favorited | +10 per fav |
| Get a prompt remixed | +25 per remix |
| Complete daily challenge | +30 |
| Maintain streak | +5 per day (capped at +50 bonus at 10-day streak) |

#### Levels & Titles
| Level | Title | Unlock |
|-------|-------|--------|
| 1-5 | Prompt Apprentice | Basic features |
| 6-15 | Prompt Crafter | Custom collections, advanced filters |
| 16-30 | Prompt Engineer | Prompt Lab, chain builder |
| 31-50 | Prompt Architect | Analytics dashboard, batch export |
| 51-75 | Prompt Master | Early access to new features, beta testing |
| 76-100 | Prompt Sage | Verified creator badge, featured placement |

**IMPORTANT:** Levels unlock *visibility* of features, not *access*. Paid users can access everything immediately. Levels are a progression *incentive*, not a paywall.

#### Streaks
- **Daily streak:** Use at least one prompt per day
- **Visual:** Fire emoji counter (🔥 7-day streak!)
- **Streak freeze:** Miss a day? Use a freeze (earn 1 per 7-day streak, or buy with XP)
- **Streak rewards:** 7 days = badge, 30 days = profile flair, 100 days = exclusive prompts

#### Daily Challenges
- "Try a prompt from a category you've never used"
- "Remix someone else's prompt"
- "Rate 5 outputs today"
- "Build a 3-step chain"
- Challenges rotate daily, personalized to push users outside comfort zones

#### Leaderboards (Opt-In)
- Weekly "Most Helpful" (prompts with highest ratings)
- "Rising Creator" (new prompt authors gaining traction)
- "Chain Master" (most-used chains)
- **Opt-in only.** No pressure. No shame.

### Anti-Manipulation Design
- XP is for engagement, NOT for gate-keeping features
- No dark patterns (no "you'll lose your streak!" anxiety-inducing notifications)
- Streak notifications are gentle: "Your 5-day streak is still going! 🔥" not "DON'T BREAK YOUR STREAK!!!"
- All gamification can be hidden entirely in settings ("Focus Mode")

---

## AI-Powered Features

This is where we go meta — **using AI to help people prompt AI better**.

### 🤖 1. Prompt Coach (Real-Time Improvement)

Users write or paste a prompt → the AI Coach analyzes it and suggests improvements:

- "Your prompt is missing a role assignment. Adding one typically improves output quality by 40%."
- "Consider adding output format constraints. Right now the AI will choose its own format."
- "This prompt is 400 words. Consider breaking it into a chain for better results."
- Shows a **Prompt Score** (0-100) based on structure, specificity, constraints, and clarity

**Interaction model:** Like Grammarly, but for prompts. Inline suggestions with explanations.

### 🧠 2. Smart Prompt Generator

Users describe what they want in plain English:

> "I need to write weekly LinkedIn posts about AI trends for a B2B audience"

The AI generates a complete, structured prompt using best practices, pre-filled with the user's profile data.

- Generates 2-3 variants at different skill levels
- Each variant shows its Prompt DNA breakdown
- User can edit, save, or send directly to their AI tool

### 🔄 3. Prompt Optimizer

Take an existing prompt that's giving mediocre results:

- Paste the prompt + paste the output you got
- AI analyzes what went wrong
- Suggests specific edits with reasoning: "The output was too generic because the prompt lacked audience specificity. Try adding: 'for technical decision-makers at Series B startups.'"
- One-click apply suggestions

### 🌐 4. Model Translator

User has a prompt that works great in ChatGPT but poorly in Claude:

- "Translate" the prompt for a different model
- Adjusts for model-specific strengths (Claude's longer context, GPT-4's instruction following, Gemini's multi-modal, etc.)
- Shows what changed and why

### 📝 5. Context Builder

For complex tasks, help users build rich context:

- Guided interview: "What's your business?" → "Who's your audience?" → "What tone?" → "What format?"
- Assembles a reusable **context block** that can prefix any prompt
- Stores as a "Persona" that can be attached to any prompt with one tap
- "Work mode," "Personal mode," "Creative mode" — quick-switch contexts

### 🔮 6. Trend Spotter

Analyzes community usage patterns to surface insights:

- "Prompt chains for content calendars are trending this week (+340%)"
- "New technique: Chain-of-Thought prompting is producing 2x better results for analysis tasks"
- Weekly digest email/notification with prompting tips and trends

---

## Accessibility & Neurodivergent Design

**This is not an afterthought. This is a competitive advantage.**

ADHD and autistic users are disproportionately represented among AI power users. Designing for them makes the app better for everyone.

### ADHD-First Principles

#### 1. Reduce Decision Paralysis
- **Never show an empty screen.** Always have defaults, suggestions, "start here" prompts.
- **Limit choices per screen.** Max 5-7 options visible. Use progressive disclosure for the rest.
- **"Just Pick One For Me" button** on every selection screen. AI picks based on profile + usage history.
- **Smart defaults everywhere.** Variables pre-filled, settings pre-configured, collections pre-populated.

#### 2. Support Hyperfocus
- **Focus Mode:** Strips the UI to just the current task. No sidebar, no notifications, no "you might also like."
- **Chain Runner:** Once a user starts a prompt chain, the app guides them step-by-step with no distractions.
- **Session Timer (optional):** Gentle "you've been in the zone for 45 minutes" nudge. Not a nag — a celebration.

#### 3. Reduce Friction to Zero
- **One-tap actions** for everything. Copy, save, share, remix — never more than one tap.
- **Persistent search bar** — always accessible, never buried.
- **Voice input** for search and prompt writing (speak your intent, AI structures it).
- **"Continue where I left off"** — app always remembers your last state.

#### 4. Support Working Memory
- **Breadcrumbs** — always show where you are (Home > Marketing > Email > Cold Outreach)
- **Recent history sidebar** — last 10 prompts used, always one tap away
- **Clipboard history** — see your last 5 copied prompts (in-app)
- **Floating action notes** — jot a quick note while customizing a prompt without leaving the screen

### Autism-Friendly Principles

#### 1. Predictable, Consistent UI
- **No surprise modals or pop-ups.** All dialogs are user-initiated.
- **Consistent layout across every screen.** Navigation never moves. Buttons are always in the same place.
- **Explicit, literal labels.** "Copy to Clipboard" not "Grab It." "Save to Collection" not "Stash It."
- **No ambiguous icons without labels.** Every icon has a text label. Always.

#### 2. Sensory Comfort
- **Light/Dark/Custom themes.** Including a high-contrast mode and a "muted colors" mode.
- **Reduced motion toggle.** Disables all animations, transitions, and auto-scrolling.
- **No auto-playing anything.** No videos, no animated tutorials, no bouncing elements.
- **Adjustable text size** — system-level AND in-app override.
- **Monospace font option** for prompt viewing (many ND users prefer fixed-width for readability).

#### 3. Clear Information Architecture
- **Explicit categorization.** No "miscellaneous" categories. Everything has a clear home.
- **Sorting options are explicit** — "Most Popular," "Newest," "Highest Rated," "Most Used by You"
- **Filter state is always visible.** User always knows what filters are active.
- **Preview before action.** Always show what will happen before it happens (prompt preview, chain preview, etc.)

#### 4. Communication Preferences
- **Notification granularity:** Users can control EVERY notification type independently.
- **No urgency language** in notifications. No "Don't miss out!" No FOMO triggers.
- **Email digest options:** Real-time, daily, weekly, never. Per category.
- **Quiet hours built in.** Respects system DND and adds app-level quiet hours.

### Universal Accessibility
- **WCAG 2.2 AA compliance** minimum, AAA where feasible
- **Screen reader optimized** — full VoiceOver/TalkBack support
- **Keyboard navigation** (web) — every action reachable without a mouse
- **Dynamic Type support** (iOS) and system font scaling (Android)
- **RTL language support** from launch architecture (even if not localized yet)
- **Color-blind safe palette** — no information conveyed by color alone

---

## Community Features

### Prompt Marketplace

#### For Users
- Browse user-submitted prompts alongside official library
- **Quality tiers:**
  - ⭐ Staff Picks (curated by our team)
  - 🏆 Community Favorites (highest rated)
  - 🆕 New Submissions (recent, unvetted)
  - 🧪 Experimental (creative/unusual approaches)
- Rate prompts (1-5 stars) + leave usage notes ("Worked great for cold emails, not as good for warm leads")
- Report low-quality or misleading prompts

#### For Creators
- Submit prompts with description, category, variables, and Prompt DNA annotations
- Creator dashboard: views, favorites, remixes, ratings
- **Revenue share program (future phase):** Top creators can monetize premium prompts
- Verified Creator badge at Level 76+ or by application
- Portfolio page showing all their prompts + stats

### Remix / Fork System
- Any public prompt can be remixed (like GitHub fork)
- Remixes link back to the original with full lineage tree
- Original author gets credit and notification
- "Remix Chain" shows the evolution of a prompt idea
- Remixes can be public or private

### Community Interaction
- **Comments on prompts** — usage tips, variations, results sharing
- **"This worked for me" / "Didn't work for me"** quick feedback (low-effort signal)
- **Follow creators** — get notified when they publish new prompts
- **Collections sharing** — publish a curated collection ("My Top 10 Marketing Prompts") as a mini-guide

### Moderation & Quality
- AI-assisted moderation (flag low-quality, detect spam/duplicates)
- Community flagging with human review
- Quality score algorithm: rating + usage + recency + remix count
- No anonymous submissions — all tied to accounts (reduces spam)

### Community Challenges (Monthly)
- "Best prompt for [theme]" competitions
- Voting by community
- Winners get featured placement + XP + profile badge
- Themes rotate: productivity, creative writing, business, code, fun/experimental

---

## Monetization & Pricing Strategy

### Tier Structure

#### 🆓 Free Tier — "Apprentice"
- Access to 500+ curated prompts (rotating selection)
- Basic search and filters
- 5 saved prompts in personal library
- Prompt DNA view (limited to 3 per day)
- Community browsing (read-only)
- Basic Prompt Coach (5 analyses per day)

#### 💰 Pro — $9.99/mo ($7.99/mo annual)  — "Engineer"
- **Full library access** (all prompts, all categories)
- **Unlimited** saves, collections, and customizations
- **Prompt Lab** — A/B testing and cross-model comparison
- **Prompt Coach** — unlimited AI-powered prompt analysis
- **Smart Generator** — unlimited AI prompt generation
- **Prompt Chains** — build and run multi-step workflows
- **Full community access** — submit, rate, comment, remix
- **Analytics dashboard**
- **Priority search** — results weighted by your usage patterns
- **Offline access** — full library available offline on mobile

#### 🏢 Team — $24.99/mo per seat ($19.99 annual) — "Architect"
- Everything in Pro
- **Shared team collections** — collaborate on prompt libraries
- **Team analytics** — usage across the organization
- **Brand context presets** — shared brand voice, audience, and style settings
- **Admin controls** — manage seats, permissions, usage
- **SSO support** — enterprise authentication
- **API access** — integrate prompts into internal tools
- **Custom prompt development** — request custom prompts from our team (limited)

#### 🎯 Enterprise — Custom Pricing
- Everything in Team
- **Dedicated prompt library** — custom prompts for your industry/company
- **On-premise / private cloud** deployment option
- **Custom integrations** — Slack, Teams, internal tools
- **Training & onboarding** for teams
- **SLA and priority support**

### Revenue Diversification (Future)
- **Creator Revenue Share** — top creators earn 70% of premium prompt sales
- **Sponsored Prompts** — brands can sponsor prompts in relevant categories (clearly labeled)
- **Prompt Certification** — paid course + exam → "Certified Prompt Engineer" badge
- **API / SDK** — developers pay per-call to integrate our prompt library and Coach

---

## Technical Considerations

### Architecture Implications
- **PostgreSQL foundation** — already in place, excellent for full-text search, JSONB for flexible prompt schemas
- **Semantic search** — pgvector extension for embedding-based search alongside keyword matching
- **API-first design** — single API serving web, iOS, Android clients
- **Real-time sync** — WebSocket or SSE for cross-device sync
- **Caching layer** — prompt templates are highly cacheable; Redis for hot paths
- **AI integration layer** — abstraction over OpenAI, Anthropic, Google APIs for Prompt Lab / Coach features

### Data Model (Key Entities)
- **Prompt** — template, variables, DNA annotations, metadata, version history
- **Chain** — ordered sequence of prompts with data flow definitions
- **Collection** — user-curated grouping of prompts
- **User** — profile, preferences, usage history, XP/level
- **Rating** — per-prompt, per-user, with optional notes
- **Remix** — fork relationship linking child prompt to parent
- **Session** — Prompt Lab test sessions with inputs/outputs/scores

### Mobile-Specific
- **Share extension** (iOS/Android) — highlight text in any app → "Improve with Prompt Toolkit"
- **Widget** — "Prompt of the Day" home screen widget
- **Keyboard extension** (stretch goal) — access prompts from any text field
- **Siri Shortcuts / Android Quick Actions** — "Hey Siri, give me a prompt for writing emails"

---

## Open Questions

These need answers from the broader council before finalizing:

1. **API key model for Prompt Lab** — Do users bring their own API keys for cross-model testing, or do we proxy through our accounts? (Cost implications are massive.)
2. **Content moderation depth** — How aggressively do we moderate community prompts? AI-only? Human review? Community-driven?
3. **Prompt data ownership** — When a user creates a prompt, can we use anonymized versions to improve our AI features? Privacy policy implications.
4. **Creator monetization timeline** — When do we introduce revenue sharing? Too early = unsustainable. Too late = creators go elsewhere.
5. **Model-specific optimization** — How deep do we go on model-specific prompt tuning? Each model update could invalidate optimizations.
6. **Offline-first architecture** — How much functionality works without internet? Impacts mobile architecture significantly.
7. **Localization priority** — Which languages/markets first after English?
8. **Name** — "Prompt Toolkit" is descriptive but generic. Do we need a more memorable brand name?

---

## What Would Make ME Pay $10/mo

If I'm being honest about what would make this indispensable:

1. **Prompt Coach that actually improves my prompts** — not generic tips, but specific, actionable rewrites based on what I'm trying to do. Like having a prompting expert looking over my shoulder.

2. **The "Just Do It For Me" flow** — I describe what I want in plain English, and the app generates a production-ready prompt. Not a template I have to fill in. A finished, customized prompt.

3. **Prompt Chains for real workflows** — I don't write one prompt at a time. I have workflows. Research → outline → draft → edit. An app that understands multi-step prompting is 10x more useful than a single-prompt library.

4. **Cross-model intelligence** — "This prompt works great in Claude but needs these changes for GPT-4." That kind of model-aware guidance is worth paying for.

5. **Community that surfaces quality** — A curated, rated, remixable library that gets better every week because real users are contributing and rating. PromptBase tried this but made it transactional (buy/sell). We make it collaborative (share/remix/rate).

6. **It makes me better, not dependent** — Prompt DNA is the killer feature. It teaches me the *pattern*, not just the *prompt*. Over time I need the app less for basics but more for advanced features. That's healthy retention.

---

## Design Principles (Summary)

1. **Value in 60 seconds.** First-time user has a useful prompt in hand within a minute.
2. **Teach, don't just serve.** Every interaction should make the user slightly better at prompting.
3. **Personalize everything.** The app should feel different for a marketer vs. a developer vs. a student.
4. **Reduce friction to zero.** One tap to copy. One tap to save. One tap to remix.
5. **Respect neurodivergent users.** Predictable UI, no anxiety triggers, sensory options, executive function support.
6. **Community as flywheel.** More users → more prompts → better recommendations → more users.
7. **AI-native.** Use AI internally to make the AI-prompting experience better. Go meta.
8. **Data-driven improvement.** Measure what works. Surface insights. Close the feedback loop.

---

*Next steps: Architecture review (Engineering), market sizing (Strategist), competitive positioning (Marketing), content pipeline planning (Operations).*
