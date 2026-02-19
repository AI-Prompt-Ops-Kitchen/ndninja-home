---
name: workflow-insights
domain: Meta/Workflow
level: mangekyo
description: Auto-synthesized weekly insights from Claude Code chat history. Living document.
last_updated: 2026-02-19
auto_generated: true
---

# Workflow Insights — Living Digest

*Auto-updated weekly by Sharingan chat digest. Each section = one week of sessions.*

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
