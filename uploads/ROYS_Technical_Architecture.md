# ROYS (Roystonea Documents) — Technical Architecture Proposal
## Version 1.0 — February 22, 2026
### CONFIDENTIAL — Roystonea Compliance LLC

---

## 1. Executive Summary

This document defines the technical architecture for ROYS, a SaaS platform that generates audit-aligned, regulation-specific SOPs for FDA-regulated and ISO-certified organizations. Built as a custom stack using Python/FastAPI + React + PostgreSQL, designed for 50-100 concurrent users at launch.

**Key Design Principles:**
- The content library (regulatory knowledge graph) is the core IP — it lives in PostgreSQL, fully portable
- Deterministic assembly — same inputs always produce the same output, no AI in generation
- Professional Word (.docx) output is the product — output quality is non-negotiable
- SOP generation, not document management — stay in lane
- Designed for the ceiling (50-100 concurrent users from day one)

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Backend** | Python 3.13 + FastAPI | Async-native, excellent for concurrent doc generation, team already knows it |
| **Frontend** | React 19 + Vite + Tailwind v4 | Same stack as the Dojo — proven, fast, modern |
| **Database** | PostgreSQL 17 | Always PostgreSQL. Robust, JSONB for flexible metadata, full-text search |
| **Document Generation** | docxtpl (Jinja2 + python-docx) | Template-based Word generation, non-dev can edit templates in Word |
| **Payments** | Stripe (Checkout + Billing + Meters + Portal) | Industry standard, handles mixed pricing model |
| **Auth** | JWT (access + refresh tokens) | Stateless, scalable, standard B2B SaaS pattern |
| **File Storage** | Local filesystem + S3-compatible (future) | Generated docs stored temporarily, delivered via signed URLs |
| **Task Queue** | asyncio ThreadPoolExecutor | Document generation offloaded to thread pool (Celery if needed later) |
| **Hosting** | Linux server (existing infra) or VPS | Docker-ready, can move to any cloud |
| **Reverse Proxy** | Nginx | SSL termination, static assets, rate limiting |

### Why NOT Bubble.io

Evelyn has a paid Bubble.io account (1 year). The custom stack is the better path because:
- Full control over document output quality (the product IS the document)
- No vendor lock-in on the core IP
- PostgreSQL from day one (portable, queryable, versionable)
- SOC 2 readiness when enterprise customers come
- No performance ceiling for concurrent document generation
- We can build exactly what the product needs, nothing more

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (port 443)                        │
│                    SSL + Static Assets + Proxy                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐    ┌──────────▼──────────┐
     │  React Frontend  │    │   FastAPI Backend    │
     │  (Vite build)    │    │   (port 8070)        │
     │  /static/        │    │   /api/              │
     └──────────────────┘    └──────────┬───────────┘
                                        │
                    ┌───────────────────┬┴──────────────────┐
                    │                   │                    │
           ┌────────▼──────┐  ┌────────▼──────┐   ┌───────▼────────┐
           │  PostgreSQL    │  │  Doc Generator │   │  Stripe API    │
           │  (roys DB)     │  │  (ThreadPool)  │   │  Webhooks      │
           │                │  │  docxtpl       │   │  Meters        │
           └────────────────┘  └────────────────┘   └────────────────┘
```

### Request Flow: SOP Generation

```
1. User selects standards/regulations + SOP + content tier + template structure
2. Frontend POST /api/generate
3. Backend validates purchase/subscription entitlement
4. Assembly engine queries PostgreSQL:
   - Get SOP metadata
   - Get applicable requirements for selected standards
   - Get content blocks for the SOP + standard combination + tier
   - Get requirement-to-SOP mappings for traceability table
5. Document generator (thread pool):
   - Load .docx template matching selected structure
   - Render via docxtpl with assembled content
   - Apply tier-specific formatting (traceability depth)
6. Return download URL (signed, time-limited)
7. Record usage in DB + report to Stripe Meter
```

---

## 4. Database Schema

### Core Content Tables (The Knowledge Graph)

```sql
-- ============================================================
-- REGULATORY KNOWLEDGE GRAPH — This is the core IP
-- ============================================================

-- Standards and Regulations
-- UI must distinguish: Standards (voluntary) vs Regulations (legally binding)
CREATE TABLE standards (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(50) UNIQUE NOT NULL,  -- 'ISO_13485_2016', '21_CFR_820'
    name            VARCHAR(200) NOT NULL,         -- 'ISO 13485:2016'
    full_title      TEXT NOT NULL,                  -- 'Medical devices — Quality management systems'
    standard_type   VARCHAR(20) NOT NULL CHECK (standard_type IN ('standard', 'regulation')),
    version         VARCHAR(20),                   -- '2016', '2026 QMSR'
    effective_date  DATE,
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'superseded', 'draft')),
    superseded_by   INTEGER REFERENCES standards(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Regulatory Requirements (610+ individual requirements)
CREATE TABLE requirements (
    id              SERIAL PRIMARY KEY,
    standard_id     INTEGER NOT NULL REFERENCES standards(id),
    clause_number   VARCHAR(50) NOT NULL,          -- '4.2.4', '820.40', '5.6.2.1'
    clause_title    VARCHAR(300),                   -- 'Control of Documents'
    requirement_text TEXT NOT NULL,                 -- Paraphrased (never quoted for ISO copyright)
    requirement_type VARCHAR(20) DEFAULT 'shall'
                    CHECK (requirement_type IN ('shall', 'should', 'may', 'informational')),
    parent_clause   VARCHAR(50),                   -- For hierarchical navigation
    sort_order      INTEGER DEFAULT 0,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(standard_id, clause_number)
);

-- Standard Operating Procedures (81 SOPs)
CREATE TABLE sops (
    id              SERIAL PRIMARY KEY,
    sop_number      VARCHAR(20) UNIQUE NOT NULL,   -- 'SOP-001'
    title           VARCHAR(300) NOT NULL,          -- 'Document Control'
    category        VARCHAR(100),                   -- 'Quality Management', 'Production', 'Design'
    description     TEXT,
    complexity      VARCHAR(20) DEFAULT 'standard'
                    CHECK (complexity IN ('simple', 'standard', 'complex')),
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Requirement-to-SOP Mappings (539+ traceable connections)
CREATE TABLE requirement_sop_mappings (
    id              SERIAL PRIMARY KEY,
    requirement_id  INTEGER NOT NULL REFERENCES requirements(id),
    sop_id          INTEGER NOT NULL REFERENCES sops(id),
    coverage_type   VARCHAR(20) DEFAULT 'primary'
                    CHECK (coverage_type IN ('primary', 'supporting')),
    sop_section     VARCHAR(50),                   -- Which section of the SOP addresses this
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(requirement_id, sop_id)
);

-- Content Blocks (567+ blocks, 7 sections per SOP)
-- Keyed to standard COMBINATIONS, not individual standards
CREATE TABLE content_blocks (
    id              SERIAL PRIMARY KEY,
    sop_id          INTEGER NOT NULL REFERENCES sops(id),
    section_type    VARCHAR(30) NOT NULL
                    CHECK (section_type IN (
                        'purpose', 'scope', 'definitions',
                        'responsibilities', 'procedure', 'records', 'references'
                    )),
    content_tier    VARCHAR(20) NOT NULL DEFAULT 'core'
                    CHECK (content_tier IN ('core', 'enhanced')),
    standard_combo  VARCHAR(200) NOT NULL,         -- 'ISO_13485_2016' or 'ISO_13485_2016+21_CFR_820'
    content_text    TEXT NOT NULL,                  -- The actual SOP content (rich text / markdown)
    version         INTEGER DEFAULT 1,
    status          VARCHAR(20) DEFAULT 'approved'
                    CHECK (status IN ('draft', 'in_review', 'approved', 'superseded')),
    authored_by     VARCHAR(100) DEFAULT 'Evelyn Rodriguez Gomez',
    change_reason   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Content Block Version History (full audit trail)
CREATE TABLE content_block_versions (
    id              SERIAL PRIMARY KEY,
    content_block_id INTEGER NOT NULL REFERENCES content_blocks(id),
    version         INTEGER NOT NULL,
    content_text    TEXT NOT NULL,
    change_reason   TEXT,
    changed_by      VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Cross-references between SOPs (Enhanced tier feature)
CREATE TABLE sop_cross_references (
    id              SERIAL PRIMARY KEY,
    source_sop_id   INTEGER NOT NULL REFERENCES sops(id),
    target_sop_id   INTEGER NOT NULL REFERENCES sops(id),
    reference_type  VARCHAR(50),                   -- 'requires', 'related', 'supersedes'
    context         TEXT,                           -- Why this cross-reference exists
    UNIQUE(source_sop_id, target_sop_id)
);

-- Template Structures (how the document is organized)
CREATE TABLE template_structures (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,          -- 'Standard 7-Section', 'Condensed', 'FDA-Style'
    description     TEXT,
    sections        JSONB NOT NULL,                 -- Ordered list of section_types to include
    docx_template   VARCHAR(200) NOT NULL,          -- Path to .docx template file
    is_default      BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Standard Combinations (pre-defined valid combos for the assembly engine)
CREATE TABLE standard_combinations (
    id              SERIAL PRIMARY KEY,
    combo_key       VARCHAR(200) UNIQUE NOT NULL,   -- 'ISO_13485_2016+21_CFR_820'
    display_name    VARCHAR(200) NOT NULL,           -- 'ISO 13485 + 21 CFR 820 (QMSR)'
    standards       INTEGER[] NOT NULL,              -- Array of standard IDs
    marketing_bundle VARCHAR(100),                   -- 'Medical Device QMS', 'Lab Accreditation'
    is_active       BOOLEAN DEFAULT TRUE
);

-- Indexes for assembly engine performance
CREATE INDEX idx_requirements_standard ON requirements(standard_id);
CREATE INDEX idx_content_blocks_sop ON content_blocks(sop_id, section_type);
CREATE INDEX idx_content_blocks_combo ON content_blocks(standard_combo, content_tier);
CREATE INDEX idx_content_blocks_status ON content_blocks(status) WHERE status = 'approved';
CREATE INDEX idx_mappings_sop ON requirement_sop_mappings(sop_id);
CREATE INDEX idx_mappings_requirement ON requirement_sop_mappings(requirement_id);
```

### User & Commerce Tables

```sql
-- ============================================================
-- USERS, PURCHASES & SUBSCRIPTIONS
-- ============================================================

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200),
    company_name    VARCHAR(200),
    job_title       VARCHAR(200),
    stripe_customer_id VARCHAR(100) UNIQUE,
    is_active       BOOLEAN DEFAULT TRUE,
    is_admin        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Track what each user has purchased / can access
CREATE TABLE user_sop_access (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    sop_id          INTEGER NOT NULL REFERENCES sops(id),
    content_tier    VARCHAR(20) NOT NULL,           -- 'core' or 'enhanced'
    standard_combo  VARCHAR(200) NOT NULL,
    template_structure_id INTEGER REFERENCES template_structures(id),
    purchase_type   VARCHAR(30) NOT NULL
                    CHECK (purchase_type IN ('single', 'bundle', 'subscription')),
    stripe_payment_id VARCHAR(100),
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    document_path   VARCHAR(500),                   -- Path to generated .docx file
    download_count  INTEGER DEFAULT 0
);

-- Subscription tracking (mirrors Stripe, for app-side entitlement checks)
CREATE TABLE subscriptions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    stripe_subscription_id VARCHAR(100) UNIQUE,
    plan_type       VARCHAR(30) NOT NULL
                    CHECK (plan_type IN (
                        'individual_core_monthly', 'individual_core_annual',
                        'individual_enhanced_monthly', 'individual_enhanced_annual',
                        'team_core_monthly', 'team_core_annual',
                        'team_enhanced_monthly', 'team_enhanced_annual'
                    )),
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'trialing', 'past_due', 'canceled', 'expired')),
    sops_per_month  INTEGER NOT NULL,               -- 5 for individual, 15 for team
    sops_used_this_period INTEGER DEFAULT 0,
    current_period_start TIMESTAMPTZ,
    current_period_end   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Team members (for team subscriptions)
CREATE TABLE team_members (
    id              SERIAL PRIMARY KEY,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id),
    user_id         INTEGER NOT NULL REFERENCES users(id),
    role            VARCHAR(20) DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    invited_at      TIMESTAMPTZ DEFAULT NOW(),
    accepted_at     TIMESTAMPTZ
);

-- Consulting requests
CREATE TABLE consulting_requests (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    sop_access_id   INTEGER NOT NULL REFERENCES user_sop_access(id),
    content_tier    VARCHAR(20) NOT NULL,
    stripe_payment_id VARCHAR(100),
    amount_cents    INTEGER NOT NULL,
    status          VARCHAR(30) DEFAULT 'pending'
                    CHECK (status IN ('pending', 'paid', 'in_progress', 'delivered', 'canceled')),
    notes           TEXT,                           -- Customer notes for the review
    delivered_document_path VARCHAR(500),
    requested_at    TIMESTAMPTZ DEFAULT NOW(),
    delivered_at    TIMESTAMPTZ
);

-- Usage tracking (application-side, supplements Stripe Meters)
CREATE TABLE usage_log (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    action          VARCHAR(50) NOT NULL,            -- 'sop_generated', 'sop_downloaded', 'consulting_requested'
    sop_id          INTEGER REFERENCES sops(id),
    standard_combo  VARCHAR(200),
    content_tier    VARCHAR(20),
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_log_user ON usage_log(user_id, created_at DESC);
CREATE INDEX idx_usage_log_action ON usage_log(action, created_at DESC);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id) WHERE status = 'active';
CREATE INDEX idx_consulting_status ON consulting_requests(status) WHERE status IN ('pending', 'paid', 'in_progress');
```

---

## 5. Assembly Engine

The assembly engine is the heart of ROYS. It is purely deterministic — no AI, no fuzzy logic.

```python
# Simplified assembly logic

async def assemble_sop(
    sop_id: int,
    standard_ids: list[int],
    content_tier: str,          # 'core' or 'enhanced'
    template_structure_id: int,
    db: AsyncSession,
) -> AssembledSOP:
    """
    Assemble an SOP from content blocks based on user selections.
    Same inputs ALWAYS produce the same output.
    """
    # 1. Resolve standard combination key
    standards = await db.execute(
        select(Standard).where(Standard.id.in_(standard_ids)).order_by(Standard.code)
    )
    combo_key = "+".join(s.code for s in standards)

    # 2. Get SOP metadata
    sop = await db.get(SOP, sop_id)

    # 3. Get template structure (which sections to include)
    structure = await db.get(TemplateStructure, template_structure_id)
    sections_to_include = structure.sections  # e.g., ['purpose', 'scope', 'procedure', 'records']

    # 4. Get content blocks for this SOP + combo + tier
    #    Fall back to closest match if exact combo doesn't exist
    blocks = await get_content_blocks(db, sop_id, combo_key, content_tier, sections_to_include)

    # 5. Get requirement mappings for traceability table
    mappings = await get_traceability_mappings(db, sop_id, standard_ids)

    # 6. Get cross-references (Enhanced tier only)
    cross_refs = []
    if content_tier == 'enhanced':
        cross_refs = await get_cross_references(db, sop_id)

    return AssembledSOP(
        sop=sop,
        standards=standards,
        content_blocks=blocks,
        traceability_mappings=mappings,
        cross_references=cross_refs,
        template_structure=structure,
        content_tier=content_tier,
    )


async def get_content_blocks(db, sop_id, combo_key, tier, sections):
    """
    Retrieve content blocks with fallback logic:
    1. Try exact combo match at requested tier
    2. Try exact combo match at core tier (if enhanced was requested)
    3. Try individual standard blocks and merge
    """
    blocks = {}
    for section in sections:
        block = await db.execute(
            select(ContentBlock)
            .where(
                ContentBlock.sop_id == sop_id,
                ContentBlock.section_type == section,
                ContentBlock.standard_combo == combo_key,
                ContentBlock.content_tier == tier,
                ContentBlock.status == 'approved',
            )
            .order_by(ContentBlock.version.desc())
            .limit(1)
        )
        result = block.scalar_one_or_none()

        if not result and tier == 'enhanced':
            # Fallback to core tier for this section
            result = await _get_block(db, sop_id, section, combo_key, 'core')

        if result:
            blocks[section] = result

    return blocks
```

### Content Block Fallback Strategy

The assembly engine handles standard combinations gracefully:

```
User selects: ISO 13485 + 21 CFR 820

Assembly tries (in order):
1. content_blocks WHERE standard_combo = 'ISO_13485_2016+21_CFR_820' ← Exact match (best)
2. content_blocks WHERE standard_combo = 'ISO_13485_2016' UNION
   content_blocks WHERE standard_combo = '21_CFR_820'         ← Merge individual blocks
3. Error: "Content not yet available for this combination"     ← Graceful failure
```

This means Evelyn can author content for common combinations first and add more over time without breaking anything.

---

## 6. Document Generation

### Template-Based Approach with docxtpl

```
templates/
├── standard_7section.docx      # Full 7-section SOP template
├── condensed_5section.docx     # Shortened format (no definitions/references)
├── fda_style.docx              # FDA-preferred formatting
└── custom/                     # Future custom templates
```

Each template is a professionally designed Word document with Jinja2 tags:

```
{{ sop_number }} — {{ sop_title }}

Purpose
{{ purpose_content }}

Scope
{{ scope_content }}

{% if 'definitions' in sections %}
Definitions
{{ definitions_content }}
{% endif %}

Responsibilities
{{ responsibilities_content }}

Procedure
{{ procedure_content }}

Records
{{ records_content }}

{% if 'references' in sections %}
References
{{ references_content }}
{% endif %}

{% if content_tier == 'enhanced' %}
Appendix A: Traceability Matrix
{% for mapping in traceability_mappings %}
{{ mapping.clause_number }} | {{ mapping.clause_title }} | {{ mapping.sop_section }}
{% endfor %}

{% if cross_references %}
Appendix B: Related Procedures
{% for ref in cross_references %}
{{ ref.target_sop_number }} — {{ ref.target_sop_title }} ({{ ref.reference_type }})
{% endfor %}
{% endif %}
{% endif %}
```

### Document Generator Service

```python
from concurrent.futures import ThreadPoolExecutor
from docxtpl import DocxTemplate
import asyncio

# Thread pool for document generation (CPU-bound work)
doc_executor = ThreadPoolExecutor(max_workers=8)

# Cache parsed templates in memory
_template_cache: dict[str, DocxTemplate] = {}

def _get_template(template_path: str) -> DocxTemplate:
    """Load and cache .docx templates."""
    if template_path not in _template_cache:
        _template_cache[template_path] = DocxTemplate(template_path)
    # Always return a copy to prevent cross-request contamination
    return DocxTemplate(template_path)


def _render_document(assembled: AssembledSOP, output_path: str) -> str:
    """Render assembled SOP to Word document. Runs in thread pool."""
    tpl = _get_template(assembled.template_structure.docx_template)

    context = {
        "sop_number": assembled.sop.sop_number,
        "sop_title": assembled.sop.title,
        "sop_category": assembled.sop.category,
        "standards_list": ", ".join(s.name for s in assembled.standards),
        "content_tier": assembled.content_tier,
        "sections": [b.section_type for b in assembled.content_blocks.values()],
        "generation_date": datetime.now().strftime("%B %d, %Y"),

        # Section content
        "purpose_content": assembled.content_blocks.get("purpose", {}).content_text,
        "scope_content": assembled.content_blocks.get("scope", {}).content_text,
        "definitions_content": assembled.content_blocks.get("definitions", {}).content_text,
        "responsibilities_content": assembled.content_blocks.get("responsibilities", {}).content_text,
        "procedure_content": assembled.content_blocks.get("procedure", {}).content_text,
        "records_content": assembled.content_blocks.get("records", {}).content_text,
        "references_content": assembled.content_blocks.get("references", {}).content_text,

        # Traceability (depth depends on tier)
        "traceability_mappings": [
            {
                "standard_name": m.standard_name,
                "clause_number": m.clause_number,
                "clause_title": m.clause_title,
                "sop_section": m.sop_section,
                "coverage_type": m.coverage_type,
            }
            for m in assembled.traceability_mappings
        ],

        # Cross-references (Enhanced only)
        "cross_references": [
            {
                "target_sop_number": r.target_sop.sop_number,
                "target_sop_title": r.target_sop.title,
                "reference_type": r.reference_type,
            }
            for r in assembled.cross_references
        ],

        # Placeholders for customer customization
        "company_name": "[YOUR COMPANY NAME]",
        "effective_date": "[EFFECTIVE DATE]",
        "document_number": "[DOCUMENT NUMBER]",
        "revision": "[REV]",
        "approved_by": "[APPROVED BY]",
    }

    tpl.render(context)
    tpl.save(output_path)
    return output_path


async def generate_sop_document(assembled: AssembledSOP) -> str:
    """Async wrapper — offloads rendering to thread pool."""
    output_path = f"/tmp/roys_generated/{uuid4()}.docx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    result = await asyncio.get_event_loop().run_in_executor(
        doc_executor, _render_document, assembled, output_path
    )
    return result
```

### Core vs Enhanced Output Differences

| Feature | Core | Enhanced |
|---|---|---|
| SOP content (all selected standards) | Full content | Full content |
| Risk elements | Baseline (inherent to process) | Deeper risk tools (mini-FMEA, risk assessment) |
| Traceability | Reference list of applicable clauses | Full matrix: clause → SOP section mapping |
| Cross-references | Standalone document | Links to related SOPs |
| Placeholders | Standard customization markers | Standard customization markers |
| Formatting | Professional | Professional |

---

## 7. API Design

### Public API Endpoints

```
Authentication
  POST   /api/auth/register              Create account
  POST   /api/auth/login                 Login (returns JWT)
  POST   /api/auth/refresh               Refresh access token
  GET    /api/auth/me                    Current user profile

Catalog (Public — no auth required for browsing)
  GET    /api/standards                  List all standards/regulations
  GET    /api/sops                       List all SOPs (filterable by standard)
  GET    /api/sops/:id                   SOP detail (metadata, applicable standards, sections)
  GET    /api/sops/:id/preview           Preview: which requirements this SOP addresses
  GET    /api/template-structures        Available document structures
  GET    /api/bundles                    Marketing bundles (Medical Device QMS, Lab, GLP)

Generation (Auth required)
  POST   /api/generate                   Generate SOP document
    Body: {
      sop_id: int,
      standard_ids: int[],
      content_tier: "core" | "enhanced",
      template_structure_id: int
    }
    Returns: { download_url: string, access_id: int }

  GET    /api/generate/:access_id/download   Download generated document

Purchases & Subscriptions (Auth required)
  POST   /api/checkout/single            Create Stripe Checkout for single SOP
  POST   /api/checkout/bundle            Create Stripe Checkout for bundle (5 SOPs)
  POST   /api/checkout/subscription      Create Stripe Checkout for subscription
  GET    /api/billing/portal             Get Stripe Billing Portal URL
  GET    /api/billing/usage              Current period usage stats

  POST   /api/consulting/request         Request expert review
    Body: { sop_access_id: int, notes: string }

User Account (Auth required)
  GET    /api/account/library            User's generated SOPs + download history
  GET    /api/account/consulting         Consulting request status

Stripe Webhooks
  POST   /api/webhooks/stripe            Stripe event handler

Admin (Auth required, admin only)
  GET    /api/admin/content-blocks       List/search all content blocks
  PUT    /api/admin/content-blocks/:id   Update content block (creates version)
  GET    /api/admin/sops/:id/blocks      All blocks for an SOP
  GET    /api/admin/standards/:id/coverage  Coverage report for a standard
  GET    /api/admin/consulting           Consulting request queue
  PUT    /api/admin/consulting/:id       Update consulting request status
  GET    /api/admin/analytics            Usage analytics dashboard data
```

---

## 8. Stripe Integration Architecture

### Products & Prices Setup

```python
# Stripe product configuration
STRIPE_PRODUCTS = {
    # One-time purchases
    "single_core":     {"price": 4900,   "type": "one_time"},   # $49
    "single_enhanced": {"price": 7500,   "type": "one_time"},   # $75
    "bundle_core":     {"price": 15900,  "type": "one_time"},   # $159 (5 SOPs)
    "bundle_enhanced": {"price": 23900,  "type": "one_time"},   # $239 (5 SOPs)

    # Subscriptions
    "individual_core_monthly":     {"price": 7900,   "interval": "month"},  # $79/mo
    "individual_enhanced_monthly": {"price": 11900,  "interval": "month"},  # $119/mo
    "team_core_monthly":           {"price": 19900,  "interval": "month"},  # $199/mo
    "team_enhanced_monthly":       {"price": 29900,  "interval": "month"},  # $299/mo

    # Annual (17% discount)
    "individual_core_annual":     {"price": 79000,   "interval": "year"},   # $790/yr
    "individual_enhanced_annual": {"price": 119000,  "interval": "year"},   # $1,190/yr
    "team_core_annual":           {"price": 199000,  "interval": "year"},   # $1,990/yr
    "team_enhanced_annual":       {"price": 299000,  "interval": "year"},   # $2,990/yr

    # Overages (subscribers only)
    "overage_core":     {"price": 3400,  "type": "one_time"},  # $34/SOP
    "overage_enhanced": {"price": 5300,  "type": "one_time"},  # $53/SOP

    # Consulting add-ons
    "consulting_core_onetime":    {"price": 12900, "type": "one_time"},  # $129
    "consulting_enhanced_onetime":{"price": 19900, "type": "one_time"},  # $199
    "consulting_core_sub":        {"price": 9900,  "type": "one_time"},  # $99
    "consulting_enhanced_sub":    {"price": 15900, "type": "one_time"},  # $159
}
```

### Webhook Handler

```python
@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)

    match event["type"]:
        case "checkout.session.completed":
            await handle_checkout_complete(event["data"]["object"])

        case "customer.subscription.created" | "customer.subscription.updated":
            await handle_subscription_change(event["data"]["object"])

        case "customer.subscription.deleted":
            await handle_subscription_canceled(event["data"]["object"])

        case "invoice.payment_succeeded":
            await handle_payment_success(event["data"]["object"])

        case "invoice.payment_failed":
            await handle_payment_failure(event["data"]["object"])

        case "invoice.upcoming":
            await handle_upcoming_invoice(event["data"]["object"])

    return {"received": True}
```

### Usage Metering

```python
async def record_sop_generation(user_id: int, stripe_customer_id: str):
    """Record SOP generation for billing purposes."""
    # 1. Record in our DB
    await db.execute(insert(UsageLog).values(
        user_id=user_id, action="sop_generated"
    ))

    # 2. Report to Stripe Meter (for subscription overage billing)
    if stripe_customer_id:
        stripe.billing.MeterEvent.create(
            event_name="sops_generated",
            payload={"value": "1", "stripe_customer_id": stripe_customer_id},
        )

    # 3. Update subscription usage counter
    await increment_subscription_usage(user_id)
```

---

## 9. Admin Panel

Evelyn needs to manage 567+ content blocks without touching code.

### Admin Features (MVP)

- **Content Block Editor:** Rich text editor for each block. Shows SOP, section, standard combo, version history.
- **Bulk SOP View:** See all 7 sections of an SOP side-by-side. Edit in context.
- **Standard Coverage Report:** For each standard, see which requirements are mapped, which SOPs cover them, identify gaps.
- **Version Control:** Every save creates a version with timestamp and change reason. Cannot save without a change reason.
- **Status Workflow:** Draft → In Review → Approved → Superseded. Only "Approved" blocks are served.
- **Consulting Queue:** List of pending consulting requests with status management.
- **Analytics Dashboard:** SOPs sold by type, revenue by tier, usage patterns.

### Content Import (Excel → PostgreSQL)

One-time migration script to move Evelyn's existing Excel content into PostgreSQL:

```python
# import_content.py — Run once to seed the database
import pandas as pd

def import_requirements(excel_path: str):
    """Import requirements from Evelyn's Excel file."""
    df = pd.read_excel(excel_path, sheet_name="Requirements")
    for _, row in df.iterrows():
        db.execute(insert(Requirement).values(
            standard_id=lookup_standard(row["Standard"]),
            clause_number=row["Clause"],
            clause_title=row["Title"],
            requirement_text=row["Requirement Text"],
            requirement_type=row["Type"],
        ))

# Similar functions for SOPs, content blocks, and mappings
```

---

## 10. Security

| Requirement | Implementation |
|---|---|
| **Authentication** | JWT (access token 15min, refresh token 7 days) |
| **Password Storage** | bcrypt (cost factor 12) |
| **HTTPS** | Nginx SSL termination (Let's Encrypt) |
| **CORS** | Whitelist production domain only |
| **Rate Limiting** | Nginx rate limiting + application-level per-user |
| **Input Validation** | Pydantic models on all API endpoints |
| **SQL Injection** | SQLAlchemy ORM (parameterized queries) |
| **XSS** | React (auto-escapes), CSP headers |
| **Stripe Webhooks** | Signature verification on every event |
| **File Downloads** | Signed URLs with expiration (1 hour) |
| **Admin Access** | Separate admin JWT claim, middleware check |
| **Audit Log** | All content changes versioned, all user actions logged |

### Future (Post-Launch)
- SOC 2 Type II preparation (when enterprise customers require it)
- Data encryption at rest (PostgreSQL pgcrypto)
- MFA for admin accounts

---

## 11. Project Structure

```
roys/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Environment config
│   ├── database.py                 # PostgreSQL connection + session
│   ├── models/
│   │   ├── content.py              # Standards, Requirements, SOPs, ContentBlocks
│   │   ├── users.py                # Users, Subscriptions, TeamMembers
│   │   └── commerce.py             # Access, ConsultingRequests, UsageLog
│   ├── routers/
│   │   ├── auth.py                 # Registration, login, JWT
│   │   ├── catalog.py              # Public browsing endpoints
│   │   ├── generate.py             # SOP generation
│   │   ├── billing.py              # Stripe checkout, portal, webhooks
│   │   ├── consulting.py           # Consulting request flow
│   │   ├── account.py              # User library, history
│   │   └── admin.py                # Content management, analytics
│   ├── services/
│   │   ├── assembly.py             # Assembly engine (the core logic)
│   │   ├── docgen.py               # Document generation (docxtpl)
│   │   ├── stripe_service.py       # Stripe API wrapper
│   │   └── email_service.py        # Transactional emails
│   ├── migrations/                 # Alembic migrations
│   ├── templates/                  # Word document templates (.docx)
│   ├── scripts/
│   │   └── import_content.py       # Excel → PostgreSQL migration
│   └── tests/
│       ├── test_assembly.py
│       ├── test_docgen.py
│       └── test_billing.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CatalogBrowser.tsx   # Standards + SOP selection
│   │   │   ├── SOPCard.tsx          # Individual SOP display
│   │   │   ├── StandardSelector.tsx # Standard/regulation checkboxes
│   │   │   ├── TierSelector.tsx     # Core vs Enhanced selection
│   │   │   ├── StructureSelector.tsx# Template structure selection
│   │   │   ├── TraceabilityPreview.tsx # Preview requirement coverage
│   │   │   ├── CheckoutFlow.tsx     # Purchase/subscribe flow
│   │   │   └── ConsultingRequest.tsx# Request expert review
│   │   ├── pages/
│   │   │   ├── Landing.tsx          # Public landing page
│   │   │   ├── Catalog.tsx          # Browse SOPs
│   │   │   ├── Generate.tsx         # SOP generation wizard
│   │   │   ├── Account.tsx          # User library
│   │   │   └── Admin.tsx            # Content management
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useStripe.ts
│   │   └── App.tsx
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 12. MVP Feature Checklist

### Must Have (Launch)

- [ ] Landing page with value proposition, standard coverage, sample traceability
- [ ] User registration and login (JWT auth)
- [ ] Standard/regulation selection (checkboxes with type labels)
- [ ] SOP catalog browsable by category, filterable by selected standards
- [ ] Template structure selection (which sections to include)
- [ ] SOP generation: select → assemble → render → download Word doc
- [ ] Traceability table in generated document (tier-dependent depth)
- [ ] Core vs Enhanced content tier selection
- [ ] Stripe Checkout: single SOP purchase
- [ ] Stripe Checkout: bundle of 5 SOPs
- [ ] Stripe Checkout: subscription (monthly + annual)
- [ ] Basic account page (download history, re-download)
- [ ] Consulting add-on: "Request Expert Review" button + payment
- [ ] Admin panel: content block CRUD with version history
- [ ] Admin panel: consulting request queue
- [ ] Notification to Evelyn on new consulting requests (email)
- [ ] Professional Word document output with proper formatting
- [ ] Customer customization placeholders clearly marked in output

### Deferred (v1.0 — Post-Launch)

- [ ] Stripe Billing Portal for self-service subscription management
- [ ] Overage billing (Stripe Meters integration)
- [ ] Team subscriptions with seat management
- [ ] Content update alerts for previous purchasers
- [ ] Admin analytics dashboard
- [ ] SEO-optimized blog section

### Deferred (v1.5+)

- [ ] API for eQMS integration
- [ ] Spanish-language content (90 days post-launch)
- [ ] Additional standards (MDSAP, ISO 14971, ISO 15189)

---

## 13. Content Migration Plan

### Phase 1: Schema Design + Seed Data
1. Create PostgreSQL database `roys` with schema above
2. Write import script for Evelyn's Excel files
3. Map Excel column names to database fields
4. Run import, verify counts match (610 requirements, 81 SOPs, 567 blocks, 539 mappings)

### Phase 2: Standard Combination Resolution
1. Analyze which standard combinations exist in the content
2. Create `standard_combinations` records for each valid combo
3. Tag content blocks with their `standard_combo` keys
4. Verify assembly engine can resolve all combinations

### Phase 3: 21 CFR 820 → QMSR Update
1. Evelyn updates content blocks referencing old 21 CFR 820 language
2. Create new standard record for QMSR (supersedes 21 CFR 820)
3. Version old content blocks as "superseded"
4. Create updated content blocks with QMSR references

### Phase 4: Template Design
1. Design 2-3 Word document templates with professional formatting
2. Test with docxtpl rendering
3. Verify output quality with 3-5 quality managers (beta testers)

---

## 14. Deployment Architecture

### Production

```
Server (existing Linux infra or dedicated VPS)
├── Docker Compose
│   ├── roys-backend (FastAPI, port 8070)
│   ├── roys-frontend (Nginx serving built React, port 80/443)
│   └── PostgreSQL 17 (port 5432, roys database)
├── Nginx (reverse proxy, SSL)
├── Let's Encrypt (auto-renew certs)
└── Backups (pg_dump daily to S3-compatible)
```

### Domain
- `roystoneadocs.com`
- SSL via Let's Encrypt
- DNS via Cloudflare (DDoS protection + CDN for static assets)

---

## 15. Development Timeline (Estimated)

| Phase | Scope | Weeks |
|---|---|---|
| **Phase 0: Foundation** | PostgreSQL schema, content import, project scaffolding | 1-2 |
| **Phase 1: Assembly Engine** | Core assembly logic, content block retrieval, fallback strategy | 1-2 |
| **Phase 2: Document Generation** | docxtpl templates, Word output, formatting quality | 1-2 |
| **Phase 3: Frontend Core** | Landing page, catalog browser, standard selector, generation wizard | 2-3 |
| **Phase 4: Payments** | Stripe integration (checkout, webhooks, subscriptions) | 1-2 |
| **Phase 5: Admin Panel** | Content CRUD, version history, consulting queue | 1-2 |
| **Phase 6: Polish & Beta** | Testing, output quality review, beta tester feedback | 1-2 |
| **Total** | | **8-15 weeks** |

Part-time at ~10 hrs/week means the realistic timeline is closer to the higher end. Parallel work on frontend + backend can compress this.

---

*This architecture is designed to be built incrementally. Phase 0-2 can be validated with CLI-only document generation before the frontend exists. The content library in PostgreSQL is the foundation — everything else is a delivery mechanism for that IP.*

*Document Version: 1.0 — February 22, 2026*
*CONFIDENTIAL — Roystonea Compliance LLC*
