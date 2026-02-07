# Prompt Toolkit SaaS — Technical Architecture

> **Status:** Draft v1.0
> **Stack:** Next.js 15 + PostgreSQL (Supabase) + Capacitor + Vercel
> **Platforms:** Web, iOS, Android

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Web App    │  │  iOS App     │  │ Android App  │              │
│  │  (Next.js)   │  │ (Capacitor)  │  │ (Capacitor)  │              │
│  │  Vercel CDN  │  │  App Store   │  │  Play Store  │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           │                                         │
│              Same Next.js codebase (RSC + Client)                   │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API LAYER (Vercel Edge/Serverless)           │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │  Next.js API   │  │  Server        │  │  Middleware     │        │
│  │  Routes        │  │  Actions       │  │  (Auth + RBAC) │        │
│  │  /api/v1/*     │  │  (mutations)   │  │                │        │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘        │
│          │                   │                   │                  │
│          └───────────────────┼───────────────────┘                  │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                    │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │   Supabase       │  │   Supabase       │  │   Vercel Blob   │   │
│  │   PostgreSQL     │  │   Auth           │  │   (file store)  │   │
│  │   (primary DB)   │  │   (JWT sessions) │  │                 │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐                        │
│  │   Supabase       │  │   Stripe         │                        │
│  │   Realtime       │  │   (payments)     │                        │
│  │   (live updates) │  │                  │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Next.js 15 (App Router) | RSC for SEO, Server Actions for mutations, single codebase |
| Database | Supabase (managed PostgreSQL) | Existing PG data migrates directly, plus built-in auth/realtime/storage |
| Auth | Supabase Auth (+ NextAuth adapter if needed) | Native row-level security, JWT tokens work with Capacitor |
| Mobile | Capacitor | Wraps the Next.js app for App Store/Play Store with native APIs |
| Hosting | Vercel | First-class Next.js support, edge functions, preview deploys |
| Payments | Stripe | Industry standard, good mobile support |
| ORM | Drizzle ORM | Type-safe, lightweight, great PostgreSQL support |

---

## 2. Database Schema

### Entity Relationship Diagram

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    users      │     │    categories     │     │      tags        │
│──────────────│     │──────────────────│     │──────────────────│
│ id (PK)      │     │ id (PK)          │     │ id (PK)          │
│ email        │     │ name             │     │ name             │
│ display_name │     │ slug             │     │ slug             │
│ avatar_url   │     │ description      │     │ color            │
│ role         │     │ icon             │     │ created_at       │
│ tier         │     │ parent_id (FK)   │     └────────┬─────────┘
│ stripe_id    │     │ sort_order       │              │
│ created_at   │     │ created_at       │              │
└──────┬───────┘     └────────┬─────────┘     ┌────────┴─────────┐
       │                      │               │  prompt_tags     │
       │              ┌───────┴────────┐      │──────────────────│
       │              │                │      │ prompt_id (FK)   │
       ▼              ▼                │      │ tag_id (FK)      │
┌──────────────────────────────┐      │      └────────┬─────────┘
│          prompts             │      │               │
│──────────────────────────────│◄─────┘───────────────┘
│ id (PK)                     │
│ title                       │
│ slug                        │
│ description                 │
│ content (the prompt text)   │
│ system_prompt               │
│ example_output              │
│ use_case                    │
│ difficulty                  │
│ ai_model_tags               │
│ category_id (FK)            │
│ author_id (FK → users)      │
│ is_public                   │
│ is_featured                 │
│ version                     │
│ fork_of (FK → prompts)      │
│ created_at                  │
│ updated_at                  │
└──────────┬───────────────────┘
           │
     ┌─────┼──────────────┐
     │     │              │
     ▼     ▼              ▼
┌─────────┐ ┌──────────┐ ┌──────────────┐
│favorites│ │ ratings  │ │ usage_logs   │
│─────────│ │──────────│ │──────────────│
│user_id  │ │user_id   │ │ id (PK)      │
│prompt_id│ │prompt_id │ │ user_id (FK) │
│folder   │ │score 1-5 │ │ prompt_id(FK)│
│note     │ │review    │ │ action       │
│created  │ │created   │ │ metadata     │
└─────────┘ └──────────┘ │ created_at   │
                         └──────────────┘
```

### Full SQL Schema

See [`schema.sql`](./app/src/db/schema.sql) for the complete migration-ready schema.

### Migration Strategy (Home Lab → Supabase)

1. **Export** existing PG data with `pg_dump --data-only --format=custom`
2. **Create** Supabase project, run schema migration
3. **Import** with `pg_restore` into Supabase's connection string
4. **Map** existing rows to new schema (write a migration script for any column renames)
5. **Enable** Row Level Security policies
6. **Verify** data integrity with count + spot checks

---

## 3. API Routes

### REST API (Next.js Route Handlers)

```
/api/v1/
├── auth/
│   ├── POST   /signup              — Create account
│   ├── POST   /login               — Email/password login
│   ├── POST   /login/oauth         — Google/GitHub/Apple OAuth
│   ├── POST   /logout              — End session
│   └── GET    /me                  — Current user profile
│
├── prompts/
│   ├── GET    /                    — List/search prompts (paginated, filterable)
│   ├── POST   /                    — Create prompt (auth required)
│   ├── GET    /:slug               — Get prompt detail
│   ├── PUT    /:slug               — Update prompt (owner/admin)
│   ├── DELETE /:slug               — Soft-delete prompt (owner/admin)
│   ├── POST   /:slug/fork          — Fork a prompt
│   ├── POST   /:slug/rate          — Rate a prompt (1-5)
│   ├── POST   /:slug/favorite      — Toggle favorite
│   └── POST   /:slug/copy          — Log a "copy to clipboard" action
│
├── categories/
│   ├── GET    /                    — List all categories (tree)
│   └── GET    /:slug               — Category detail + prompts
│
├── users/
│   ├── GET    /:id                 — Public profile
│   ├── PUT    /me                  — Update own profile
│   ├── GET    /me/favorites        — User's favorited prompts
│   ├── GET    /me/prompts          — User's created prompts
│   └── GET    /me/usage            — Usage analytics
│
├── search/
│   └── GET    /?q=...&category=... — Full-text search with filters
│
├── admin/
│   ├── GET    /stats               — Dashboard stats
│   ├── GET    /prompts/pending     — Moderation queue
│   └── PUT    /prompts/:id/review  — Approve/reject
│
└── billing/
    ├── POST   /checkout            — Create Stripe checkout session
    ├── POST   /portal              — Stripe customer portal
    └── POST   /webhook             — Stripe webhook handler
```

### Server Actions (for mutations via RSC)

```typescript
// Direct form submissions — no API roundtrip
'use server'
createPrompt(formData: FormData)
updatePrompt(id: string, formData: FormData)
toggleFavorite(promptId: string)
ratePrompt(promptId: string, score: number)
updateProfile(formData: FormData)
```

---

## 4. Authentication Strategy

### Primary: Supabase Auth

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client   │────▶│ Supabase Auth│────▶│  PostgreSQL   │
│ (Browser/ │     │  (JWT)       │     │  (RLS enforced)│
│  Mobile)  │◀────│              │◀────│               │
└──────────┘     └──────────────┘     └──────────────┘
```

**Why Supabase Auth over NextAuth/Clerk:**
- **Row Level Security** — Auth tokens flow directly to DB; RLS policies enforce access without middleware
- **No vendor lock-in** on auth layer (it's just PostgreSQL + GoTrue under the hood)
- **Capacitor-friendly** — Token-based auth works natively on mobile
- **Built-in OAuth** — Google, GitHub, Apple (required for iOS) providers
- **Free tier** — 50k MAU included

### Auth Flow

1. **Web:** Supabase `signInWithOAuth()` → redirect → JWT stored in httpOnly cookie
2. **Mobile (Capacitor):** Deep link OAuth → token stored in Capacitor Preferences (encrypted)
3. **API Routes:** Middleware validates JWT, attaches user to request context
4. **RLS:** Every DB query automatically scoped by `auth.uid()`

### User Roles & Tiers

| Role | Permissions |
|------|-------------|
| `anonymous` | Browse public prompts, search, view details |
| `free` | Everything above + save favorites, rate, 10 copies/day |
| `pro` | Everything above + unlimited copies, create prompts, usage analytics |
| `admin` | Everything above + moderation, featured management, user management |

---

## 5. Deployment Pipeline

```
┌──────────┐    ┌───────────┐    ┌──────────────┐    ┌───────────┐
│   Local   │───▶│  GitHub    │───▶│  Vercel CI   │───▶│Production │
│   Dev     │    │  (main)    │    │  (auto-build)│    │  (Vercel) │
└──────────┘    └───────────┘    └──────────────┘    └───────────┘
     │               │                   │
     │          ┌────┴────┐         ┌────┴────┐
     │          │ PR → dev│         │ Preview │
     │          │ branch  │         │ Deploy  │
     │          └─────────┘         └─────────┘
     │
     ▼
┌──────────────────────────────────────────┐
│          Capacitor Build Pipeline         │
│                                          │
│  npm run build                           │
│  npx cap sync                            │
│  ├── iOS: Xcode → TestFlight → App Store │
│  └── Android: Android Studio → Play Store│
└──────────────────────────────────────────┘
```

### Environment Strategy

| Environment | URL | Database | Purpose |
|-------------|-----|----------|---------|
| Local | localhost:3000 | Local PG or Supabase dev branch | Development |
| Preview | *.vercel.app | Supabase staging project | PR reviews |
| Production | prompttoolkit.com | Supabase production | Live |

### CI/CD Steps (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]
  pull_request:

jobs:
  quality:
    - npm ci
    - npm run lint
    - npm run type-check
    - npm run test

  deploy:
    needs: quality
    - Vercel auto-deploys (connected via GitHub integration)

  mobile:
    needs: quality
    on: release/tag only
    - npm run build && npx cap sync
    - Fastlane for iOS/Android store submission
```

### Required Environment Variables

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...       # Server-side only

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# App
NEXT_PUBLIC_APP_URL=https://prompttoolkit.com
```

---

## 6. Capacitor Mobile Strategy

### How It Works

Capacitor wraps the production web build in a native WebView. The same Next.js output runs on iOS/Android with access to native APIs.

```
Next.js build (static export)
        │
        ▼
  npx cap sync
        │
   ┌────┴────┐
   ▼         ▼
  iOS      Android
(Swift)   (Kotlin)
WebView   WebView
```

### Key Considerations

1. **Static Export** — Mobile builds use `output: 'export'` in next.config (SSR routes won't work natively)
2. **API Calls** — Mobile app calls the same Vercel-hosted API (not local server)
3. **Auth** — OAuth uses deep links (capacitor://callback) instead of redirects
4. **Push Notifications** — @capacitor/push-notifications for engagement
5. **App Store Requirements:**
   - Apple Sign In required (if offering any OAuth)
   - Privacy nutrition labels
   - Review guidelines compliance

### Phase Strategy

| Phase | Target | Timeline |
|-------|--------|----------|
| 1 | Web app (MVP) | Weeks 1-4 |
| 2 | PWA (installable) | Week 5 |
| 3 | iOS + Android (Capacitor) | Weeks 6-8 |
| 4 | Native features (push, haptics) | Weeks 9-10 |

---

## 7. Performance & Scaling

### Caching Strategy

```
Browser ←→ Vercel Edge Cache ←→ ISR (revalidate: 60) ←→ Supabase
```

- **Static pages** (landing, about): Build-time generated
- **Prompt listings**: ISR with 60s revalidation
- **Prompt detail**: ISR with on-demand revalidation on edit
- **User-specific data**: Client-side fetch with SWR/React Query
- **Search**: Edge function + Supabase full-text search (pg_trgm + tsvector)

### Estimated Costs (at 10k MAU)

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| Vercel | Pro | $20 |
| Supabase | Pro | $25 |
| Stripe | Per-transaction | ~2.9% + $0.30 |
| Domain | Annual | ~$12/yr |
| Apple Developer | Annual | $99/yr |
| Google Play | One-time | $25 |
| **Total** | | **~$50/mo + transaction fees** |

---

## 8. Security

- **RLS everywhere** — No query touches data without auth context
- **Input validation** — Zod schemas on all API inputs
- **Rate limiting** — Vercel WAF + custom middleware (100 req/min for free tier)
- **CSRF** — Built into Server Actions
- **XSS** — React's default escaping + CSP headers
- **SQL Injection** — Parameterized queries via Drizzle ORM (never raw string interpolation)
- **Secrets** — All in Vercel env vars, never in code

---

## 9. File Structure

```
app/
├── src/
│   ├── app/                     # Next.js App Router
│   │   ├── (marketing)/         # Landing, pricing, about
│   │   ├── (app)/               # Authenticated app shell
│   │   │   ├── dashboard/
│   │   │   ├── browse/
│   │   │   ├── prompt/[slug]/
│   │   │   ├── profile/
│   │   │   └── layout.tsx       # App shell with sidebar
│   │   ├── api/v1/              # API route handlers
│   │   ├── auth/                # Auth pages (login, signup)
│   │   ├── layout.tsx           # Root layout
│   │   └── page.tsx             # Landing page
│   ├── components/
│   │   ├── ui/                  # Shadcn/ui components
│   │   ├── prompts/             # Prompt-specific components
│   │   └── layout/              # Shell, sidebar, nav
│   ├── db/
│   │   ├── schema.sql           # PostgreSQL schema
│   │   ├── schema.ts            # Drizzle ORM schema
│   │   └── migrations/          # SQL migrations
│   ├── lib/
│   │   ├── supabase/            # Supabase client (server + browser)
│   │   ├── stripe/              # Stripe helpers
│   │   └── utils.ts             # Shared utilities
│   └── types/                   # TypeScript types
├── capacitor.config.ts
├── ios/                         # Capacitor iOS project
├── android/                     # Capacitor Android project
└── package.json
```
