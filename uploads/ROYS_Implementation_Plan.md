# ROYS (Roystonea Documents) — Implementation Plan
## All Phases: From Foundation to Launch
### February 22, 2026 — CONFIDENTIAL

---

## Infrastructure Decision: Digital Ocean

### Recommended Setup: Single 4GB Droplet + Docker Compose

| Component | Spec | Cost |
|---|---|---|
| **Droplet** | 4GB RAM / 2 vCPU / 80GB SSD (Premium) | $24/mo |
| **Automated Backups** | Daily snapshots | $4.80/mo |
| **Cloud Firewall** | Stateful, default-deny | Free |
| **SSL** | Let's Encrypt (auto-renew) | Free |
| **DNS** | Cloudflare (DDoS + CDN) | Free tier |
| **Domain** | roystoneadocs.com | ~$12/yr |
| **Total** | | **~$30/mo** |

This handles 50-100 concurrent users comfortably. When ROYS hits traction (month 3-6), upgrade path is: split to Droplet + Managed PostgreSQL ($32/mo), then add load balancer + multiple droplets when needed.

### Growth Path

```
Launch:     Single 4GB Droplet ($29/mo) — 50-100 concurrent users
Month 3-6:  Droplet + Managed DB ($32/mo) — independent scaling, PITR backups
Month 6-12: Load Balancer + 2x Droplets + HA DB ($81/mo) — 300+ concurrent
```

---

## Phase 0: Foundation (Week 1-2)
### Goal: Database schema + content import + project scaffolding

Everything starts here. The content library in PostgreSQL is the foundation that every other phase builds on. We can validate the data model before writing a single line of frontend code.

### Step 0.1: Project Setup

```
Tasks:
□ Create Git repository for ROYS project
□ Set up project directory structure (see Architecture doc Section 11)
□ Initialize Python backend with FastAPI
□ Initialize React frontend with Vite + Tailwind v4
□ Create docker-compose.yml for local development
□ Create .env.example with all required environment variables
□ Set up PostgreSQL 17 database locally (Docker container)
□ Install core Python dependencies:
  - fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic
  - python-docx, docxtpl, python-jose[cryptography], passlib[bcrypt]
  - stripe, pydantic, aiofiles, python-multipart
□ Install core frontend dependencies:
  - react, react-dom, react-router-dom
  - @tanstack/react-query, axios
  - tailwindcss, @headlessui/react
```

**Acceptance Criteria:** `docker-compose up` starts PostgreSQL + FastAPI + Vite dev server. All three services healthy.

### Step 0.2: Database Schema

```
Tasks:
□ Create Alembic migration infrastructure
□ Write initial migration with full schema:
  - standards table
  - requirements table (610+ rows)
  - sops table (81 rows)
  - content_blocks table (567+ rows)
  - content_block_versions table
  - requirement_sop_mappings table (539+ rows)
  - sop_cross_references table
  - template_structures table
  - standard_combinations table
  - users table
  - user_sop_access table
  - subscriptions table
  - team_members table
  - consulting_requests table
  - usage_log table
□ Create all indexes from Architecture doc Section 4
□ Run migration, verify schema is clean
□ Write seed data for template_structures (2-3 document formats)
□ Write seed data for standard_combinations (common combos)
```

**Acceptance Criteria:** `alembic upgrade head` creates all tables. Schema matches Architecture doc exactly.

### Step 0.3: Content Import from Excel

This is the critical step — moving Evelyn's IP from Excel into PostgreSQL.

```
Tasks:
□ Get Evelyn's Excel files and map column names to database fields
□ Write import_content.py script with these functions:
  - import_standards() — Create records for all 5 standards/regulations
  - import_requirements() — Import 610+ requirements with clause numbers
  - import_sops() — Import 81 SOPs with metadata and categories
  - import_content_blocks() — Import 567+ content blocks with:
    * SOP association
    * Section type (purpose/scope/definitions/responsibilities/procedure/records/references)
    * Standard combination key
    * Content tier (core/enhanced)
  - import_mappings() — Import 539+ requirement-to-SOP mappings
  - import_cross_references() — Import SOP cross-references (if data exists)
□ Run import script
□ Write verification queries:
  - Count check: standards=5, requirements=610+, sops=81, blocks=567+, mappings=539+
  - Integrity check: all foreign keys valid
  - Coverage check: every SOP has at least 1 content block per section type
  - Combo check: standard_combo values match standard_combinations table
□ Generate coverage report: for each standard, how many requirements → SOPs
□ Create a backup of the fully imported database (pg_dump)
```

**Acceptance Criteria:** All content imported. Verification queries pass. Counts match Evelyn's Excel totals. Coverage report reviewed by Evelyn.

### Step 0.4: SQLAlchemy Models

```
Tasks:
□ Create models/content.py — Standard, Requirement, SOP, ContentBlock,
  ContentBlockVersion, RequirementSOPMapping, SOPCrossReference,
  TemplateStructure, StandardCombination
□ Create models/users.py — User, Subscription, TeamMember
□ Create models/commerce.py — UserSOPAccess, ConsultingRequest, UsageLog
□ Create database.py — async engine, session factory, dependency injection
□ Test: query each table via SQLAlchemy, verify data matches
```

**Acceptance Criteria:** All models defined. Can query content library via SQLAlchemy async sessions.

### Phase 0 Definition of Done
- [ ] Project runs locally via Docker Compose
- [ ] PostgreSQL schema fully created via Alembic
- [ ] All of Evelyn's content imported and verified
- [ ] SQLAlchemy models working for all tables
- [ ] Coverage report generated and reviewed
- [ ] Database backed up

---

## Phase 1: Assembly Engine (Week 3-4)
### Goal: Core logic that turns user selections into assembled SOP data

The assembly engine is the heart of ROYS. No frontend needed yet — this is pure backend logic that we can test from the command line.

### Step 1.1: Assembly Logic

```
Tasks:
□ Create services/assembly.py with:
  - assemble_sop(sop_id, standard_ids, content_tier, template_structure_id)
  - get_content_blocks() with fallback strategy:
    1. Exact standard combo match at requested tier
    2. Exact combo match at core tier (if enhanced requested)
    3. Individual standard blocks merged
    4. Graceful error if no content available
  - get_traceability_mappings() — get all requirement→SOP mappings
    * Core tier: reference list of applicable clauses
    * Enhanced tier: full matrix with SOP section mapping
  - get_cross_references() — Enhanced tier only
□ Create AssembledSOP dataclass/Pydantic model to hold the result
□ Handle standard_combo resolution:
  - Sort standard codes alphabetically to create deterministic combo key
  - e.g., [21_CFR_820, ISO_13485_2016] → "21_CFR_820+ISO_13485_2016"
```

**Acceptance Criteria:** Given a SOP ID + standard IDs + tier, the engine returns a complete AssembledSOP with all content blocks, traceability data, and cross-references. Same inputs always return the same output.

### Step 1.2: Assembly Engine Tests

```
Tasks:
□ Write test_assembly.py:
  - test_single_standard_core: ISO 13485 only, core tier
  - test_single_standard_enhanced: ISO 13485 only, enhanced tier
  - test_multi_standard: ISO 13485 + 21 CFR 820 combined
  - test_fallback_to_core: Request enhanced where only core exists
  - test_fallback_to_individual: Request combo where only individual blocks exist
  - test_missing_content: Request combo with no content, verify graceful error
  - test_deterministic: Same inputs produce identical output every time
  - test_all_sections_present: Verify all sections from template structure are populated
  - test_traceability_core_vs_enhanced: Core gets reference list, enhanced gets full matrix
□ Verify all 81 SOPs can be assembled for at least one standard combo
```

**Acceptance Criteria:** All tests pass. Every SOP in the database can be successfully assembled.

### Step 1.3: CLI Generation Tool

```
Tasks:
□ Create scripts/generate_cli.py — command-line SOP generator for testing:
  - Input: SOP number, standard codes, tier, output path
  - Output: prints assembled content to console or file
  - Example: python generate_cli.py --sop SOP-001 --standards ISO_13485_2016 21_CFR_820 --tier enhanced
□ Use this to validate content quality with Evelyn before building the frontend
□ Generate 5-10 sample SOPs for Evelyn's review
```

**Acceptance Criteria:** Evelyn reviews CLI-generated output and confirms content is correctly assembled. This is the first real validation checkpoint.

### Phase 1 Definition of Done
- [ ] Assembly engine returns complete SOP data for any valid selection
- [ ] Fallback strategy works for missing combinations
- [ ] All tests pass
- [ ] Evelyn has reviewed 5-10 generated SOPs and approved content assembly
- [ ] Core vs Enhanced tier differences verified

---

## Phase 2: Document Generation (Week 5-6)
### Goal: Turn assembled SOP data into professional Word documents

This is where ROYS becomes tangible. The generated Word document IS the product.

### Step 2.1: Word Template Design

```
Tasks:
□ Design 2-3 professional .docx templates in Microsoft Word:
  - standard_7section.docx — Full 7-section SOP (default)
  - condensed_5section.docx — Shorter format (no definitions/references)
  - (optional) fda_style.docx — FDA-preferred formatting
□ Each template includes:
  - Professional header: [COMPANY NAME] | [DOCUMENT NUMBER] | Rev [REV]
  - Professional footer: Page X of Y | [EFFECTIVE DATE] | CONFIDENTIAL
  - Title page with SOP number, title, standard coverage
  - Section headings with consistent hierarchy
  - Table formatting for traceability matrix
  - Placeholder fields clearly marked: [YOUR COMPANY NAME], [EFFECTIVE DATE], etc.
  - Jinja2 tags for docxtpl rendering:
    * {{ sop_number }}, {{ sop_title }}, {{ standards_list }}
    * {{ purpose_content }}, {{ scope_content }}, etc.
    * {% for mapping in traceability_mappings %} ... {% endfor %}
    * {% if content_tier == 'enhanced' %} ... {% endif %}
□ Evelyn reviews and approves template design before proceeding
□ Register templates in template_structures database table
```

**Acceptance Criteria:** Templates open cleanly in Word, look professional, and have all Jinja2 tags in the correct locations. Evelyn approves the design.

### Step 2.2: Document Generator Service

```
Tasks:
□ Create services/docgen.py:
  - ThreadPoolExecutor with 8 workers for concurrent rendering
  - Template caching (load once, render many)
  - _render_document(assembled_sop, output_path) → generates .docx
  - generate_sop_document(assembled_sop) → async wrapper
  - Signed URL generation for downloads (time-limited, 1 hour)
□ Handle content rendering:
  - Rich text content blocks → proper Word formatting
  - Numbered/bulleted lists preserved
  - Tables rendered correctly
  - Traceability matrix as appendix (Enhanced) or reference list (Core)
  - Cross-references section (Enhanced only)
  - All customer-customization placeholders clearly marked
□ Temporary file management:
  - Generated docs stored in /tmp/roys_generated/
  - Cleanup job: delete files older than 24 hours
  - Track document_path in user_sop_access table
```

**Acceptance Criteria:** Generated Word docs open perfectly in Microsoft Word and Google Docs. Formatting is professional. Traceability tables are accurate.

### Step 2.3: Output Quality Validation

```
Tasks:
□ Generate one SOP per standard/regulation (5 total) at both tiers (10 docs)
□ Evelyn reviews ALL 10 documents for:
  - Content accuracy (correct regulatory references?)
  - Formatting quality (professional enough for an auditor?)
  - Traceability correctness (mappings accurate?)
  - Placeholder clarity (customization points obvious?)
  - Core vs Enhanced differences clear?
□ Send 3-5 sample SOPs to beta testers for feedback:
  - "Would you bring this to an FDA audit?"
  - "Is the formatting professional enough?"
  - "Are the customization points clear?"
□ Iterate on template design based on feedback
□ Generate final samples for ALL 81 SOPs and spot-check 10-15 randomly
```

**Acceptance Criteria:** Evelyn and at least 2 beta testers confirm document quality meets "audit-aligned" standard. No formatting issues. Traceability is accurate.

### Phase 2 Definition of Done
- [ ] Professional Word templates designed and approved
- [ ] Document generator produces clean .docx files
- [ ] 8 concurrent document generations work without errors
- [ ] Evelyn approved output quality
- [ ] Beta tester feedback incorporated
- [ ] All 81 SOPs can be generated without errors

---

## Phase 3: Frontend Core (Week 7-9)
### Goal: Landing page, catalog browser, generation wizard, account system

### Step 3.1: Auth System

```
Tasks:
□ Create routers/auth.py:
  - POST /api/auth/register — email, password, name, company
  - POST /api/auth/login — returns JWT (access 15min + refresh 7 days)
  - POST /api/auth/refresh — refresh access token
  - GET /api/auth/me — current user profile
□ JWT middleware for protected routes
□ Password hashing with bcrypt (cost factor 12)
□ Frontend auth hooks: useAuth(), protected route wrapper
□ Login/register pages (clean, minimal, trustworthy design)
```

### Step 3.2: Public Catalog (No Auth Required)

```
Tasks:
□ Create routers/catalog.py:
  - GET /api/standards — list all standards/regulations with type labels
  - GET /api/sops — list SOPs, filterable by standard
  - GET /api/sops/:id — SOP detail with applicable standards, sections, preview
  - GET /api/sops/:id/preview — which requirements this SOP covers
  - GET /api/template-structures — available document structures
□ Frontend pages:
  - Landing page:
    * Value proposition headline (NOT "audit-ready" — use "the hardest 80% done")
    * Standards coverage display (ISO 13485, 21 CFR 820, etc.)
    * Sample traceability table preview
    * Pricing tiers
    * Testimonials section (populated from beta testers)
    * CTA: "Get Started" → register/catalog
  - Catalog page:
    * Standard/regulation selector (checkboxes with type labels)
    * SOP grid/list filtered by selection
    * Each SOP card: title, category, applicable standards, complexity, price
    * Click → SOP detail with requirement coverage preview
```

### Step 3.3: SOP Generation Wizard

```
Tasks:
□ Create routers/generate.py:
  - POST /api/generate — main generation endpoint
    * Validates purchase/subscription entitlement
    * Calls assembly engine
    * Calls document generator
    * Records usage
    * Returns download URL
  - GET /api/generate/:access_id/download — serve the file
□ Frontend generation wizard (multi-step flow):
  Step 1: "Which standards/regulations apply?"
    → Checkboxes for each standard/regulation
    → Type labels: "Standard (voluntary)" vs "Regulation (legally binding)"
    → Count indicator: "X SOPs available for this selection"

  Step 2: "Which procedure do you need?"
    → Filtered SOP catalog based on selected standards
    → Categorized by function (Quality, Production, Design, etc.)
    → SOP card shows: title, standards, complexity, price by tier

  Step 3: "Choose your content tier"
    → Core vs Enhanced comparison (side-by-side)
    → Clear differences: traceability depth, risk content, cross-references
    → Price displayed for each tier

  Step 4: "Choose document structure"
    → Template structure options (full 7-section, condensed, etc.)
    → Preview of which sections will be included

  Step 5: "Review & Purchase"
    → Summary of all selections
    → Price breakdown
    → "Purchase" → Stripe Checkout
    → OR "Add to Bundle" if buying multiple
    → OR "Included in Subscription" if subscriber

  Step 6: "Your SOP is Ready"
    → Download button (immediate)
    → "Request Expert Review" button (consulting add-on)
    → "What to do next" guidance
    → Related SOPs suggestion
```

### Step 3.4: Account Page

```
Tasks:
□ Create routers/account.py:
  - GET /api/account/library — user's generated SOPs + download history
  - GET /api/account/consulting — consulting request statuses
□ Frontend account page:
  - Library: list of generated SOPs with re-download links
  - Consulting: status of any expert review requests
  - Subscription info (if subscriber): plan, usage this period, renewal date
  - Billing portal link (Stripe)
```

### Step 3.5: Responsive Design & Trust Signals

```
Tasks:
□ Responsive layout for mobile/tablet (quality managers browse on phones)
□ Trust signals throughout:
  - "Expert-curated by regulatory professionals" badge
  - "Not AI-generated" indicator
  - "610 requirements mapped across 5 standards" stat
  - Evelyn's credentials and experience
  - Beta tester testimonials
□ Never use the word "template" — SOPs, procedures, documentation
□ Clean, professional design (think: Daiki's UI quality, OpenRegulatory's transparency)
□ Loading states for generation (micro-loading with status: "Assembling your SOP...")
```

### Phase 3 Definition of Done
- [ ] User can register, login, browse catalog without auth
- [ ] Full generation wizard works end-to-end (select → generate → download)
- [ ] Landing page communicates value proposition clearly
- [ ] Responsive on mobile
- [ ] Trust signals visible throughout
- [ ] Account page shows library and consulting requests

---

## Phase 4: Payments (Week 10-11)
### Goal: Stripe integration for all purchase types

### Step 4.1: Stripe Product Setup

```
Tasks:
□ Create Stripe account for Roystonea Compliance LLC
□ Create Stripe products and prices:
  One-time purchases:
  - single_core: $49
  - single_enhanced: $75
  - bundle_core: $159 (5 SOPs)
  - bundle_enhanced: $239 (5 SOPs)

  Subscriptions:
  - individual_core_monthly: $79/mo
  - individual_enhanced_monthly: $119/mo
  - team_core_monthly: $199/mo
  - team_enhanced_monthly: $299/mo
  - individual_core_annual: $790/yr
  - individual_enhanced_annual: $1,190/yr
  - team_core_annual: $1,990/yr
  - team_enhanced_annual: $2,990/yr

  Overages:
  - overage_core: $34/SOP
  - overage_enhanced: $53/SOP

  Consulting:
  - consulting_core_onetime: $129
  - consulting_enhanced_onetime: $199
  - consulting_core_subscriber: $99
  - consulting_enhanced_subscriber: $159

□ Create Stripe Billing Meter: sops_generated
□ Configure Stripe Tax (SaaS tax code, exclusive pricing)
□ Set up webhook endpoint URL
```

### Step 4.2: Checkout Flows

```
Tasks:
□ Create routers/billing.py:
  - POST /api/checkout/single — Stripe Checkout for single SOP
  - POST /api/checkout/bundle — Stripe Checkout for 5-SOP bundle
  - POST /api/checkout/subscription — Stripe Checkout for subscription
  - GET /api/billing/portal — Stripe Billing Portal URL
  - GET /api/billing/usage — current period usage stats
□ Create services/stripe_service.py:
  - create_checkout_session() for each purchase type
  - create_portal_session() for subscription management
  - record_meter_event() for usage tracking
  - check_entitlement() — can this user generate this SOP?
□ Frontend integration:
  - Stripe Checkout redirect on purchase
  - Success/cancel return pages
  - Subscription management via Billing Portal
  - Usage indicator for subscribers (X of 5 SOPs used this month)
```

### Step 4.3: Webhook Handler

```
Tasks:
□ POST /api/webhooks/stripe — handle all Stripe events:
  - checkout.session.completed → provision access, update DB
  - customer.subscription.created → activate subscription
  - customer.subscription.updated → handle plan changes
  - customer.subscription.deleted → deactivate subscription
  - invoice.payment_succeeded → log successful payment
  - invoice.payment_failed → flag account, notify user
  - invoice.upcoming → calculate overages, add line items
□ Webhook signature verification on every event
□ Idempotent handlers (check if already processed)
□ Test with Stripe CLI (stripe listen --forward-to)
```

### Step 4.4: Entitlement Logic

```
Tasks:
□ Build entitlement check into generation endpoint:
  - Single purchase: check user_sop_access for this SOP + tier
  - Bundle: check remaining bundle credits
  - Subscription: check active subscription + usage limit
  - Overage: if subscriber over limit, charge overage price
□ Handle edge cases:
  - User upgrades from core to enhanced (pay difference)
  - User re-downloads previously purchased SOP (free)
  - Subscription expires mid-month (access to already-generated docs persists)
  - Team member generates SOP (counts against team pool)
```

### Step 4.5: Consulting Add-On

```
Tasks:
□ Create routers/consulting.py:
  - POST /api/consulting/request — create consulting request + Stripe payment
  - GET /api/consulting/:id — check status
□ Consulting request flow:
  1. User generates SOP
  2. Clicks "Request Expert Review" → sees price based on tier + customer type
  3. Stripe Checkout for consulting fee
  4. On payment success: create consulting_request record, notify Evelyn
  5. Evelyn reviews, customizes, uploads revised document
  6. User notified, can download revised version
□ Notification to Evelyn: email on new consulting request
□ Admin interface for managing consulting queue (Phase 5)
```

### Phase 4 Definition of Done
- [ ] Single SOP purchase works end-to-end (select → pay → generate → download)
- [ ] Bundle purchase works (5 SOPs, customer picks any 5)
- [ ] Monthly and annual subscriptions work
- [ ] Usage tracking accurate (Stripe Meters + app-side)
- [ ] Overage billing functional
- [ ] Consulting add-on payment and request flow complete
- [ ] Webhook handler processes all events correctly
- [ ] Tested with Stripe test mode end-to-end

---

## Phase 5: Admin Panel (Week 12-13)
### Goal: Content management for Evelyn + consulting queue

### Step 5.1: Admin Authentication

```
Tasks:
□ Admin middleware: check is_admin claim in JWT
□ Admin routes require admin auth
□ Evelyn's account flagged as admin in database
```

### Step 5.2: Content Management

```
Tasks:
□ Create routers/admin.py:
  Content Block Management:
  - GET /api/admin/content-blocks — list/search/filter all blocks
  - GET /api/admin/content-blocks/:id — single block with version history
  - PUT /api/admin/content-blocks/:id — update block (creates new version)
    * Requires change_reason field
    * Old version marked as superseded
    * New version created with incremented version number
  - GET /api/admin/sops/:id/blocks — all blocks for an SOP (7 sections side-by-side)

  Coverage Reports:
  - GET /api/admin/standards/:id/coverage — for each standard:
    * Total requirements
    * Requirements mapped to SOPs
    * Requirements with content blocks
    * Gap identification
  - GET /api/admin/sops/:id/coverage — which standards/requirements this SOP covers

□ Frontend admin pages:
  - Content Block Editor:
    * Rich text editor (TipTap or similar)
    * Shows: SOP, section type, standard combo, tier
    * Version history sidebar
    * Cannot save without change_reason
    * Status workflow: Draft → In Review → Approved → Superseded
  - SOP Overview:
    * All 7 sections displayed for one SOP
    * Edit any section in-place
    * Standard combo selector to view different versions
  - Coverage Dashboard:
    * Per-standard requirement coverage percentage
    * Visual gap identification
    * Filter by SOP category
```

### Step 5.3: Consulting Queue

```
Tasks:
□ Admin consulting management:
  - GET /api/admin/consulting — list all requests, filterable by status
  - PUT /api/admin/consulting/:id — update status, upload revised document
□ Frontend consulting queue:
  - List of pending/in-progress requests
  - View original generated SOP + customer notes
  - Upload revised document
  - Update status: pending → in_progress → delivered
  - Customer notified on delivery (email)
```

### Step 5.4: Analytics Dashboard

```
Tasks:
□ GET /api/admin/analytics — aggregate data:
  - SOPs generated by type/standard/tier (daily/weekly/monthly)
  - Revenue by purchase type
  - Top 10 most-generated SOPs
  - Customer acquisition (new registrations per week)
  - Subscription conversion rate (single purchasers → subscribers)
  - Consulting request volume
□ Simple dashboard with charts (recharts or similar)
```

### Phase 5 Definition of Done
- [ ] Evelyn can edit any content block with full version history
- [ ] Change reason required for all edits
- [ ] Coverage reports show gaps accurately
- [ ] Consulting queue functional (receive, review, deliver)
- [ ] Analytics dashboard shows key metrics
- [ ] All admin actions logged

---

## Phase 6: Polish, Deploy & Beta (Week 14-16)
### Goal: Production deployment, testing, beta program, launch readiness

### Step 6.1: Digital Ocean Setup

```
Tasks:
□ Create Digital Ocean account (Roystonea Compliance LLC)
□ Create 4GB/2vCPU Premium Droplet (Ubuntu 22.04, nyc3 region)
□ Enable automated backups ($4.80/mo)
□ Configure Cloud Firewall:
  - SSH (22): Evelyn's IP + your IP only
  - HTTP (80): anywhere
  - HTTPS (443): anywhere
  - All other inbound: deny
□ SSH setup:
  - Add SSH keys (disable password auth)
  - Create non-root deploy user
□ Install Docker + Docker Compose on Droplet
□ Point domain DNS to Droplet IP (Cloudflare)
□ Set up Let's Encrypt SSL with Certbot (auto-renewal)
□ Create production docker-compose.yml:
  - nginx (reverse proxy + static frontend)
  - fastapi (4 Uvicorn workers)
  - postgres (with volume mount for persistence)
□ Configure Nginx:
  - HTTPS redirect
  - Proxy /api/ to FastAPI
  - Serve React build at /
  - Gzip compression
  - Security headers (HSTS, X-Frame-Options, CSP)
□ PostgreSQL production config:
  - shared_buffers: 1GB
  - effective_cache_size: 3GB
  - max_connections: 100
  - Daily pg_dump backup to /backups/ (cron 2am)
□ Deploy application
□ Run Alembic migrations on production DB
□ Import content library to production DB
□ Verify all endpoints working
```

### Step 6.2: Production Hardening

```
Tasks:
□ Environment variables secured (.env not in git, Docker secrets)
□ Stripe webhook endpoint configured for production URL
□ Switch Stripe to live mode (after testing)
□ CORS configured for production domain only
□ Rate limiting on auth endpoints (prevent brute force)
□ Rate limiting on generation endpoint (prevent abuse)
□ Error handling: friendly error pages, no stack traces exposed
□ Logging: structured JSON logs, rotate daily
□ Health check endpoint: GET /api/health (used by monitoring)
□ Uptime monitoring: simple cron-based health check with email alert
□ Database backup verified: test restore from backup
□ Load test: simulate 50-100 concurrent SOP generations
```

### Step 6.3: Beta Program

```
Tasks:
□ Recruit beta testers from Evelyn's professional network
□ Create beta accounts (free access for 30 days)
□ Prepare feedback form:
  - SOP content quality (1-5 + comments)
  - Document formatting (1-5 + comments)
  - Traceability usefulness (1-5 + comments)
  - User experience (1-5 + comments)
  - "Would you pay $X for this?" (pricing validation)
  - "Would you bring this to an audit?" (the ultimate question)
□ Run beta for 2 weeks
□ Collect feedback, identify critical issues
□ Fix critical issues
□ Collect testimonials (with permission to use name/role)
□ Finalize pricing based on feedback
```

### Step 6.4: Pre-Launch Checklist

```
Tasks:
□ Legal:
  - Terms of Service (ROYS delivers guidance, not regulatory advice)
  - Privacy Policy (GDPR-aware, data handling)
  - Refund policy
  - Content disclaimer: "requires organization-specific customization"
□ Content:
  - 21 CFR 820 content updated for QMSR (Evelyn, pre-launch requirement)
  - All content blocks reviewed and status = 'approved'
  - Landing page copy finalized
  - Testimonials from beta testers placed
□ Technical:
  - All Stripe products configured in live mode
  - Webhook handler tested with live events
  - SSL certificate valid and auto-renewing
  - Backup system verified
  - Monitoring active
□ Marketing (minimal for launch):
  - Landing page live
  - Evelyn's LinkedIn profile updated
  - Announcement post drafted
  - Email to beta testers: "We're live!"
  - Email to Evelyn's network: soft launch announcement
```

### Step 6.5: Launch

```
Tasks:
□ Switch Stripe to live mode
□ Open registration to public
□ Evelyn publishes LinkedIn announcement
□ Email waitlist / network
□ Monitor for first 48 hours:
  - Server health (CPU, memory, disk)
  - Error logs
  - Stripe webhook delivery
  - First purchase celebration! 🎉
```

### Phase 6 Definition of Done
- [ ] Application deployed and running on Digital Ocean
- [ ] SSL working, domain configured
- [ ] Beta testing complete, critical feedback addressed
- [ ] Stripe live mode active
- [ ] Legal pages published
- [ ] 21 CFR 820 content updated for QMSR
- [ ] Monitoring and backups operational
- [ ] At least 3 testimonials collected
- [ ] ROYS is live and accepting payments

---

## Cross-Phase: Continuous Items

These tasks run alongside the phases, not within a specific one:

### Content Quality (Evelyn, throughout all phases)

```
□ Review CLI-generated output (Phase 1)
□ Review Word document quality (Phase 2)
□ Update 21 CFR 820 content for QMSR (before launch)
□ Identify and fill content gaps discovered during testing
□ Write enhanced-tier risk content where missing
□ Verify traceability mappings are at sub-clause level
□ Prepare 2-3 "hero" SOPs for marketing (best examples)
```

### LinkedIn Content (Evelyn, starting Phase 3)

```
□ 1 post/week minimum during build phase
□ Topics: QMSR remediation, audit tips, common 483 observations
□ Build connections with quality professionals
□ Do NOT market ROYS until close to launch
□ Content serves consulting credibility in the meantime
```

### Beta Tester Relationships (Evelyn, starting Phase 4)

```
□ Reach out to 9 identified testers, explain what's coming
□ Set expectations: beta access in exchange for honest feedback + testimonial
□ Schedule feedback sessions
□ Maintain relationships — these become first paying customers
```

---

## Timeline Summary

| Phase | Scope | Weeks | Depends On |
|---|---|---|---|
| **Phase 0** | Foundation (DB, schema, import) | 1-2 | Evelyn's Excel files |
| **Phase 1** | Assembly Engine | 3-4 | Phase 0 |
| **Phase 2** | Document Generation | 5-6 | Phase 1 + Evelyn template approval |
| **Phase 3** | Frontend Core | 7-9 | Phase 2 (can start in parallel with Phase 2) |
| **Phase 4** | Payments (Stripe) | 10-11 | Phase 3 |
| **Phase 5** | Admin Panel | 12-13 | Phase 4 (can start in parallel) |
| **Phase 6** | Deploy, Beta, Launch | 14-16 | Phase 5 |

**Critical path dependencies:**
- Phase 0 blocks everything
- Phase 1-2 are sequential (assembly before doc gen)
- Phase 3 can start frontend scaffolding in parallel with Phase 2
- Phase 4-5 can partially overlap
- Phase 6 requires all other phases complete

**At ~10 hrs/week:** Realistic timeline is **14-18 weeks** (3.5-4.5 months)
**At ~15-20 hrs/week:** Could compress to **10-14 weeks** (2.5-3.5 months)

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Content import fails or data is messy | Phase 0 includes thorough verification. Budget extra time for data cleanup. |
| Document output quality is poor | Phase 2 has dedicated quality validation step. Iterate before moving forward. |
| Stripe integration complexity | Use Stripe test mode throughout. Only switch to live in Phase 6. |
| Part-time execution stalls | Each phase has clear "done" criteria. Can pause and resume cleanly. |
| Beta feedback requires major changes | Beta in Phase 6 is 2 weeks. Budget 1 week for fixes. If fundamental issues, delay launch. |
| Evelyn's content needs QMSR updates | Flagged as pre-launch requirement. Must complete before Phase 6 launch. |
| 50-100 concurrent users overwhelms server | Load test in Phase 6. 4GB droplet with 8 doc-gen workers handles this. Upgrade to 8GB if needed ($48/mo). |

---

## Budget Summary

| Item | One-Time | Monthly |
|---|---|---|
| Digital Ocean Droplet (4GB) | — | $24 |
| DO Automated Backups | — | $4.80 |
| Domain registration | $12/yr | — |
| Stripe fees (2.9% + $0.30/txn) | — | Variable |
| docxtpl + python-docx | — | Free (open source) |
| Let's Encrypt SSL | — | Free |
| Cloudflare DNS + CDN | — | Free tier |
| **Total infrastructure** | **~$12/yr** | **~$30/mo** |

Development cost: Ninja labor (us, with Claude Code). No external contractors needed.

---

*This plan is designed to be executed incrementally. Every phase produces working, testable output. The content library in PostgreSQL is the foundation — everything else is a delivery mechanism. Start with Phase 0 and the rest follows.*

*Let's build this thing. Ninjas Assemble.*

*Document Version: 1.0 — February 22, 2026*
*CONFIDENTIAL — Roystonea Compliance LLC*
