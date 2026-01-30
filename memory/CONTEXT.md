# CONTEXT.md — Compaction-Resistant Summary
> Last updated: 2026-01-29 22:45 EST
> This file survives compaction. Keep under 50 lines.

## Active Projects

### 🥷 Ninja Content Pipeline [WORKING]
Automated YouTube/social video creation. See `memory/projects/ninja-content.md`
- Command: `ninja_content.py --auto --no-music --thumbnail`
- Uses: Veo 3.1 (Vertex AI), ElevenLabs, Nano Banana Pro
- Voice clone: `pDrEFcc78kuc76ECGkU8`

### 🛡️ Compaction Safety System [JUST COMPLETED]
All 3 tiers implemented:
- Tier 1: Visual health indicator, manual save, preview, confirmation, export
- Tier 2: Pin system, turn estimation, version history, language reframing
- Tier 3: Named checkpoints, two-tier memory (PINNED.md), restore points

## Recent Decisions (2026-01-29)
- Single clip + hard loop > multiclip (better quality, cheaper)
- Nano Banana Pro > Imagen for thumbnails
- Veo B-roll generator fixed (was Ken Burns, now real video)
- **Audio fix**: Keep original audio as WAV, strip from segments, re-attach cleanly
- **B-roll prompts**: All include "no text, no logos" to prevent gibberish
- **4 clips default** instead of 3 for better coverage
- **THE GOLDEN RULE**: If you CAN do it, you SHOULD do it. No delegation.

## Open Loops
- **Setting up remote access to user's RTX 4090** (need hostname/IP)
- Local B-roll scripts created: `ninja_broll_local.py`, `local_broll_setup.py`
- YouTube OAuth still needs user to run browser auth
- Awaiting v3 video feedback (audio distortion fix)

## User Communication Notes
- **ONE question at a time** (neurodivergent, multiple Qs overwhelming)
- Be resourceful before asking
- They hate re-explaining things
- When unsure, check memory files BEFORE asking
- **User felt understood** by neurodivergent insight — remember this matters

## Don't Forget
- **PINNED.md** = items that NEVER get compressed
- Use "archive" not "delete", "checkpoint" not "save point"
- Show what's preserved, don't just say "it's saved"
- **THE GOLDEN RULE**: If you CAN do it, DO it. No delegation.
