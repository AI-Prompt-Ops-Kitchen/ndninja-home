---
name: figma-nb2-integration
domain: Design/Content
level: 3-tomoe
description: Analysis of Figma ecosystem + Nano Banana 2 integration opportunities — Figma Weave (acquired Weavy), Figma Buzz templates, NB2 cost/speed gains, and practical impact on the Ninja content pipeline.
sources:
  - type: blog
    title: "Figma Blog — Welcome Weavy to Figma"
    url: "https://www.figma.com/blog/welcome-weavy-to-figma/"
    date: "2026-02-26"
    confidence: high
  - type: article
    title: "TechCrunch — Figma Acquires Weavy"
    url: "https://techcrunch.com/2025/10/30/figma-acquires-ai-powered-media-generation-company-weavy/"
    date: "2026-02-26"
    confidence: high
  - type: docs
    title: "Figma Weave/Weavy FAQ"
    url: "https://help.figma.com/hc/en-us/articles/35965787376919-Figma-Weave-Weavy-FAQ"
    date: "2026-02-26"
    confidence: high
  - type: blog
    title: "Figma Buzz Landing Page"
    url: "https://www.figma.com/buzz/"
    date: "2026-02-26"
    confidence: high
  - type: blog
    title: "Figma Blog — Introducing Buzz"
    url: "https://www.figma.com/blog/introducing-figma-buzz/"
    date: "2026-02-26"
    confidence: high
  - type: blog
    title: "Google Blog — Nano Banana 2"
    url: "https://blog.google/innovation-and-ai/technology/ai/nano-banana-2/"
    date: "2026-02-26"
    confidence: high
  - type: article
    title: "TechCrunch — Google Launches Nano Banana 2"
    url: "https://techcrunch.com/2026/02/26/google-launches-nano-banana-2-model-with-faster-image-generation/"
    date: "2026-02-26"
    confidence: high
  - type: article
    title: "WaveSpeedAI — NB2 vs NB Pro Comparison"
    url: "https://wavespeed.ai/blog/posts/nano-banana-2-vs-nano-banana-pro-whats-the-difference/"
    date: "2026-02-26"
    confidence: medium
  - type: blog
    title: "Figma Blog — Claude Code to Figma MCP"
    url: "https://www.figma.com/blog/introducing-claude-code-to-figma/"
    date: "2026-02-26"
    confidence: high
  - type: article
    title: "TechCrunch — Figma AI Image Editing"
    url: "https://techcrunch.com/2025/12/10/figma-launches-new-ai-powered-object-removal-and-image-extension/"
    date: "2026-02-26"
    confidence: high
last_updated: 2026-02-26
sources_count: 10
can_do_from_cli: partial
cross_links:
  - figma-design-tool
  - nano-banana-pro
  - fal-ai-image-gen
---

# Figma + Nano Banana 2 Integration — Opportunity Analysis

## Mental Model

Three Figma ecosystem developments converged in late 2025 / early 2026:

| Development | What It Is | Status |
|------------|-----------|--------|
| **Figma Weave** (Weavy acquisition) | Node-based multi-model AI canvas — chain generation + editing + compositing | Separate product at weavy.ai, NOT in Figma editor yet |
| **Figma Buzz** | Brand-locked templates with editable fields + CSV bulk generation | Live, available on Figma plans |
| **Nano Banana 2** | Gemini 3.1 Flash Image — Pro quality at Flash speed, 50% cheaper | Live, model ID: `gemini-3.1-flash-image-preview` |

**Key caveat:** The Instagram post showing NB2 in a design editor was almost certainly **Weavy's standalone interface**, not something built into Figma. Figma Weave integration has no timeline.

---

## Figma Weave (formerly Weavy)

- Figma acquired Weavy in October 2025 for ~$150-200M
- Node-based creative platform chaining multiple AI models with professional editing tools
- **Model selector:** Nano Banana, Flux, Ideogram, Seedream, Sora, Veo, Seedance — pick best model per task
- **Editing tools:** Multi-layer compositing, matte manipulation, typography, color grading, masking, all in visual node graph
- **Key advantage:** Outputs can be branched, remixed, and refined — every step is visible and reproducible
- **Current status:** Available at weavy.ai as separate product. NOT integrated into Figma editor. No timeline given.
- **Our action:** Create free Weavy account to experiment. Do NOT build production workflows on it until Figma integration ships.

---

## Figma Buzz — Brand Templates at Scale

- Simplified tool for non-designers to create on-brand visual assets
- Designers create **locked templates**; editors fill in content fields only
- **AI features:** Image gen/editing via gpt-image-1 (NOT NB2), background removal, upscaling, text tone adjustment, translation
- **Bulk creation:** Upload CSV → populate multiple asset variants from one template (e.g., 10 thumbnail A/B tests in one click)
- **Template types:** Social posts, digital ads, email headers, YouTube thumbnails explicitly supported
- **Brand controls:** Lock logos, colors, fonts. Only designated fields are editable. Prevents off-brand output.

### How This Helps Our Pipeline
1. Design 4 thumbnail templates: Gaming News, Reaction/Opinion, Top 10, Game Review
2. Lock ninja branding (dojo theme, character placement, font choices, color palette)
3. Editable fields: title text, game artwork, episode number, expression
4. CSV bulk generation for A/B thumbnail testing
5. Same templates work for social media (Instagram, Twitter, community posts)

**Important:** Buzz's AI uses gpt-image-1, not NB2. For AI image quality we're better with our direct NB2 API calls. Buzz is valuable for the template/branding system, not the AI model.

---

## Nano Banana 2 — Key Specs

| Dimension | NB Pro | NB2 (Flash Image) |
|-----------|--------|-------------------|
| Model ID | `gemini-3-pro-image-preview` | `gemini-3.1-flash-image-preview` |
| Speed | 8-12s | Under 2s for standard |
| Cost (1K) | ~$0.134 | ~$0.067 (50% cheaper) |
| Quality | Best (deep reasoning) | Near-Pro (vibrant, sharp) |
| Character consistency | Good with reference | Up to 5 characters in one workflow |
| Text rendering | Excellent | Improved, legible on mockups |
| Multi-turn editing | Supported | Better — maintains identity across edits |
| New features | — | Mask-free inpainting, web-search grounding, controllable thinking levels, 512px preview resolution |

**For our Pixar-style content:** NB2 quality is effectively equivalent. Pro still edges ahead on photorealism and complex spatial reasoning, but we don't need that for cartoon avatars.

**Already done:** All pipeline scripts updated to `gemini-3.1-flash-image-preview` (Feb 26, 2026).

---

## Opportunity Rankings

| Priority | Opportunity | Impact | Effort | Status |
|----------|-----------|--------|--------|--------|
| 1 | NB Pro → NB2 model swap | HIGH | LOW | **DONE** (Feb 26) |
| 2 | Figma Buzz thumbnail templates | HIGH | MEDIUM | Not started |
| 3 | NB2 multi-turn character consistency test | HIGH | LOW | Not started |
| 4 | Figma Buzz social media templates | MEDIUM | LOW | Not started |
| 5 | Weavy experimentation (standalone) | MEDIUM | MEDIUM | Watch and wait |
| 6 | Figma MCP for Dojo UI iteration | MEDIUM | MEDIUM | Low priority |
| 7 | NB2 inpainting for thumbnail editing | MEDIUM | LOW | Experiment when needed |
| 8 | Merch mockup pipeline | MEDIUM | HIGH | Future (post-1K subs) |

---

## Figma MCP + Claude Code

"Code to Canvas" integration launched Feb 17, 2026:
- Claude Code captures a rendered UI and converts it into editable Figma frames
- The Dojo dashboard (React + Tailwind) could be round-tripped through Figma for design iteration
- Most useful when planning major UI overhauls, not incremental changes

---

## Limitations

1. **Figma Weave is NOT in Figma yet** — the most important caveat. Standalone product only.
2. **Buzz uses gpt-image-1, not NB2** — for AI quality, use our direct NB2 API
3. **Headless Linux constraints persist** — Figma plugins, figma-use CLI, Figma Make all need GUI/browser. REST API remains export-only.
4. **NB2 vs Pro for photorealism** — NB2 has "slightly artificial quality" in some comparisons. Fine for stylized art, may not suffice for product photography.
5. **Figma Buzz is browser-based** — manual tool, not an API. Cannot automate in our Python pipeline.

**What this does NOT replace:** Kling Avatar video gen, FFmpeg compositing, Dojo pipeline orchestration, ElevenLabs TTS. These tools supplement, not replace.

---

## Bottom Line

The NB2 model swap (already done) is the biggest concrete win — 50% cost savings. Figma Buzz thumbnail templates are the next most practical move. Everything else is "watch and wait," especially Figma Weave which looks exciting but isn't integrated yet.
