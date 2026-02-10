# PINNED.md — Protected Context (Never Compress)
> Items here are **immune to compaction**. They persist verbatim across all sessions.
> Add critical facts, preferences, and non-negotiables here.

## 🧠 User Profile (Permanent)
- **Name:** Neurodivergent Ninja 🥷
- **Neurodivergence:** Autism + ADHD
- **Ground Rule:** ONE question at a time — multiple questions are overwhelming
- **Communication:** Hates re-explaining things; check memory before asking
- **Timezone:** America/Chicago (Central)

## 🎯 Active Project: Ninja Content Pipeline
- **Command:** `ninja_content.py --auto --no-music --thumbnail`
- **Voice ID:** `aQspKon0UdKOuBZQQrEE` (Neurodivergent Ninja Remix)
- **TTS Model:** `eleven_v3` (works with remix, more natural flow)
- **Reference Image (video):** `assets/reference/ninja_helmet_v4_hires.jpg` (1568x2720)
- **Reference Image (thumbnail):** `assets/reference/ninja_helmet_v4_hires.jpg`
- **Vertex AI Project:** `gen-lang-client-0601509945`

### Video Generation Stack (2026-02-07) ✅ VERIFIED WORKING
1. **TTS:** Remix voice + eleven_v3 (no timestamps needed - skip captions)
2. **Avatar:** Kling Avatar v2 Standard via fal.ai
3. **Captions:** NONE - rely on YouTube/Instagram auto-captions

### ⚠️ CRITICAL: Image Resolution Requirements
- **MINIMUM:** 1024x1792 pixels
- **WhatsApp compresses images!** Always use HD mode or send as Document
- Low-res images cause Kling to hallucinate Chinese/foreign text

### Standard Intro
```
What's up my fellow ninjas!? This is Neurodivergent Ninja here and I'm back with another quick update video.
```

### Standard Outro
```
Thanks for watching my video! Please like, follow and subscribe to help this channel grow! This is Neurodivergent Ninja signing off. I'll see you in my next video!
```

### Pipeline Backup
- **Location:** `backups/pipeline_20260207_103704/`
- **Config Doc:** `PIPELINE_CONFIG.md`

## 🎨 NNNN Branding (Neurodivergent Ninja News Network)
- **Official Folder:** `assets/branding/nnnn_official/`
- **Logo (All Blue):** `logo_all_blue.png` - ocean/sapphire monochrome
- **Logo (Blue+White):** `logo_blue_white.png` - high contrast
- **YouTube Banner:** `banner_all_blue_*.png` or `banner_blue_white_*.png`
- **Watermark:** `watermark_*.png` (200x200)
- **Profile Pic:** `profile_*.png` (800x800)

## 🔒 Non-Negotiables
- **Database:** PostgreSQL always
- **Don't dismiss info** the user just gave — if it doesn't fit assumptions, ASK
- **Be resourceful** before asking questions
- **Actions > words** — when you say you'll build something, DO IT
- **THE GOLDEN RULE:** If you CAN do it, you SHOULD do it. No delegation when you have the tools.

## 🔐 API Key Security (CRITICAL - Added 2026-02-07)
- **NEVER hardcode API keys** in any file, even as "fallback defaults"
- **NEVER commit .env files** or files containing keys
- Always use `os.environ.get('KEY_NAME')` with NO default value
- Pre-commit hook installed (`.git/hooks/pre-commit`) scans for key patterns
- If you see a hardcoded key ANYWHERE → remove it IMMEDIATELY
- **Backup files are dangerous** — scrub them before committing
- Once a key is exposed on GitHub, it's burned FOREVER (Google auto-revokes)

## 🤖 AUTOMATION IS NON-NEGOTIABLE
Due to ADHD + Autism, manual steps = failure points:
- **No "open X and click Y"** — will forget or procrastinate
- **No multi-step manual processes** — overwhelming
- **Everything must run end-to-end automatically**
- **If it can't be fully automated, it's not a valid solution**
- This is a CORE DESIGN PRINCIPLE for all tools and workflows

## 🛠️ GSD (Get Shit Done) - Claude Code Framework
- **Installed:** `~/.claude/commands/GSD/`
- **Source:** https://github.com/OutcomefocusAi/GSD
- **Key Commands:**
  - `/gsd:new-project` - Initialize with questioning → research → requirements → roadmap
  - `/gsd:map-codebase` - Analyze existing codebase (brownfield)
  - `/gsd:plan-phase N` - Create detailed execution plan
  - `/gsd:execute-phase N` - Wave-based parallel execution
  - `/gsd:verify-work` - Conversational UAT
  - `/gsd:debug` - Systematic debugging with persistent state
  - `/gsd:progress` - Check status, route to next action
- **11 sub-agents:** planner, executor, verifier, roadmapper, researchers, debugger, codebase-mapper
- **Creates `.planning/` folder** with PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md

## 📌 Pinned Items
<!-- Add items below using: - [YYYY-MM-DD] Item description -->

- [2026-02-07] 🏠 **DREAM HOME PURCHASED!** $625k new construction, backs to pond, ~5 min from current home. Closing in 4-6 weeks.

