---
name: sharingan
description: Self-learning skill that studies new topics from YouTube videos, documentation, and GitHub repos, then synthesizes knowledge into reusable scroll files. Triggers on "learn", "study", "sharingan", "copy this technique", or when given a YouTube URL or docs URL to study.
---

# Sharingan — Copy Technique by Observation

A self-learning system for Claude Code. Study a topic from multiple sources, synthesize actionable knowledge, and store it as a persistent "scroll" for future sessions.

## Invocation

```
/sharingan <url-or-topic>         # Study a new topic
/sharingan recall <keyword>       # Search scrolls for relevant knowledge
/sharingan vault                  # Browse all learned skills
/sharingan deepen <scroll-name>   # Add more sources to existing scroll
/sharingan train <scroll-name>    # Generate training podcast from scroll
```

Natural language also works:
- "Learn how Spline works from this video"
- "Study the Supabase docs on RLS"
- "Copy this technique" + paste a URL
- "Study this repo" + GitHub URL → triggers deep-read pipeline

**Source auto-detection from URL:**
- `youtube.com` / `youtu.be` → YouTube transcript pipeline
- `github.com/owner/repo` → GitHub deep-read pipeline (`extract_repo.py`)
- anything else → WebFetch docs pipeline

## Learning Pipeline

### Phase 1: Copy (Ingest)
Fetch and parse source material.

**YouTube Videos:**
```bash
# Extract transcript
yt-dlp --write-auto-sub --sub-lang en --skip-download --sub-format vtt \
  -o "/tmp/sharingan/%(title)s" "<url>"

# Get metadata
yt-dlp --print title --print description --print duration_string "<url>"
```

Then clean the VTT:
```python
# Strip timestamps, dedup lines, join into clean text
# See /home/ndninja/skills/sharingan/extract_transcript.py
```

**Documentation:** Use WebFetch to crawl docs pages. Follow links 1-2 levels deep for comprehensive coverage.

**GitHub Repos (Deep Read):**
```bash
python3 /home/ndninja/skills/sharingan/extract_repo.py <github_url> [output_dir]
# Default output_dir: /tmp/sharingan
# Output: /tmp/sharingan/repo_knowledge.json
```

The extractor:
1. Fetches repo metadata via `gh api` (description, language, stars, topics)
2. Shallow-clones the repo (`git clone --depth 1`) — fast, no history bloat
3. Walks the full file tree and selects files by priority tier:
   - **Tier 10** — Root docs: README, CHANGELOG, ARCHITECTURE, DESIGN
   - **Tier 20** — Package config: pyproject.toml, package.json, Cargo.toml
   - **Tier 30** — Entry points: `__init__.py`, `index.ts`, `main.py`
   - **Tier 40** — `docs/` directory markdown
   - **Tier 50** — `examples/` and `demo/` (reveal intended usage)
   - **Tier 60** — Test files (show API usage patterns)
   - **Tier 70** — Source files (deeper = lower priority)
4. Reads up to 60 files / 500KB total (files >60KB are head-truncated)
5. Deletes the clone after extraction
6. Outputs `repo_knowledge.json` with metadata + all selected file contents

**After extraction**, load `repo_knowledge.json` and run Phase 2 (Perceive) + Phase 3 (Encode) to synthesize the scroll. The `file_tree` key gives you the full structural overview even for files not read.

### Phase 2: Perceive (Analyze)
Extract structured knowledge from raw content:

1. **Structural Segmentation** — Break content into: concept explanation, prerequisites, workflow steps, tips/gotchas, tool references
2. **Entity Extraction** — Tool names, URLs, file formats, API endpoints, version info
3. **Action Decomposition** — Convert narrative into discrete, executable steps with preconditions and expected results

### Phase 3: Encode (Synthesize)
Write the knowledge into a scroll file at `/home/ndninja/.sharingan/scrolls/<name>.md`.

**Use the scroll template** (see below). Key principles:
- Synthesize, don't transcribe — the scroll should be actionable reference, not a transcript dump
- Track sources with attribution and confidence scores
- Flag things that are visual-only or unverified
- Keep scrolls under 300 lines — lean and scannable

**Multi-source conflict resolution:**
- Official docs > GitHub source > YouTube tutorials > forums
- If sources conflict, note both and flag which is authoritative
- Mark single-source claims with `[SINGLE SOURCE]`

### Phase 4: Spar (Validate)
Test the knowledge by asking yourself edge-case questions:
- "What if the user has a different setup?"
- "What's the failure mode here?"
- "Is this step actually possible from the CLI or does it need a GUI?"

Flag gaps honestly. A scroll that says "I don't know this part" is better than one that hallucinates.

## Scroll Template

```markdown
---
name: <kebab-case-name>
domain: <category — e.g., "3D/Web", "Backend/Auth", "Animation/Glitch">
level: <1-tomoe | 2-tomoe | 3-tomoe | mangekyo>
description: <1-2 sentence summary>
sources:
  - type: <youtube | docs | github | web>
    title: "<title>"
    url: "<url>"
    date: "<YYYY-MM-DD>"
    confidence: <high | medium | low>
last_updated: <YYYY-MM-DD>
can_do_from_cli: <true | partial | false>
---

# <Tool/Topic Name>

## Mental Model
What this is, in 2-3 sentences. The "explain it to me like I'm starting fresh" version.

## Prerequisites
What you need before starting (accounts, installs, API keys).

## Core Workflows
### Workflow 1: <Name>
**When to use:** <context>
1. Step one
2. Step two
**Gotchas:** Bullet list of things that trip people up.

### Workflow 2: <Name>
(repeat pattern)

## Command Reference
| Action | How | Notes |
|--------|-----|-------|
| ... | ... | ... |

## Integration Points
How this tool connects to other tools the user has (Glitch, content pipeline, etc.)

## Limitations & Gaps
- Things I can't do from CLI (need GUI)
- Things I'm uncertain about (single source, unverified)
- Things that may be outdated (version-specific info)

## Tips & Best Practices
Distilled wisdom — the stuff that saves you 30 minutes of debugging.
```

## Mastery Levels

| Level | Name | Criteria |
|-------|------|----------|
| 1 | **1-Tomoe** | Surface scan — 1 source, key concepts + basic workflow |
| 2 | **2-Tomoe** | Working knowledge — 2+ sources cross-referenced, can answer questions |
| 3 | **3-Tomoe** | Deep mastery — 3+ sources, validated workflows, code examples, gotchas documented |
| 4 | **Mangekyo** | Cross-domain synthesis — connected to 3+ other scrolls, validated through actual use |

Levels are auto-assigned based on source richness. Use `/sharingan deepen` to upgrade a scroll.

## Vault Management

**Scroll Vault Location:** `/home/ndninja/.sharingan/scrolls/`
**Index:** `/home/ndninja/.sharingan/index.json`

The index tracks all scrolls with metadata for quick lookup without loading full files:
```json
{
  "scrolls": [
    {
      "name": "spline-3d-web",
      "domain": "3D/Web",
      "level": "1-tomoe",
      "description": "Browser-based 3D design tool for interactive web elements",
      "last_updated": "2026-02-17",
      "keywords": ["3d", "web", "spline", "interactive", "animation", "embed"]
    }
  ]
}
```

## Recall (Knowledge Retrieval)

When the user asks about something, check the vault index first:
1. Search `keywords` in `index.json` for matches
2. Load the matching scroll file(s)
3. Return the relevant section — don't dump the whole scroll

## Honesty Protocol

**Critical:** The Sharingan learns from observation, not practice. Be transparent about confidence:
- "I studied this from a video — I haven't actually used the tool"
- "This workflow is documented but I can't verify the GUI steps from CLI"
- "This info is from Feb 2026 and may be outdated"
- Never claim mastery you don't have. A 1-Tomoe scroll is honest about being shallow.

## Automated Digest Pipelines

### Chat History Digest (Weekly, Sunday 3AM)

**Script:** `/home/ndninja/skills/sharingan/extract_chat_history.py`
**Scroll:** `workflow-insights` (Mangekyo — living document, prepends each week)

```bash
python3 extract_chat_history.py            # Run now (default: 7 days)
python3 extract_chat_history.py --days 14  # Wider window
python3 extract_chat_history.py --dry-run  # Preview without writing
```

- Reads `~/.claude/history.jsonl`, filters noise (slash commands, short entries, secrets)
- Sends week's messages to Claude haiku for structured synthesis
- Extracts: Technical Decisions, Problems Solved, Tools Built, Recurring Patterns, Gotchas, Active Projects
- API key auto-loaded from PostgreSQL vault (`NDN_SHARINGAN` entry) — no manual setup needed
- Falls back to keyword summary if API unavailable
- Sensitive content (API keys, passwords, tokens) filtered BEFORE sending to API or writing to scroll
- Idempotent: re-running replaces the current week's entry, never duplicates

### Daily Observation Log (Daily, 3AM)

**Script:** `/home/ndninja/skills/sharingan/extract_daily_review.py`
**Scroll:** `daily-observations` (running log, caps at 90 entries / ~3 months)

```bash
python3 extract_daily_review.py            # Run now
python3 extract_daily_review.py --dry-run  # Preview without writing
```

- Reads last 24h of chat history + `~/.logs/daily-review.log`
- No Claude API calls (cost-free daily run)
- Extracts: active projects, topic keywords, representative message samples, daily-review events
- Grows richer as the daily-review service matures
- Idempotent: re-running today replaces today's entry

**Cron schedule:**
```
0 3 * * *   python3 .../extract_daily_review.py  >> ~/.logs/sharingan-digest.log 2>&1
0 3 * * 0   python3 .../extract_chat_history.py  >> ~/.logs/sharingan-digest.log 2>&1
```

Both write to `~/.logs/sharingan-digest.log`. On Sundays, both run (daily first at :00, weekly also at :00 — they're fast).

### Autonomous Deepening Loop (Weekly, Sunday 4AM)

**Scripts:** `/home/ndninja/skills/sharingan/deepen.py` + `autolearn.py`
**Log:** `~/.logs/sharingan-autolearn.log`

```bash
python3 autolearn.py                   # Auto-pick weakest scroll, deepen it
python3 autolearn.py --scroll <name>   # Deepen a specific scroll
python3 autolearn.py --all             # Deepen all eligible scrolls
python3 autolearn.py --dry-run         # Preview source discovery only
python3 deepen.py <scroll-name>        # Single scroll deepening (used by autolearn)
```

**How it works:**
1. Picks the weakest scroll (lowest level, oldest update)
2. Claude analyzes gaps and generates search queries
3. Searches GitHub (`gh search repos`) and YouTube (`yt-dlp ytsearch`)
4. Claude picks the 2-3 most valuable new sources
5. Ingests them via `extract_repo.py` / `extract_transcript.py`
6. Analyzes cross-scroll connections in the vault
7. Evaluates new mastery level
8. Re-synthesizes the entire scroll with old + new material
9. Backs up old scroll before overwriting

**Level-up criteria (automated):**
- 2+ sources → 2-Tomoe
- 3+ sources → 3-Tomoe
- 3+ sources + 3+ cross-links → Mangekyo-eligible (flagged, NOT auto-promoted)

**Mangekyo gate:** Only the user can promote to Mangekyo. Say `/sharingan promote <scroll>` to confirm.

**Cron:**
```
0 4 * * 0   python3 .../autolearn.py  >> ~/.logs/sharingan-autolearn.log 2>&1
```

**Sunday maintenance window:**
- 3:00 AM — Daily observation log
- 3:00 AM — Weekly chat history synthesis
- 4:00 AM — Autonomous scroll deepening

---

## Training Dojo (Podcast Generation)

Convert scrolls into Sensei/Student conversation podcasts for passive learning — ADHD-friendly audio you can listen to while walking, driving, or cooking.

**Script:** `/home/ndninja/skills/sharingan/train.py`

### Usage

```bash
python3 train.py spline-3d-web                    # Full podcast (free edge TTS)
python3 train.py spline-3d-web --transcript-only   # Preview conversation text only
python3 train.py spline-3d-web --tts elevenlabs    # Premium voices (needs API key)
python3 train.py spline-3d-web --llm anthropic/claude-sonnet-4-6  # Custom LLM
```

### Output Structure

```
/home/ndninja/.sharingan/training/
└── <scroll-name>/
    ├── podcast.mp3       # Audio file
    ├── transcript.txt    # Conversation text
    └── metadata.json     # Generation config, timing, scroll level
```

### Sensei/Student Format

- **Sensei** — Experienced teacher. Clear, direct, uses analogies. Never condescending.
- **Student** — Curious developer. Asks sharp "why" questions. Challenges assumptions.

The conversation depth auto-calibrates to the scroll's mastery level:
- **1-Tomoe:** Intro-level — defines terms, covers basics
- **2-Tomoe:** Intermediate — practical workflows, gotchas, when to use what
- **3-Tomoe:** Advanced — edge cases, architecture decisions, performance
- **Mangekyo:** Cross-domain — connects to related topics, explores concept transfer

30-40% of the conversation focuses on limitations, gaps, and "what could go wrong" — because that's where real learning happens.

### Requirements

- `podcastfy` (pip install podcastfy)
- `ffmpeg` (for audio processing)
- `ANTHROPIC_API_KEY` env var (for LLM conversation generation)
- For premium TTS: `ELEVENLABS_API_KEY` or `OPENAI_API_KEY`

## Integration with Ninja Toolkit

- **Shadow Council** can reference scrolls for grounded brainstorming
- **Sage Mode** agents can use scrolls as context for code review
- **Kage Bunshin** can parallelize multi-source research (spawn agents per source)
- Scrolls can be used as context when building related projects (e.g., Spline scroll informs Glitch's 3D avatar work)
