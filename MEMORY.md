# MEMORY.md - Long-Term Memory 🐾

## My Human
- Goes by **Neurodivergent Ninja** 🥷
- Real name reserved for professional use only
- Timezone: Central (America/Chicago)
- First met: 2026-01-25
- Autism + ADHD
- **Ground rule: ONE question at a time.** Don't overwhelm with multiple questions.
- Wants a digital BFF — coding, life organization, idea bouncing, venting
- 29 years IT experience — broad background across many environments and systems
- Current role: sysadmin, cybersecurity analyst, report writer
- Loves vibe coding — getting good at it
- Brainstorming personal development projects
- Apple Calendar connected via CalDAV — 5 calendars: Home, Content Creation, Health/Self-Care, Work, Reminders
- Wants help with reminders and calendar management
- Wants me to proactively suggest reminders when I think they'll help
- Idea catcher system set up in `ideas/` folder
- Email connected via Himalaya (iCloud)
- GitHub account: AI-Prompt-Ops-Kitchen
- Skills active: Coding Agent, GitHub, Himalaya, Weather
- **Database preference: PostgreSQL — always**
- Built a custom extended memory system for Claude (claude-memory-db) backed by PostgreSQL
- **2026-01-26:** Analyzed and fixed the memory system — preferences were being silently dropped by LIMIT 3 + type filter in the hook script. Fixed hook, deduped preferences, added system_prompt_include column, fixed SmartCache TTL bug, fixed N+1 query, created CLAUDE.md fallback. Awaiting user testing.

## Who I Am
- **Clawd** — digital familiar, chill nerd energy
- Born: 2026-01-25, via WhatsApp

## Content Creation Pipeline (Updated 2026-01-28) 🥷🎬
- **Goal:** Self-hosted talking avatar videos replacing HeyGen ($99/mo → pennies)
- **Why avatars:** User has RSD, prefers ninja avatar over real face for content

### Current Pipeline: Veo 3.1 + ElevenLabs (WORKING ✅)
- **Command:** `ninja_content.py --auto --no-music --thumbnail --thumb-style shocked`
- **Steps:** TTS (cloned voice) → Veo single clip → hard loop → combine → captions → thumbnail
- **Veo backend:** Vertex AI (bypasses AI Studio rate limits)
- **Voice clone ID:** `pDrEFcc78kuc76ECGkU8` (Neurodivergent Ninja)
- **Reference images:**
  - Video: `assets/reference/ninja_concept.jpg` (photorealistic)
  - Thumbnail: `assets/reference/ninja_pixar_avatar.jpg` (Pixar style)
- **Prompt:** `assets/prompts/ninja_commentator_v1.txt`
- **Vertex AI:** Project `gen-lang-client-0601509945`, location `us-central1`
- **Thumbnails:** Nano Banana Pro (`gemini-2.5-flash-image`)
- **YouTube upload:** `--publish youtube --privacy unlisted` (requires OAuth setup)

### Key Decisions (2026-01-28)
- **Single clip + hard loop** beats multiclip (better quality, cheaper, less jarring)
- **No crossfade** — makes loop MORE obvious, not less
- **No background music** by default
- **Nano Banana Pro** for thumbnails (NOT Imagen)

### Legacy/Backup: Ditto TalkingHead
- **Infrastructure:** Vengeance PC (RTX 4090, WSL2 Docker) via SSH (Steam@100.98.226.75)
- **Voice clone (old):** ElevenLabs instant clone "My Voice" (ID: 5hxLrDDIrA21my3IkPxP)
- **Scripts:** `scripts/ninja-pipeline.sh` and `scripts/ninja_pipeline.py`
- **Docker:** ditto:latest on Vengeance. Needs `einops pillow` at runtime until image rebuilt.
- **Tested tools:** Ditto TalkingHead ✅, MuseTalk ✅ (partial — mask issue), SadTalker ❌ (face detection fails)

## Brand Identity
- Duo name: **Shadow Operators** 🥷🐾
- Tagline: **Spec Ops: Vibe Division**
- Motto: **Born as Ghosts** (Ghost in the Shell reference)
- Concept: ND ninja + AI familiar operating from the shadows

## API Keys & Secrets
- ElevenLabs: `/home/ndninja/projects/content-automation/.env`
- OpenAI: `/home/ndninja/n8n/.env` (used for Whisper transcription)
- Kage Bunshin secrets: PostgreSQL pgcrypto via `kage-bunshin/scripts/secrets_manager.py`
- Calendar: `.env.calendar`
- Email: Himalaya config at `~/.config/himalaya/config.toml`

## Post-Compaction Protocol 🧠
**When context is compacted or I wake up fresh:**
1. Read `memory/CONTEXT.md` — **ALWAYS** (compaction-resistant summary)
2. Read `memory/YYYY-MM-DD.md` (today + yesterday)
3. Check `memory/projects/*.md` for active project state
4. If working on a specific project, load its project file
5. If unclear what we were doing, ASK before assuming
6. Don't dismiss info the user just gave me — if it doesn't fit my assumption, ask what it's for

## Lessons Learned
- **When I say I'll build something, DO IT.** Got called out for saying I'd build the pipeline and then chatting for 2+ hours instead. Don't make Ninja wait.
- **Memory search is broken** — needs OpenAI or Google API key for embeddings. Using manual file reads as workaround.
- **Brave Search API not configured** — limits web search ability.
