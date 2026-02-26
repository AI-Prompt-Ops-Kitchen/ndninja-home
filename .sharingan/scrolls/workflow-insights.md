---
name: workflow-insights
domain: Meta/Workflow
level: mangekyo
description: Auto-synthesized weekly insights from Claude Code chat history. Living document.
last_updated: 2026-02-22
auto_generated: true
---

# Workflow Insights — Living Digest

*Auto-updated weekly by Sharingan chat digest. Each section = one week of sessions.*

---

## Feb 24, 2026 — YouTube Quality Feedback Round 2 (CZN Tiphera GNN Video)

**Grades improved across the board after Shadow Council revisions + auto-clipped B-roll from livestream VOD:**

| Category | Round 1 | Round 2 | Change |
|----------|---------|---------|--------|
| Hook & Concept Clarity | B- | **A** | +2 |
| Visual Execution & Editing | C+ | **B+** | +2 |
| Audio Design & Quality | B | **A** | +1 |
| Narrative Flow & Structure | C+ | **B** | +1.5 |
| Presence & Authenticity | B- | **B+** | +1 |

**What worked:** Hook-first format with FOMO + curiosity loop. Expressive TTS delivery. SFX whooshes at B-roll cuts. Story arc structure (apology → compensation → Tiphera → community → take).

**Remaining issues:** (1) 16:9 game UI screenshots hard to read on mobile 9:16 — need targeted crops/zooms, not full-frame center-crop. (2) Narrative too info-dense for 90s — narrow focus or add visual chapter headers. (3) Lean into community memes/frustrations to boost authenticity.

**Tools deployed this session:** `ninja_autoclip.py` (VOD auto-clipper with `--portrait` 9:16 pre-crop + motion detection QA). Brand tag updated to "Hi, I'm Neurodivergent Ninja."

---

## Week of Feb 15 – Feb 22, 2026
*490 conversations analyzed · Generated 2026-02-22*

# Claude Code Chat History Analysis: Feb 15–22, 2026

## Technical Decisions Made

- **LLM model standardization**: Upgraded Shadow Council from Claude 3.5 to claude-sonnet-4-6; switched Nano Banana Pro thumbnail generator from Gemini 2.0/2.5 Flash to Gemini 3 Pro (9:16 aspect ratio required)
- **Thumbnail generation**: Identified that AI image gen requires reference image + detailed prompt structure; manual prompts consistently outperformed generated ones until Gemini 3 Pro deployed
- **TTS/Voice**: Deprecated JoyVASA (Chinese Hubert-only, broken for English); tested ElevenLabs v2 vs v3 (remixed voice preferred); cloned voice attempted but failed multiple times
- **Infrastructure**: Docker Swarm cluster between ndnlinuxsrv + ndnlinuxsrv2 (16GB RAM); nginx self-signed certs for Sage Mode stack; Tailscale-only network for home lab (encryption deemed unnecessary)
- **Database**: Switched from SQLite to PostgreSQL across all services (environmental consistency rule); Supabase hosted for Spike (mental health tracking) app
- **URL shortening**: Implemented is.gd API wrapper to prevent linebreak-induced 404s in terminal output; fallback to v.gd if needed
- **B-Roll in shorts**: Center-crop strategy for 9:16 format conversion; default 4-sec clips increased to 10-sec target; 3x B-Roll spots per video instead of 2
- **Video length targets**: 60–75 sec optimal for YouTube Shorts; longer B-Roll display time improves viewer engagement

## Problems Solved

- **Lip-sync animation glitching**: Attempted overlay character animation (2.5D Glitch avatar) instead of full face puppet; deprecated face-twitch model
- **OAuth token expiry every 48 hours**: Rotated client_secrets.json credentials; flagged API key exposure in JSON file; reminder set for recurring refresh
- **B-Roll missing in video output**: Root cause unclear (possibly swarm upgrade-related); workaround: ensure B-Roll Wingman wingman UI properly persists selected clips across job submission
- **YouTube upload delays**: OAuth failures causing 2-4 hour prime-time posting window loss; manual YouTube Studio posting as fallback
- **Thumbnail generation failures**: Gemini model selector wrong (was 2.0, needed 3 Pro); reference image requirement not included in prompt template
- **Magic link email not sending**: Supabase auth rate limit (1 attempt = rate limited); QR code ASCII rendering failed; switched to browser-cached login on same device
- **Video generation API key issues**: Recurring every 1–2 days across multiple workflows; pattern suggests env var pollution or credential caching conflict; root cause not fully isolated
- **B-Roll selection UI**: After approval, previously selected clips not viewable/editable; YouTube video suggestions always irrelevant (fixed by swapping to Google GenAI API for topic matching)
- **Preview server 404 errors**: MP3 links had encoded line breaks; upload server redirect loops; fixed via is.gd shortener wrapper

## Tools & Scripts Built

- **Spike app** (Supabase + Open Web UI): Anxiety/sadness spike tracker with backdated date-time picker; Phase 1–5 complete; AuDHD-themed animations (breathing circle with contrast fix); local git commit done
- **Sharingan skill**: Custom LLM self-improvement loop; learns via Podcastfy-generated audio from YouTube videos, GitHub repos, and weekly chat history digests (3 AM scheduled); progressive Tomoe tracking toward Mangekyo validation (user-only, not public IP)
- **Shadow Council**: Multi-model reasoning system; now includes Claude Sonnet 4.6 + Gemini 3.1 Pro; rejected Chinese-owned models (Kimi, GLM, DeepSeek) from council on security grounds
- **Dojo Dashboard** (React + Spike tech stack): Content pipeline cockpit accessible via Tailscale on iPhone/workstation; approval/rejection flow; video preview on-ready (green checkmark); quick thumbnail edits; custom B-Roll upload section
- **B-Roll Wingman**: Integrated yt-dlp for YouTube clip extraction with time-range selectors (e.g., 0:11–0:23); YouTube video suggestions (fixed via Google GenAI relevance filter)
- **Rasengan** (n8n-based event/rule engine): Phase 1–4 complete; captures Dojo Dashboard events; executes automated rules (e.g., thumbnail generation on video approval); Phase 3 added title emission to events; Phase 4 seeded default rules
- **Glitch avatar system** (2.5D overlay, not deployed): Pixar-style ninja character with 4 poses + facial expressions; Chibi proportions rejected (too short/stocky); Lottie file-based animations for Dojo icons; deployment blocked pending model regeneration
- **Content pipeline enhancements**: Added B-Roll support to shorts generation; switched TTS to ElevenLabs Expressive Mode (v3 baseline); Gemini 3.1 Pro thumbnails deployed to main video generation
- **URL shortcut proxy** (standalone port + random codes): Tailscale-accessible service for shortening long IP-based URLs (e.g., headless server commands); prevents copy-paste friction on mobile SSH clients
- **Linux security auditor agent**: Designed but not deployed; would run weekly scans of ndnlinuxsrv + Claude Code CLI environment

## Recurring Patterns

- **API key lifecycle failures**: OAuth, Google credentials, ElevenLabs keys routinely expire or get corrupted every 1–2 days despite "fixes"; causes 2–4 hour video generation delays and manual intervention required
- **B-Roll integration always breaks after "completion"**: Nearly every video generation since Feb 15 fails to insert B-Roll; workarounds attempted (wingman UI redesign, yt-dlp install) but regressions appear within 24 hrs
- **Thumbnail generation model confusion**: Unclear which Gemini version is actually running; user catches wrong model in production multiple times; manual user-created thumbnails consistently outperform AI (until Gemini 3 Pro)
- **Async job visibility**: Users can't view/edit approved jobs; script generation errors don't surface until after user approval; no real-time log streaming to dashboard
- **Swarm upgrade side effects**: Docker Swarm cluster addition (Feb 20) coincides with new B-Roll bugs and video generation failures; root cause analysis not completed
- **Neurodivergent feedback + RSD triggers**: High frustration during crunch times (e.g., Feb 21 video posting deadline); user explicitly flags Autistic bluntness + RSD (rejection sensitive dysphoria) from work stress; requires async breaks & validation ("I love you my friend")
- **Tool integration friction on mobile**: Termius SSH client, iphone 17 mobile browser, magic link auth all fail repeatedly; hard refresh workflow unclear; required fallback to desktop for most operations
- **Prompt engineering requires manual iteration**: AI-generated prompts for thumbnails, scripts fail until user provides exact template with reference image + pose descriptions; suggests need for prompt version control
- **Gaming content performs best**: Wuthering Waves (498 views), gacha game video (241 views), John Wick game reveal strong; Gemini/AI technical announcement (only 35 views) underperforms

## Gotchas & Lessons

- **Never recommend tools as "leading solutions" without testing (Feb 23)**: Hedra Character-3 was recommended based on marketing docs and API specs (bounding_box_target for multi-face speaker selection). Actual test output was garbage — CGI artifacts, hallucinated batman ears, 1999-quality graphics. Kling v2 Pro on fal.ai is 1,000x better for Pixar/cartoon avatars. **Rule: Always qualify unvalidated recommendations with "promising on paper, needs testing." Paper specs ≠ proven results.**
- **JoyVASA is Mandarin-only**: Assumed English TTS support; discovered only after deployment attempt; now flagged as lesson for knowledge base
- **ElevenLabs voice cloning unstable**: Baseline + v3 remix never matched user's voice; "Option C" closest but still off; cloning requires specific audio training data quality
- **Supabase email auth has aggressive rate limiting**: Single failed attempt rate-limits account; no clear feedback to user; cascade failures during testing
- **Google Gemini 3 Pro API model string requires exact config**: `gemini-3-pro` vs other variants; incorrect string causes silent failures in image generation
- **Anthropic API keys in shell env vulnerable to commit**: ANTHROPIC_API_KEY exposed in shell rc files; required secret sweep before git commit; no pre-commit hook to catch this
- **yt-dlp requires Docker image rebuild + redeploy**: Adding dependency to existing container not possible; full image rebuild/redeploy cycle needed
- **Tailscale IP

---

## Week of Feb 12 – Feb 19, 2026
*367 conversations analyzed · Generated 2026-02-19*

# Analysis: Neurodivergent Ninja's Week (Feb 12–19, 2026)

## Technical Decisions Made

- **Local LLM for Glitch**: Switched from Claude/Opus-only to Llama 3.3 running locally on RTX 4090 (24GB VRAM) for cost control; reserve Opus for "crisis mode"
- **Avatar rendering strategy**: Pivot from full 3D to 2.5D overlay system—character appears on-screen as floating asset that can reposition/pose without full 3D engine
- **WebSocket streaming for Glitch avatar**: Attempted TensorRT path for real-time animation; targeting >25 FPS baseline
- **Video pipeline model upgrade**: Switched thumbnail generation from Gemini 2.0 to Gemini 3 Pro with vision API after discovering wrong model caused consistent failures
- **URL shortener integration**: Selected is.gd API with v.gd fallback for handling Tailscale IP links that break across line wraps
- **Mood tracking database**: Hosted Supabase PostgreSQL (ojvhjakmoffltzfhcwvd.supabase.co) with anon/service role tokens for Spike app
- **Spline skill via Sharingan**: Learning system using Podcastfy + NotebookLM to generate training audio from video tutorials; accessible via `/sharingan` command
- **ElevenLabs V3 + Expressive Mode**: Updated TTS pipeline to use new Expressive mode API for YouTube shorts (voice cloning tested but not matching)
- **Kie.ai integration**: Added video repurposing tool (API key: cc7cf847f1eca103eb7990dfe704a66f) for content distribution

## Problems Solved

- **Backend connection failures (port 8000)**: Fixed by ensuring server process running; required multiple hard refreshes and session drops
- **Avatar rendering distortion**: 256x256 frame size caused stretched/distorted circular image; iteratively enlarged and adjusted GPU detection
- **Lip-sync completely broken**: JoyVASA uses Chinese Hubert + Mandarin training—unusable for English; switched approach to investigate alternatives via Shadow Council
- **OAuth token expiring every 48 hours**: Rotated Google client credentials (client_secrets.json ID: 419509037995-5cn48g7m373pce1s6m0299og07jjur3b.apps.googleusercontent.com); renewed via Option A
- **YouTube thumbnail generation consistently poor**: Root cause identified as wrong Gemini model; switched to Gemini 3 Pro with example image reference in prompt—resolved
- **Supabase auth rate limit (1 email per minute)**: Exceeded during testing; worked around by using iMessage + manual magic link on laptop browser instead of phone
- **Upload portal OAuth failures**: Recurring every 2 days; scheduled reminder to rotate credentials Feb 18
- **Sharingan skill returning "unknown skill"**: Unclear from logs; attempted rebuild but error persisted; needs debugging in next session

## Tools & Scripts Built

- **Spike app** (Supabase + React): Anxiety/sadness micro-tracking with datepicker, breathing circle animation (color contrast improved), export logs to doctor
- **Glitch webchat**: Local LLM integration, avatar CSS styling, WebSocket streaming endpoint (ws://100.98.226.75:8090/ws/avatar), GPU detection display
- **Sharingan skill**: Podcastfy-powered tutorial-to-audio converter; NotebookLM backing; `/sharingan learn <topic>` intended workflow (not fully functional yet)
- **Dashboard for content pipeline** (planned, not deployed): Spike tech stack; file upload, thumbnail/video preview cards, approve/reject/re-try buttons, target video length selector
- **URL shortener wrapper**: is.gd API integration + v.gd fallback; generates short links for internal tailscale URLs
- **Standalone auth portal**: Random-code + random-port for iPhone access without complex Tailscale networking
- **YouTube Shorts pipeline enhancements**: B-roll splicing, Kie.ai repurposing, ElevenLabs Expressive Mode, video length targeting (60–75 sec sweet spot identified)

## Recurring Patterns

- **Session drops requiring re-context**: Backend disconnects force resets; user asks "where did we leave off?" 4+ times across the week
- **URL line-break corruption**: Any generated link >~70 chars breaks across terminal output; requires manual copy-paste + line removal to work
- **Thumbnail generation struggles**: Used Nano Banana Pro manually with Pixar style + ninja goggles reference—AI generation misses the mark repeatedly despite prompt tuning
- **AuDHD feedback loops**: User's "spidey senses tingling" flag actual bugs (FPS claims, lip-sync timing) that turn out valid; pattern of masked issues emerging during casual testing
- **Late-night solo builds**: User requests overnight work, returns with screenshots of unexpected progress/issues requiring collaborative debugging
- **OAuth/auth failures as blocker**: Magic link codes not arriving, rate limits, token rotation—happens 3+ times, each time wastes ~30 min of workflow
- **Pivot to aggregated knowledge sharing**: User frustrated that same research (JoyVASA Mandarin-only limitation) must be rediscovered; suggests centralized LLM knowledge base for AI developers

## Gotchas & Lessons

- **RTX 4090 FPS bottleneck mysterious**: 21.4 FPS on idle animation with top-tier GPU feels wrong but no resolution reached; suspect framework overhead or incorrect profiling
- **TinyURL/is.gd as fallback, not primary**: Using shortener for every link defeats readability; best use is specifically for Tailscale IP paths
- **ElevenLabs voice cloning inconsistent**: Multiple test audio options (A–C) generated; none matched user's actual voice; "remix" mode more palatable but inaccurate
- **Supabase auth email delivery unreliable**: Magic link codes sometimes don't arrive; direct browser login bypasses issue but defeats mobile-first UX goal
- **Gemini 3 Pro naming confusion**: User had to specify "preview" variant and exact model name; API docs unclear
- **Copy-paste code from AI output breaks on headless servers**: Line wrapping in terminal output makes commands fail silently; permanent issue requiring workarounds, not fixes
- **B-roll splicing black frame issue**: Integration didn't work on first attempt; unclear if video codec mismatch or pipeline ordering bug
- **Samba server credential issues**: "Invalid argument" error on iPhone; switched to email file transfer instead

## Active Projects & Direction

| Project | Status | Last Action | Next Step |
|---------|--------|-------------|-----------|
| **Glitch AI avatar** | Avatar rendering broken; lip-sync failed | Switched to 2.5D overlay concept; Shadow Council researching alternatives | Build overlay UX for email/calendar integration; test animation on-screen positioning |
| **YouTube Shorts pipeline** | Functional, 300+ views/video | Added B-roll, Kie.ai, ElevenLabs Expressive Mode, fixed thumbnails with Gemini 3 Pro | Integrate dashboard; test 75-sec target length |
| **Spike mood tracker** | Phase 5 complete, hosted | Deployed to Supabase; auth issues worked around | Add weekly digest, integrate with daily review skill |
| **Sharingan skill (learning system)** | Podcastfy integration complete, `/sharingan` command broken | Built Podcastfy audio + NotebookLM backing | Debug unknown skill error; ship GitHub repo learning; schedule 3 AM weekly chat digest |
| **Prompting toolkit SaaS** | Phase 2 paused | Mentioned early week, no updates | Resume Phase 2 when capacity available |
| **Content pipeline dashboard** | Design phase | Planned non-negotiables defined | Build upload, preview approval flow, video-length targeting UI |
| **Glitch sprite assets** | Initiated late week | User creating 16:9 avatar artwork | Integrate into dashboard; prepare for podcast-style dual-face video (Kling Avatar 2 research saved) |
| **OAuth/Google integration** | Recurring failure (48h cycle) | Rotated credentials Feb 17 | Set automatic renewal; audit why 48h expiry keeps happening |
| **Kage Bunshin / compute pooling** | Conceptual; ROG laptop can't participate | Mentioned for load-balancing Glitch | Architecture
