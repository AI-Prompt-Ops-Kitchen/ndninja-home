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
```

Natural language also works:
- "Learn how Spline works from this video"
- "Study the Supabase docs on RLS"
- "Copy this technique" + paste a URL

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

**GitHub Repos:** Clone or browse key files — README, src/ structure, examples/, API surface.

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

## Integration with Ninja Toolkit

- **Shadow Council** can reference scrolls for grounded brainstorming
- **Sage Mode** agents can use scrolls as context for code review
- **Kage Bunshin** can parallelize multi-source research (spawn agents per source)
- Scrolls can be used as context when building related projects (e.g., Spline scroll informs Glitch's 3D avatar work)
