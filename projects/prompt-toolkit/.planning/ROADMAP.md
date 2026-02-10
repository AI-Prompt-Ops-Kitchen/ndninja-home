# Prompt Toolkit SaaS - Implementation Roadmap

> **Shadow Council Validated:** 4.0/5 rating (GPT-5.2, Gemini 3 Pro, Sonar Reasoning Pro)
> **Approach:** MVP-first, thin vertical slices, bootstrapped execution
> **Timeline:** Month 0 → Month 18 ($10K MRR)

---

## Phase 1: Database Schema & Data Foundation (Week 1-2)

**Goal:** Design and implement core data model that supports versioning, attribution, and future marketplace

**Why First:** Shadow Council feedback: "Marketplace plans mean you'll need versioning, attribution, and permissioning. Designing this upfront avoids painful migrations later."

### Must Have
- [ ] Database schema design (prompts, variables, collections, users, versions, forks)
- [ ] Row-Level Security (RLS) policies for all user-owned tables
- [ ] Database migrations (Supabase migrations)
- [ ] Seed data: 25-50 high-quality starter prompts across 5 categories

### Should Have
- [ ] PostgreSQL full-text search setup (tsvector + GIN indexes)
- [ ] Automated RLS tests ("cannot read others' data")
- [ ] Version history tracking structure

### Success Metrics
- All RLS policies pass security audit
- Seed prompts cover core use cases (marketing, code, writing, research, personal)
- Full-text search returns results in <100ms

### Out of Scope
- Advanced search filters (defer to Phase 3)
- Community features
- AI-generated metadata

### Deliverable
`schema.sql` + seed data + RLS test suite + performance benchmarks

---

## Phase 2: MVP Core - Prompt Library (Week 3-4)

**Goal:** Thin vertical slice: Browse, search, view prompts

**Why:** Shadow Council: "Ship 'Prompt Library + Customizer' as a thin vertical slice first. Don't build full taxonomy, advanced search, and Prompt DNA simultaneously."

### Must Have
- [ ] `/browse` page with category navigation
- [ ] Basic text search (PostgreSQL full-text)
- [ ] Prompt detail view (`/prompt/[slug]`)
- [ ] Prompt card component with preview
- [ ] Server-side rendering for SEO
- [ ] Responsive design (mobile-first)

### Should Have
- [ ] Pagination (20 prompts per page)
- [ ] Loading states and skeletons
- [ ] Share links for individual prompts

### Success Metrics
- Browse page loads in <1s
- Search returns results in <500ms
- All prompts accessible on mobile

### Out of Scope
- Advanced filters (category, skill level, AI model)
- Favorites/collections
- Prompt DNA annotations
- User-generated prompts

### Deliverable
Working browse and search experience with 50 seed prompts

---

## Phase 3: Prompt Customizer (Week 5-6)

**Goal:** Variable substitution, live preview, copy-to-clipboard

### Must Have
- [ ] Variable parser (extract `[variable]` placeholders)
- [ ] Customizer UI with form fields
- [ ] Live preview panel
- [ ] Smart defaults based on variable names
- [ ] Copy to clipboard functionality
- [ ] "Open in ChatGPT/Claude" deep links

### Should Have
- [ ] Helper text for each variable
- [ ] Token counter/estimator (per Shadow Council: "Add token estimator and budget warnings")
- [ ] Save customized version (requires auth)
- [ ] Auto-save drafts (localStorage fallback)

### Success Metrics
- Variable substitution works for 100% of seed prompts
- Token counter accurate within 5%
- Copy action completes in <100ms

### Out of Scope
- AI-assisted variable filling
- Prompt templates library
- Batch customization

### Deliverable
Fully functional customizer with token efficiency tooling

---

## Phase 4: User Accounts & Collections (Week 7-8)

**Goal:** Auth, personal library, sync across devices

### Must Have
- [ ] NextAuth integration (email, Google, Apple)
- [ ] User profile page
- [ ] Create/delete collections
- [ ] Add prompts to collections
- [ ] Sync across devices (real-time via Supabase)
- [ ] Auth-gated features (save, customize, collections)

### Should Have
- [ ] Recently used prompts
- [ ] Usage history (last 10 prompts)
- [ ] Account settings (display name, avatar)
- [ ] Rate limiting on signup (per Shadow Council security guidance)

### Success Metrics
- Auth signup completes in <10s
- Collections sync in real-time (<2s latency)
- No data leakage (RLS tests pass)

### Out of Scope
- Team accounts
- SSO
- API access

### Deliverable
Working auth + personal collections system

---

## Phase 5: Landing Page & Waitlist (Week 9-10) — **MONTH 0 MILESTONE**

**Goal:** Public-facing landing page optimized for conversion, waitlist signup

### Must Have
- [ ] Hero section with clear value prop
- [ ] Before/after prompt examples (show the difference)
- [ ] Feature highlights (library, customizer, DNA teaser)
- [ ] Pricing table (Free vs Pro tiers)
- [ ] Waitlist signup form (email capture)
- [ ] Email confirmation flow
- [ ] Analytics (Plausible or similar, privacy-focused)
- [ ] SEO optimization (meta tags, Open Graph, sitemap)

### Should Have
- [ ] Testimonials/social proof (if available)
- [ ] FAQ section
- [ ] "Try a sample prompt" interactive demo
- [ ] Neurodivergent-friendly design (high contrast mode, reduced motion toggle)

### Success Metrics
- **Target: 200 waitlist signups in 2 weeks** (per business plan)
- Landing page loads in <2s (100% Lighthouse score)
- Conversion rate: 10%+ (visitors → signups)

### Out of Scope
- Product Hunt launch (Month 3)
- Full app access (beta only)
- Blog/content marketing

### Deliverable
Live landing page at prompttoolkit.com + 200 waitlist signups

---

## Phase 6: Prompt DNA (Teaching Layer) (Week 11-12)

**Goal:** Differentiated feature — annotate prompts to teach *why* they work

**Why:** Shadow Council: "Treat 'Prompt DNA' as a progressive enhancement with strict token budgets. Implement initially as structured metadata + short teaching notes."

### Must Have
- [ ] Prompt anatomy parser (role, context, instruction, constraints, tone)
- [ ] Color-coded highlighting in prompt view
- [ ] DNA toggle (show/hide annotations)
- [ ] Metadata schema (component types, explanations)
- [ ] Annotate 50 seed prompts with DNA

### Should Have
- [ ] "Why this works" tooltips
- [ ] DNA component library (common patterns)
- [ ] Token budget per annotation (max 50 tokens/component)
- [ ] Linting rules (ensure annotations don't bloat prompts)

### Success Metrics
- 100% of featured prompts have DNA annotations
- Annotations add <10% to prompt length
- User comprehension test: 80%+ understand DNA on first view

### Out of Scope
- AI-generated DNA (manual curation for quality)
- User-contributed DNA
- DNA for chains (defer to Phase 9)

### Deliverable
Prompt DNA feature live on 50 curated prompts + DNA authoring guide

---

## Phase 7: Beta Launch (Web) (Week 13-14) — **MONTH 2 MILESTONE**

**Goal:** Invite 50-100 waitlist users, gather feedback, measure retention

### Must Have
- [ ] Beta invite system (invite codes)
- [ ] Onboarding flow (<90s to first prompt)
- [ ] Activation event tracking (per Shadow Council: "created 1 collection + ran 3 customized prompts within 48h")
- [ ] In-app feedback mechanism (simple form)
- [ ] Usage analytics (activated users, retention, feature usage)
- [ ] Bug reporting tool

### Should Have
- [ ] User interview scheduling (recruit 10 beta users)
- [ ] Beta tester badge/recognition
- [ ] "Recently added" prompts section
- [ ] Keyboard shortcuts (power user feature)

### Success Metrics
- **Retention >30% after 30 days** (per business plan)
- Activation rate >40% (users who hit activation event)
- 10 user interviews completed
- <5 critical bugs reported

### Out of Scope
- Public signup (invite-only beta)
- Mobile apps
- Payment processing

### Deliverable
Beta product with 50-100 active users + retention data + feedback log

---

## Phase 8: Advanced Search & Filters (Week 15-16)

**Goal:** Make prompt discovery faster for power users

### Must Have
- [ ] Filter by category, skill level, AI model
- [ ] Sort by popularity, recency, rating
- [ ] Filter state persistence (URL params)
- [ ] "Clear all filters" button
- [ ] Filter UI (checkboxes, dropdowns)

### Should Have
- [ ] Saved searches (requires collections)
- [ ] Tag-based filtering
- [ ] Multi-select filters
- [ ] Faceted search (show counts per filter)

### Success Metrics
- Users find target prompt in <30s (measured via analytics)
- Filter performance <200ms
- 40%+ of users use filters (engagement metric)

### Out of Scope
- AI semantic search
- Custom filter creation
- Boolean search operators

### Deliverable
Full-featured search and filter system

---

## Phase 9: Prompt Chains (Multi-Step Workflows) (Week 17-19)

**Goal:** Enable sequential prompts with context passing

### Must Have
- [ ] Chain builder UI (list view for MVP)
- [ ] Add/remove/reorder steps
- [ ] Save chains to collections
- [ ] Run chain (manual copy flow, step-by-step)
- [ ] Chain detail view
- [ ] Pre-built chains: Blog Pipeline, Product Launch, Code Review

### Should Have
- [ ] Chain templates library
- [ ] Fork/remix chains
- [ ] Chain sharing (public links)
- [ ] Chain analytics (completion rate)

### Success Metrics
- 3 pre-built chains tested and validated
- 20%+ of users create at least 1 chain
- Chain completion rate >60%

### Out of Scope
- Visual node editor (too complex for MVP)
- Automated API execution
- Conditional branching

### Deliverable
Functional chain system with 3 pre-built workflows

---

## Phase 10: Public Launch Prep (Week 20-21) — **MONTH 3 MILESTONE**

**Goal:** Prepare for Product Hunt and public launch

### Must Have
- [ ] Remove invite-only gate (public signup enabled)
- [ ] Freemium paywall implementation (25 saved prompts limit)
- [ ] Stripe integration (Pro tier: $9.99/mo)
- [ ] Subscription management UI
- [ ] Security audit (RLS, auth, XSS, CSRF)
- [ ] Performance audit (Core Web Vitals)
- [ ] Legal pages (Privacy Policy, Terms of Service)
- [ ] Email onboarding sequence (Loops or similar)

### Should Have
- [ ] Referral system (invite friends, both get 1 month free)
- [ ] Product Hunt assets (thumbnail, screenshots, demo video)
- [ ] Press kit
- [ ] Social media accounts setup

### Success Metrics
- All security tests pass
- Lighthouse score >90
- Payment flow tested (test transactions)
- Legal review complete

### Out of Scope
- Marketplace
- Mobile apps
- Enterprise features

### Deliverable
Production-ready SaaS with payment processing

---

## Phase 11: Product Hunt Launch (Week 22) — **PUBLIC LAUNCH**

**Goal:** Launch on Product Hunt, target 500 users week 1

### Must Have
- [ ] Product Hunt submission (Tuesday/Wednesday)
- [ ] Launch announcement (Twitter/X thread)
- [ ] Reddit posts (r/SideProject, r/ChatGPT, r/Entrepreneur, r/ADHD)
- [ ] Hacker News "Show HN" post
- [ ] IndieHackers detailed post
- [ ] Monitor support channels (respond <2h during launch day)
- [ ] Scale monitoring (Supabase usage, API limits)

### Should Have
- [ ] YouTube partner reviews (3-5 creators)
- [ ] Launch discount (25% off Pro for early adopters)
- [ ] Discord or Slack community launch
- [ ] Live demo/AMA during launch day

### Success Metrics
- **500 users in week 1** (per business plan)
- Product Hunt top 5 in category
- <1 hour downtime
- Conversion rate: 3-5% (free → paid)

### Out of Scope
- Paid advertising
- PR outreach
- International launch

### Deliverable
500+ users, traction validation, initial revenue

---

## Phase 12: Prompt Coach (AI Feature) (Week 23-25)

**Goal:** AI-powered prompt analysis and improvement suggestions

### Must Have
- [ ] Prompt analysis API (OpenAI/Anthropic)
- [ ] Prompt scoring (0-100) based on structure, specificity, clarity
- [ ] Inline suggestions (like Grammarly)
- [ ] "Improve this prompt" one-click apply
- [ ] Token budget enforcement (per Shadow Council)
- [ ] Rate limiting (Pro: unlimited, Free: 5/day)

### Should Have
- [ ] Model-specific optimization (GPT vs Claude)
- [ ] Before/after comparison view
- [ ] Improvement history
- [ ] Export improvement suggestions

### Success Metrics
- Prompt score correlation with output quality: >70%
- Suggestion acceptance rate: >50%
- Pro conversion driver: 15%+ cite Coach as reason

### Out of Scope
- Automated prompt generation (Phase 13)
- Cross-model testing (Phase 14)
- Batch analysis

### Deliverable
Working AI Prompt Coach feature for Pro users

---

## Phase 13: Smart Prompt Generator (Week 26-28)

**Goal:** Natural language → structured prompt

### Must Have
- [ ] Intent parser (user describes what they want)
- [ ] Prompt template generator
- [ ] Variable extraction
- [ ] Multiple variant generation (beginner/intermediate/advanced)
- [ ] DNA annotations on generated prompts
- [ ] Save generated prompts

### Should Have
- [ ] User profile integration (auto-fill context)
- [ ] Industry-specific templates
- [ ] Output format suggestions
- [ ] Token efficiency optimization

### Success Metrics
- Generated prompt quality: 4+ stars average
- 30%+ of users try generator
- Saves 5+ minutes per prompt (user reported)

### Out of Scope
- Conversational refinement
- Multi-language support
- API access

### Deliverable
AI-powered prompt generation feature

---

## Phase 14: Mobile Apps (iOS + Android) (Week 29-34) — **MONTH 6 MILESTONE**

**Goal:** Native-feeling mobile apps via Capacitor

### Must Have
- [ ] Capacitor configuration
- [ ] iOS build (TestFlight)
- [ ] Android build (Google Play internal testing)
- [ ] Offline access (cached prompts)
- [ ] Share extension ("Improve with Prompt Toolkit")
- [ ] Widget (Prompt of the Day)
- [ ] App Store assets (screenshots, description)
- [ ] App Store submission

### Should Have
- [ ] Siri Shortcuts / Quick Actions
- [ ] Haptic feedback
- [ ] Biometric auth
- [ ] Dark mode polish

### Success Metrics
- App Store approval on first submission
- 4+ star rating
- <2s app launch time
- Offline mode works 100%

### Out of Scope
- Keyboard extension (too complex)
- Apple Watch app
- Tablet-optimized layouts

### Deliverable
Published iOS and Android apps

---

## Phase 15: Community Features (Week 35-38)

**Goal:** Enable user-submitted prompts (curated)

### Must Have
- [ ] Prompt submission form
- [ ] Moderation queue (admin review)
- [ ] Prompt rating system (1-5 stars)
- [ ] Community tab (browse user prompts)
- [ ] Creator profiles
- [ ] Remix/fork system
- [ ] Reporting mechanism (spam, low-quality)

### Should Have
- [ ] Verified Creator badge (Level 76+ or manual review)
- [ ] AI-assisted moderation (flag duplicates, spam)
- [ ] Usage notes/comments on prompts
- [ ] "This worked for me" quick feedback

### Success Metrics
- 50+ user-submitted prompts (approved)
- <5% spam rate
- Community prompts: 4+ star average
- 20%+ of users submit at least 1 prompt

### Out of Scope
- Revenue sharing (defer to marketplace)
- Prompt NFTs/blockchain
- User-to-user messaging

### Deliverable
Curated community prompt library

---

## Phase 16: Marketplace Foundation (Week 39-42) — **MONTH 12 MILESTONE**

**Goal:** Enable premium prompts and creator revenue sharing

### Must Have
- [ ] Premium prompt flagging
- [ ] Pricing tiers ($3-7 per premium prompt pack)
- [ ] Payment processing (Stripe Connect for creators)
- [ ] Revenue split (70% creator, 30% platform)
- [ ] Payout system (monthly, minimum $25)
- [ ] Creator dashboard (earnings, sales, views)
- [ ] Marketplace storefront

### Should Have
- [ ] Featured creators
- [ ] Bestseller rankings
- [ ] Creator analytics (conversion rate, avg rating)
- [ ] Affiliate links (creators can promote)

### Success Metrics
- 10+ premium creators onboarded
- $500+ marketplace GMV in first month
- Creator satisfaction: >4 stars

### Out of Scope
- Subscriptions to creators
- Donation/tip system
- NFT integration

### Deliverable
Live marketplace with revenue sharing

---

## Milestone Summary

| Month | Phase | Deliverable | Success Metric |
|-------|-------|-------------|----------------|
| 0 | 1-5 | Database, Library, Customizer, Auth, Landing | **200 waitlist signups** |
| 2 | 6-7 | Prompt DNA, Beta launch | **30% retention** |
| 3 | 8-11 | Filters, Chains, Public launch | **500 users, $1K MRR** |
| 6 | 12-14 | AI features, Mobile apps | **2,000 users, $5K MRR** |
| 12 | 15-16 | Community, Marketplace | **5,000 users, $10K MRR** |
| 18 | Growth | Scale, Team hire | **$15K+ MRR, hire contractor** |

---

## Shadow Council Key Recommendations (Integrated)

✅ **Execution Template:** Each phase has scope (must/should/out), success metrics, deliverables
✅ **Retention Metrics:** Defined in Phase 7 (activation event tracking)
✅ **Thin Vertical Slices:** Phases 2-3 ship library + customizer first
✅ **Prompt DNA Progressive:** Phase 6 uses structured metadata, not heavy AI
✅ **Data Model First:** Phase 1 designs versioning/attribution upfront
✅ **Search Performance:** Phase 1 includes PostgreSQL full-text + GIN indexes
✅ **Security:** Phase 7 includes RLS audit, Phase 10 security audit before public launch
✅ **Token Efficiency:** Phase 3 includes token counter/estimator

---

## Next Steps

1. **Create Phase 1 PLAN.md** — Detailed execution plan for database schema
2. **Set up project tracking** — Use beads or GSD for task management
3. **Begin implementation** — Start with Phase 1 (Week 1-2)
4. **Weekly reviews** — Check progress against success metrics
5. **Adjust as needed** — Roadmap is a living document

---

*Roadmap validated by Shadow Council (GPT-5.2: 4.0/5). Built for bootstrapped execution with MVP-first philosophy.*
