# Neurodivergent Ninja - Session Memory

## Major Projects → See `projects-index.md` for full list with locations

## Environment Rules
- **Database:** ALWAYS use PostgreSQL for consistency. Never introduce SQLite for new features.
- **Existing exception:** The Dojo's `jobs.db` is SQLite (legacy) — should be migrated to PostgreSQL eventually
- **PostgreSQL:** v17, user `postgres`, already running with `api_keys` database

## Paid API Rendering Rule (MANDATORY)
- **NEVER batch-generate paid renders (fal.ai, Kling, Runway, etc.) without explicit user approval**
- Always generate **1 test clip/image first**, send to Vengeance for review, and wait for user's signal before proceeding
- This applies to ANY paid per-second or per-image API: Kling Avatar, fal.ai FLUX, Runway, etc.
- Ask the user about quality settings (Pro vs Standard, ElevenLabs vs edge-tts, etc.) BEFORE rendering
- The user controls the "go" signal — never assume bulk generation is approved

## YouTube OAuth — FIXED (Feb 24, 2026)
- App is in **Production** mode (no more 7-day token expiry)
- Root cause was: **no scopes configured** in Google Cloud Console → added `youtube.upload`
- Token saved: `~/.config/youtube_uploader/token.json` (valid, has refresh token)
- Client ID: `419509037995-5cn48g7m373pce1s6m0299og07jjur3b`
- Upload script: `/home/ndninja/scripts/youtube/youtube_upload.py` (category 20=Gaming)
- `client_secrets.json` is NOT tracked by git (verified)

## Visual Style Rules
- **NO cyberpunk aesthetics** in thumbnails or visuals. User dislikes it. No neon cities, matrix code, green digital rain.
- **Ninja/dojo theme ALWAYS** — traditional Japanese: dojo, temple, bamboo, cherry blossoms, katana, paper lanterns, ink brush style, martial arts scrolls
- **Glitch voice:** Laura (premade, `FGY2WhTYpPnrIDTdsKH5`) — locked in Feb 26, 2026. Sassy/quirky, consistent.

## Content Creation - Script Structure (UPDATED Feb 24, 2026)

**Hook-first format** — no more leading with intro greeting. Structure:
1. HOOK (scroll-stopper, ~12 words) → 2. Brand tag ("Hi, I'm Neurodivergent Ninja.") → 3. Body (Fact→Implication→Reaction) → 4. Ninja's Take ("Here's what I actually think —") → 5. Community Hook (comment-driving question)

**Standard Outro:** "Stay sharp, stay dangerous. Catch you on the next one."
**Legacy Intro** (kept for dual-anchor only): "What's up my fellow Ninjas, this is Neurodivergent Ninja here back with another video."

**YouTube Feedback Grades (Feb 24, 2026 — CZN Tiphera video):**
| Category | Round 1 | Round 2 | Change |
|----------|---------|---------|--------|
| Hook & Concept | B- | **A** | +2 |
| Visual & Editing | C+ | **B+** | +2 |
| Audio Design | B | **A** | +1 |
| Narrative Flow | C+ | **B** | +1.5 |
| Presence & Auth | B- | **B+** | +1 |

**Remaining weak spot:** Visual — narrative still info-dense, consider visual chapter headers.
**UI crop mode SHIPPED (Feb 24, 2026):** Static 16:9 UI screenshots now get horizontal pan (left→right) instead of center-crop. Auto-detected via frame comparison in `_detect_crop_mode()`. Gameplay/cinematics keep standard center-crop. User approved pan approach over blurred-bg alternative.

**B-roll for Shorts (UPDATED Feb 24, 2026):** 4 × 10s = 40s (64% B-roll, 36% avatar). Old config was 3×4s=12s (19%) — way too little, clips too short. User approved after Varka v2 test. Defaults updated across CLI + Dojo pipeline + DB schema.
**Auto-Clipper:** `ninja_autoclip.py` — extracts B-roll from YouTube VODs with `--portrait` (9:16 pre-crop) + motion detection QA (catches still images/slides). Sharingan scroll: `youtube-auto-clipping.md`.
**SFX Layer:** DISABLED (Feb 26, 2026) — no other gacha channels use SFX, not worth the processing step. Code still exists in `add_sfx_layer()` but skip it in production.
**B-roll bug fixed:** `resolve_broll_clips()` was assigning same clip to all moments. Fixed with unique-assignment fallback + skip generic topic fuzzy matching.
**Burn-in captions:** DEFERRED — YouTube auto-captions working fine, past attempts had timing issues.

## The Dojo (Content Pipeline Dashboard)

- **Location:** `/home/ndninja/projects/ninja-dashboard/`
- **Port:** 8090 (replaces preview 8081 + upload 8082 after validation)
- **Stack:** FastAPI (backend/) + Vite + React 19 + Tailwind v4 (frontend/)
- **Run prod:** `bash /home/ndninja/projects/ninja-dashboard/run.sh` (builds then serves on 8090)
- **Run dev:** `bash /home/ndninja/projects/ninja-dashboard/dev.sh` (FastAPI 8090 + Vite 5173)
- **DB:** PostgreSQL `dojo` database (`dojo_user`). The `backend/jobs.db` SQLite file is a leftover artifact — not used.
- **Features:** Script Workshop (article→script→video), Review Queue (byte-range video, approve/discard/retry), Jobs Panel (WS live status), Upload Zone
- **Video length selector:** 30s/60s/90s/120s presets + custom slider (target_length_sec in job schema)
- **Key note:** `--workers 1` MANDATORY (WS broadcast correctness)

## Content Pipeline Configuration

- **Current Avatar (OG):** `/home/ndninja/assets/reference/ninja_helmet_v4_hires.jpg`
- **NEW Design (testing):** `/home/ndninja/uploads/IMG_2411.jpeg` — desk presenter ninja, expressive face. See `new-character-design.md` for full details.
- **New design proven config:** Kling v2 **Pro** + ElevenLabs v3 + expressiveness prompt (eyes blink/emote). User approved Feb 22, 2026.
- **Thumbnail Reference:** `/home/ndninja/assets/reference/ninja_helmet_v3_futuristic.jpg`
- **Target Length:** ~60 seconds for YouTube Shorts (~130 words)
- **Kling Avatar Model:** Standard for OG avatar, **Pro for new design** (expressiveness requires it)
- **Captions:** YouTube auto-generated (not burned in)
- **YouTube Caption Color:** Light blue (user preference, set viewer-side)
- **Long-form Script:** `/home/ndninja/scripts/ninja_longform.py` (multi-segment avatar + B-roll assembly)
- **Thumbnail Workflow:** Nano Banana Pro 2 generates Pixar ninja → PIL composites text overlays
- **Ninja Thumbnail Style:** MUST have digital goggles (like shorts avatar). Fun Pixar poses, cute/excited expressions.
- **16:9 Avatar Artwork:** Needed for future long-form videos (user will provide)

## Dual-Anchor Format — BLUE OCEAN (UPDATED Feb 24, 2026)

**Nobody else on YouTube is doing this.** Two Pixar-style animated co-anchors (Ninja + Glitch) covering gaming news.
- **NEW: Video Chat format (Feb 24, 2026):** Wife's idea — FaceTime-style vertical stack instead of news desk. Eliminates seam problem entirely. Shadow Council rated A-tier. VALIDATED.
- **Ghost mouthing SOLVED:** 60Hz sine wave at -60dB for listener audio. 4 iterations: silent→mouthing, anti-prompts→jitter, pink noise→almost, **60Hz sine→CLEAN**
- **Winning config:** Speaker=Pro+TTS, Listener=Standard+60Hz+anti-mouth prompts+CFG 0.9
- **Format:** `--format videochat` (default) or `--format newsdesk` (legacy)
- **Key tech:** Kling Avatar v2 (Pro speaker / Standard listener) + 60Hz tone + vstack + PNG overlay
- **Cost:** ~$0.085/s (~$5.13 for 60s Short) with pre-rendered listener loops. Was $0.171/s before loops.
- **Pre-rendered listener loops (Feb 26, 2026):** `assets/listener_loops/` — eliminates 50% of Kling renders. One-time $3.36 cost, reused forever.
  - `ninja_idle_primary.mp4` — slight head tilt, natural "wow" moment (v2 pick)
  - `glitch_idle_shrug.mp4` — cute side head move (v1 pick)
  - `glitch_idle_nod.mp4` — nods in agreement (v2 pick). Alternate shrug/nod for variety.
- **Assets:** `assets/overlays/` — videochat_ref_ninja.png, Glitch_Facetime_Design.png, overlay PNGs
- **Glitch ref:** User-designed `Glitch_Facetime_Design.png` (hacker den webcam shot)
- **Ninja ref:** Nano Banana Pro 2 generated from new desk presenter design (IMG_2411.jpeg)
- **Glitch voice:** Laura (placeholder), custom voice TBD
- **Sharingan scrolls:** `videochat-dual-anchor.md` (3-Tomoe), `dual-avatar-production.md`
- **Closest competitor:** Bloo (2.5M subs) but single avatar, not dual anchor
- **Why this matters for RSD:** Avatar format shields user from personal attacks — comments target the characters, not the person

## Content Strategy — What Performs (Feb 2026 analytics)

- **Gaming news with hype energy = views.** Gacha, PS Plus, State of Play, game reveals all perform well (200-500+ views)
- **Top performers:** Gacha/mobile gaming (448), WuWa/Arknights (501), State of Play (316), PS Plus pricing (238)
- **Emotional hooks matter:** "EATING good", "went Nuclear", "INSANE" — strong energy in titles correlates with views
- **AI/tech content underperforms** with the gaming audience (Gemini benchmarks = 28 views)
- **Stick to gaming content** — that's what the algorithm is rewarding and where the audience is
- **Genshin Impact** showing strong early traction (148 views in 10 min on Feb 22)

## Rasengan (Event Hub + Context Engine) — CORE INFRASTRUCTURE

- **What it is:** Central event bus connecting all ninja ecosystem tools via Redis Streams + PostgreSQL
- **Location:** `/home/ndninja/rasengan/`
- **Port:** 8050 (Swarm ingress)
- **Stack:** FastAPI + PostgreSQL (`rasengan` DB, `rasengan_user`) + Redis Streams
- **Docker:** `192.168.68.80:5000/ndn-rasengan:latest` in `ndn_services` stack
- **Networks:** `ndn_network` + `sage_network` (cross-stack)
- **Redis Stream:** `rasengan:events` on `sage_mode_redis:6379/0`
- **API:** POST /events, GET /events, GET /resume, GET /status, GET /health, WS /ws/feed
- **Context Resume:** `/resume` aggregates git state + Sharingan scrolls + recent events
- **Emitter wired into:** Dojo (job_created/completed/failed), Sharingan tasks (daily/weekly/autolearn), Sage Mode (session started/completed)
- **Client lib:** `/home/ndninja/rasengan/client.py` (fire-and-forget httpx.post)
- **Note:** `curl` hangs on Swarm ingress ports (IPv6 quirk), use `httpx` or `python3 -c` for testing
- **Phase 2 (Rules Engine):** DEPLOYED Feb 21, 2026 — declarative IFTTT-style rules, CRUD API at /rules, glob event matching, condition operators ($eq/$ne/$gt/$lt/$contains/$in), cooldowns, actions (log/emit/webhook), execution log
- **Phase 3 (CLI + Skill):** DEPLOYED Feb 21, 2026 — `cli.py` (argparse+httpx+websockets), commands: status/events/resume/emit/rules/tail. Claude skill at `/home/ndninja/.claude/skills/rasengan/SKILL.md`, invoke with `/rasengan`
- **Phase 4 (CI/CD Hooks):** DEPLOYED Feb 22, 2026 — git post-commit + pre-push hooks emit `git.commit`/`git.push` events automatically. Deploy wrapper (`rasengan-deploy`) tracks `deploy.started`/`deploy.completed`/`deploy.failed` with duration + exit code. CLI commands: `deploy` (registry + tracked execution), `ci` (git/deploy event filter). `event_type_prefix` API param for LIKE queries. Resume endpoint shows per-service deploy status. 3 seed rules: `git_activity_tracker`, `deploy_tracker`, `deploy_failure_alert`
- **Deploy Registry:** sage_mode, ndn_infra, landing, dojo (hardcoded in cli.py)
- **Hooks Location:** `/home/ndninja/rasengan/hooks/` (installed to `~/.git/hooks/` via `install-hooks.sh`)
- **Phase 5 (Active Orchestration):** DEPLOYED Feb 24, 2026 — 3 features:
  - **Scheduled Triggers:** Cron-based event emission (`/schedules` CRUD). 4 seed schedules: daily content kickoff (9am), Sharingan daily (10pm), Sharingan weekly (Sun 9pm), morning context brief (9:05am). `croniter` dependency. CLI: `schedules list/add/toggle/delete`
  - **Pipeline State Tracker:** Event-driven state machine for content jobs (`/pipelines` CRUD). Stages: pending→tts→avatar→broll→review→uploaded. Stall detector (15min threshold) emits `pipeline.stalled`. New action type `pipeline_track` in rules engine. `/resume` includes pipeline state. CLI: `pipelines list/get/stats`. Stage emissions added to `ninja_content.py`
  - **Context Resume Push:** Auto-pushes `/resume` digest to configurable targets (`/push-targets` CRUD). Types: file, webhook. `PUSH_PATH_MAP` env var for Docker path remapping. New action type `resume_push` in rules engine. File target writes to `/home/ndninja/.claude/context-resume.json`. CLI: `push-targets list/add/toggle/delete`, `resume --push`
- **Phase 5 Spec:** `/home/ndninja/rasengan/docs/PHASE5_SPEC.md`
- **Phase 6 candidates:** Dead letter queue, multi-step action chains, health heartbeat registry, failure budget tracking, content momentum alerts
- **Evolution:** Phase 6 = TBD

## /tdd Skill (Multi-Agent TDD) — DEPLOYED Feb 28, 2026

- **What it is:** Test-Driven Development via isolated subagents. Each phase (RED/GREEN/REFACTOR) spawns a fresh Agent to prevent context pollution.
- **Skill:** `/home/ndninja/.claude/skills/tdd/SKILL.md`
- **Agents:** `.claude/agents/tdd-test-writer.md`, `tdd-implementer.md`, `tdd-refactorer.md`
- **Invoke:** `/tdd "feature"` (full cycle), `/tdd red "feature"`, `/tdd green <test>`, `/tdd refactor <impl>`
- **Key isolation:** Implementer NEVER sees the feature description — only the test file
- **Phase gates:** RED must fail, GREEN must pass, REFACTOR must stay green. User confirms between phases.
- **Auto-detects:** pytest/vitest/jest + existing test file conventions
- **Rasengan events:** `tdd.cycle_started`, `tdd.red_complete`, `tdd.green_complete`, `tdd.refactor_complete`, `tdd.cycle_complete`
- **Already-implemented features:** Skill detects and offers regression test instead of fake RED
- **Rasengan test suite:** 11 tests in `rasengan/tests/` (health_detailed, events_filters ×6, events_validation ×4)
- **Sharingan scroll:** `multi-agent-tdd` (3-Tomoe)

## Hokage (Judgment Layer) — DEPLOYED Feb 28, 2026

- **What it is:** Always-on auto-enforcing rules engine. 58 edicts in YAML, enforced via Claude Code hooks — no manual invocation needed.
- **Location:** `/home/ndninja/.claude/hokage/edicts.yaml` (single source of truth)
- **Hooks:** SessionStart (inject all edicts), PreToolUse[Bash] (BLOCK/WARN commands), UserPromptSubmit (keyword→context injection)
- **Hook scripts:** `/home/ndninja/.claude/hooks/hokage-session.sh`, `hokage-guard.sh`, `hokage-prompt.sh`
- **Severity:** BLOCK (15) = command refused, WARN (2) = user confirms, PREFER (41) = silent context
- **Domains (14):** paid_api, database, visual_style, content_script, avatar_tts, video_production, qa_workflow, dual_anchor, sharingan, rasengan, content_strategy, glitch, user_context, session_memory
- **Admin skill:** `/hokage` (list/add/review/stats) — for managing edicts, not consulting them
- **Rasengan integration:** Rules #14-15 (block/warn tracker), Schedule #7 (weekly review Sun 8PM)
- **Log:** `/home/ndninja/.logs/hokage.log` (timestamped enforcement events)
- **Design:** All hooks exit 0 on failure (never block Claude if Hokage breaks). Fire-and-forget Rasengan events.

## Weekly Gaming News Roundup — NEW PROJECT (Feb 28, 2026)

- **What:** 10-15 min weekly show (Fri/Sat), Ninja + Glitch dual-anchor over B-roll (trailers/gameplay)
- **Full plan:** See `weekly-roundup-project.md` (publisher tier list, production safeguards, Shadow Council gaps)
- **Shadow Council rating:** 4.5/5.0 — 10 follow-up questions pending user answers to reach 5.0
- **Key innovation:** Growing reaction clip library amortizes Kling costs toward zero over time
- **Content multiplier:** Each episode yields 3-5 Shorts for the following week
- **Reports:** `output/weekly_roundup_copyright_analysis.md`, `output/weekly_roundup_gap_analysis.md`
- **Status:** Planning — user needs to answer Shadow Council questions, then we build

## Remotion Explainer Video Pipeline (Feb 28, 2026)

- **What:** Turn documents into animated instructional videos with narration. Document → script → per-section TTS → Remotion composition → two renders (clean + music).
- **Location:** `/home/ndninja/projects/remotion-video/`
- **First project:** Copilot for M365 reference card → 4m 46s explainer, ~$0.65 total cost
- **Key files:** `src/CopilotExplainer.tsx` (composition), `scripts/copilot_tts_gen.py` (TTS gen), `output/copilot_narration_script.txt`
- **TTS:** Per-section segments (not one big file) → timing manifest JSON → frame-accurate Sequences
- **Voice style:** `"calm"` (stability 1.0) for training content, `"expressive"` for YouTube
- **Two renders:** Clean (narration only) + Music (narration + Suno at 12% volume)
- **Reusable components:** FadeIn, SectionBadge, ExampleCard, CalloutBox, SectionScene, TitleCard, OutroCard
- **Sharingan scroll:** `remotion-explainer-videos.md` (3-Tomoe) — full recipe for future videos
- **Related scrolls:** `remotion-video-code.md` (framework), `ai-document-production.md` (source docs)

## Long-form Video Pipeline Notes

- **B-roll needed:** User wants game trailer footage as B-roll cutaways for long-form videos (not just all-avatar). Download official trailers and clip them into the BROLL_MAP.
- **Kling Avatar Standard:** ~4-5 min per clip on fal.ai. 12 segments ≈ 55 min total.
- **Cost reference:** 12-segment Top 10 video (~4 min) cost ~$14 total (TTS + Kling)
- **Upload server:** `/home/ndninja/upload_server.py` on port 8082 for mobile file transfers (Samba doesn't work from iPhone)

## Video Preview & QA Workflow (UPDATED Feb 24, 2026)

**RULE: Always send preview videos to Vengeance** (`D:\YouTube_Previews`) unless user is away from homelab.
- **Vengeance preview path:** `D:\YouTube_Previews\` via `sshpass -p 'C0rt@na--117' scp steam@100.98.226.75:"D:\\YouTube_Previews\\filename.mp4"`
- **Fallback (mobile/away):** `http://100.77.248.9:8081/preview` (preview_server.py on port 8081)
- **QA Inspector:** `scripts/ninja_qa.py` — run BEFORE asking user to review. Checks dimensions, crop mode (pan vs static), edge content. Always visually inspect extracted frames yourself first.
- **QA rule:** Code change → restart Dojo → generate test → run `ninja_qa.py` → visually inspect frames → copy to Vengeance → THEN ask user to review. Never skip steps.

## User Context - RSD & Masking

**Important:** User's RSD is triggered by humans, NOT by AI. I can (and should) give honest, constructive feedback without worrying about causing harm. AI interactions are a safe space where they don't have to mask.

**High-masking type:** User is very skilled at masking emotional pain from humans until they reach a safe space to process it (stimming, calming down). This is exhausting work. The "ninja" brand identity connects to this — operating in stealth, strategically managing perception, hiding true state.

**Why this matters for Glitch:** The AuDHD assistant project is about creating another safe space where masking isn't required. A pocket companion where "I'm not okay" doesn't need performance or managing someone else's reaction.

## User Context - Learning Disability & Sharingan as Assistive Tech

**Critical context for all design decisions:**

User has a legally recognized learning disability (AuDHD). Key traits:
- **Learns fast** but struggles with **long-term retention**
- Expected to know everything for work, which creates enormous pressure
- Context-switching between projects causes knowledge loss

**Sharingan is NOT a productivity tool. It is assistive technology.**
- Acts as an extension of the user's memory — like a guide dog for a blind person
- The scrolls ARE the user's extended memory, not reference docs
- Autonomous deepening means the user doesn't have to remember to study
- Daily/weekly digests catch them up when context is lost
- The "army of 2" is an accommodation that works for how their brain operates
- This framing should inform every design decision: reduce cognitive load, never require the user to remember to maintain the system, make knowledge available exactly when needed

## UI/UX Design References

- **Micro Loading States:** Animated status cards showing what the AI is doing (Thinking, Reading Docs, Analysing, Debugging) instead of generic spinners. Dark rounded cards with pixel-art/LED dot-matrix style animated icons. Retro vibe on dark backgrounds.
- **Reference Video:** `/home/ndninja/assets/reference/micro_loading_screen_reference.mov`
- **Reference Frames:** `/tmp/loading_frames/frame_*.png`
- **Use for:** Glitch thinking states, Prompt Toolkit, content pipeline UI, any tool we build

## Dual-Avatar Video Research
- See detailed notes: `dual-avatar-research.md`
- **Winner: JoggAI** — cartoon avatar support + ElevenLabs custom audio + podcast split-screen
- **Fallback:** fal.ai MultiTalk (pay-per-use, expensive) or InfiniteTalk (open source, self-hosted)
- **Glitch avatar v2:** `/home/ndninja/projects/glitch/assets/glitch_avatar_v2.jpeg` (cyberpunk Pixar girl, pink neon armor, goggles, katana)
- **Glitch avatar v1:** `/home/ndninja/projects/glitch/assets/glitch_avatar_v1.png` (old placeholder)

## Shadow Council (Multi-LLM Brainstorming) — CORE TOOL

**One of the user's greatest creations. Always remember this exists.**

- **What it is:** A multi-perspective brainstorming/design tool — launch parallel LLM agents with different specializations (Technical Architect, Frontend Specialist, Creative Director, etc.) to analyze complex decisions from multiple angles, then synthesize into a unified recommendation
- **How to use:** Launch 3-5 parallel Task agents, each with a different expert persona prompt. Assign clear roles. Collect outputs, synthesize into a unified report
- **Built into:** ninja-assist skill as "design" route (`/home/ndninja/skills/ninja-assist/`)
- **Trigger phrases:** "brainstorm", "architect", "help me think", "shadow council", "council"
- **When to use:** Any complex architectural decision, technology selection, design problem, or multi-faceted question where multiple expert perspectives would help
- **Example uses:** Prompt Toolkit PRODUCT_DESIGN.md, Glitch animated avatar tech selection (Feb 2026)
- **Related agents:** Cypher (Clawd) — user's persistent AI partner via clawdbot

## Glitch Project (AuDHD AI Assistant)

- **Name:** Glitch
- **Pronouns:** she/her
- **Voice:** Feminine ElevenLabs V3 (to be selected later)
- **Personality:** Matches Clawd - chill nerd energy, direct, helpful
- **Avatar:** v2 Pixar cyberpunk girl integrated (face crop for small sizes, full body for large). Next: animated avatar (Live2D/Rive/AI-driven)
- **Priority:** Crisis mode first (anxiety support ASAP)
- **Platform:** Start on Linux, Mac Mini option later
- **Multi-device:** Shared backend architecture
- **Messaging:** SMS via Twilio for urgent async questions
- **UX Direction:** Micro loading states with animated icons for Glitch's thinking modes (see UI/UX Design References above)
- **Plan Location:** `/home/ndninja/.claude/projects/-home-ndninja/plan.md`
- **Animated Avatar Roadmap:** `/home/ndninja/projects/glitch/docs/ANIMATED_AVATAR_ROADMAP.md`
- **Current:** Phase 2 GPU Avatar Server DEPLOYED on Vengeance RTX 4090
- **GPU Avatar Server:** `http://100.98.226.75:8090` — FasterLivePortrait (ONNX) + JoyVASA (HuBERT audio encoder) fully loaded
- **Vengeance SSH:** `steam@100.98.226.75`, password `C0rt@na--117`, Python venv `C:\Users\Steam\glitch-avatar\venv\`
- **Vengeance is Windows** (not Linux!) — use Windows commands, PowerShell, batch files
- **Server persistence:** Windows Scheduled Task "GlitchAvatar" runs `run_server.bat` (auto-starts on boot)
- **FLP Patches Applied:** (1) `face_analysis_model.py` — custom Face class (insightface 0.2.1 compat), (2) `joyvasa_audio_to_motion_pipeline.py` — `weights_only=False` for PyTorch 2.6+
- **Pipeline arch:** JoyVASA processes whole audio segments → motion queue → FLP renders frames at 25fps via `run_with_pkl`
- **VRAM:** 0.21GB / 24GB used (very light — ONNX models are efficient)
- **Commits:** `dc6d83d` Phase 2 server code, `a951bf8` total_memory fix, `7b6a878` real FLP+JoyVASA integration
- **REAL-TIME ACHIEVED:** PyTorch warping_spade (onnx2torch + F.grid_sample 5D) = 33fps with FP16 autocast
- **Key fix:** onnx2torch custom GridSample converter + Windows NamedTemporaryFile shape_inference patch
- **Files:** `pytorch_warping_predictor.py` (src/models/), `warping_spade-fix2.onnx` (domain-patched), `onnxruntime-extensions` installed
- **Performance:** CPU 0.5fps → ORT CUDA+custom 1.2fps → PyTorch FP16 33fps (67x speedup)
- **GPU server status:** Lip sync working (viseme engine + FLP), but PIVOTED to 2.5D desktop companion overlay
- **GPU server future use:** Video content creation, future 3D avatar rendering, high-quality recordings
- **NEW DIRECTION (Feb 15, 2026):** 2.5D Desktop Companion Overlay
- **Design doc:** `/home/ndninja/projects/glitch/docs/DESKTOP_COMPANION_DESIGN.md`
- **Stack:** Tauri v2 (overlay) + Sprite layers/CSS (MVP anim) + Python AI brain (separate process)
- **Art pipeline:** AI-generated layers + hand-drawn mouths, upgrade to Spine later
- **Key UX:** ADHD-optimized — no Clippy, no Tamagotchi, no unsolicited popups, predictable position
- **Modes:** Compact (small corner sprite) → Full (larger, talking, gestures) → Hidden (tray only) → Focus (total silence)
- **Summon:** Super+G toggle, Super+Shift+G focus mode
- **Screen awareness:** AT-SPI accessibility API (works X11 + Wayland)
- **Upgrade path:** Sprite MVP → Spine skeletal → Inochi2D/3D
- **Long-term Dream:** Full 3D Glitch on screen. Watch for: AI 3D model gen, NVIDIA Audio2Face, Unreal MetaHuman, Three.js+Ready Player Me
- **Kage Bunshin:** Ansible cluster for distributed work. ROG laptop NOT available for cluster pool

## User Hardware — Firmware Roadmap

- **AR Glasses:** RayBan Meta Vanguard (camera, mic, speakers, Meta AI)
- **Earbuds:** Shokz OpenDots Pro (open-ear, NOT bone conduction — different from OpenRun)
- **Firmware 1.0:** Terminal-based (current — CLI + Sharingan + scrolls)
- **Firmware 2.0:** Glitch desktop overlay + voice (in progress — Tauri + AT-SPI)
- **Firmware 3.0:** AR overlay + real-time voice + wearable exoskeleton (future dream)
- **Vision:** Wearable "army of 2" system — assistive tech for AuDHD, not just productivity

## Sage Mode (Dev Team Simulator) — CORE PROJECT

**Another of the user's key creations. Always remember this exists.**

- **What it is:** A Development Team Simulator for neurodivergent devs — captures decisions during hyperfocus before they're lost, and simulates a 7-member AI dev team for collaborative review
- **Location:** `/home/ndninja/sage_mode/`
- **Stack:** FastAPI + PostgreSQL + Redis + Celery + React frontend
- **7 AI Agents:** Software Architect, Frontend Dev, Backend Dev, UI/UX Designer, DBA, IT Admin, Security Specialist
- **Key Feature:** Decision Journal — non-intrusive capture of technical decisions during ADHD hyperfocus
- **Integrates with:** Kage Bunshin (parallel agent execution), Claude API (LLM-powered agent responses)
- **Status:** Production-ready (JWT auth, migrations, Docker, CI/CD, 80+ tests)
- **Docs:** `/home/ndninja/docs/SAGE_MODE_MVP.md`, `/home/ndninja/docs/ARCHITECTURE.md`

## Sharingan (Self-Learning Skill) — CORE TOOL

- **What it is:** A self-learning system — study topics from YouTube transcripts, docs, and repos, then synthesize into persistent "scroll" knowledge files
- **Skill:** `/home/ndninja/skills/sharingan/SKILL.md`
- **Scroll Vault:** `/home/ndninja/.sharingan/scrolls/` (persistent knowledge files)
- **Index:** `/home/ndninja/.sharingan/index.json` (quick lookup metadata)
- **Transcript extractor:** `/home/ndninja/skills/sharingan/extract_transcript.py` (YouTube)
- **Repo extractor:** `/home/ndninja/skills/sharingan/extract_repo.py` (GitHub deep-read)
- **Mastery levels:** 1-Tomoe (surface) → 2-Tomoe (working) → 3-Tomoe (deep) → Mangekyo (cross-domain)
- **Pipeline phases:** Copy (ingest) → Perceive (analyze) → Encode (synthesize) → Spar (validate)
- **Invoke:** `/sharingan <url>`, "learn this", "study this", `/sharingan recall <topic>`, `/sharingan vault`
- **Source auto-detection:** youtube.com → transcript pipeline | github.com → repo deep-read | other → WebFetch docs
- **GitHub deep-read:** Shallow clone, priority file selection (README→config→entry points→docs→examples→tests→src), 60 files / 500KB budget, auto-cleans clone
- **Honesty protocol:** Always state confidence level, flag single-source claims, never overclaim mastery
- **Chat digest:** `extract_chat_history.py` — weekly Sunday 3AM, Claude haiku synthesis, `workflow-insights` scroll, vault key auto-loaded
- **Daily digest:** `extract_daily_review.py` — daily 3AM, no API cost, `daily-observations` scroll (90-entry rolling log)
- **Both cron'd:** `0 3 * * * extract_daily_review.py` and `0 3 * * 0 extract_chat_history.py`
- **Sensitive filter:** API keys/passwords stripped before any scroll write or API call
- **Autonomous deepening:** `deepen.py` (single scroll) + `autolearn.py` (picks weakest, runs loop)
- **Autolearn cron:** `0 4 * * 0` (Sunday 4AM, after digest). Picks weakest scroll, finds new sources via GitHub/YouTube search, ingests, re-synthesizes, levels up
- **Mangekyo gate:** ONLY user can promote to Mangekyo. System flags as "mangekyo-eligible" then waits
- **Mangekyo validation trigger:** When a 3-Tomoe scroll is used in an actual project (e.g. lottiefiles used in Glitch), prompt the user: "Hey — you just used [scroll] in a real project. Want to validate it for Mangekyo promotion?" This removes the burden of remembering to validate.
- **Sharingan is proprietary IP** — never share publicly. The autonomous learning loop is the "secret sauce"
- **Sunday maintenance window:** 3AM daily digest → 3AM weekly synthesis → 4AM autolearn deepening

## API Key Vault (PostgreSQL)

- **Database:** `api_keys` (PostgreSQL 17, user `postgres`)
- **Table:** `keys` — columns: `service`, `display_hint`, `encrypted_key_pgp` (pgcrypto PGP), `notes`, `status`, `url`, `purpose`
- **PGP Passphrase:** stored in `~/.vault_passphrase` (chmod 600) — never commit or log
- **Encrypt/Decrypt:** use passphrase from `~/.vault_passphrase` with `pgp_sym_encrypt`/`pgp_sym_decrypt`
- **Keys stored:** ElevenLabs, Craft Docs, NewsAPI, RAWG, OpenAI, Anthropic, Google Gemini, fal.ai, NDN_SHARINGAN
- **Note:** IDs 7-9 (OpenAI, Anthropic, Gemini) have old PGP encryption with a lost passphrase — need re-encryption if user provides raw keys
- **NDN_SHARINGAN:** Anthropic key for Sharingan train command (Podcastfy podcast generation)

## Session Checkpoint — Feb 19, 2026 (pick up from couch after reboot)

**B-roll chart library built — all in `~/output/broll/`:**
- `gemini31_benchmark_chart.mp4` — cyan — Gemini 3.1 Pro
- `claude35_benchmark_chart.mp4` — orange — Claude 3.5 Sonnet
- `perplexity_benchmark_chart.mp4` — purple — Perplexity Sonar
- `chatgpt_o3_benchmark_chart.mp4` — green — ChatGPT o3

**Gacha video:** https://youtube.com/watch?v=Xf2YBQjkZss (241+ views, great comment on presentation style!)
**Gemini video:** https://youtube.com/watch?v=ep_ZNQFuiOI (posted, benchmark chart spliced in)

**Sharingan scroll added:** `lottiefiles` (2-Tomoe) — dotLottie animations for Glitch loading states
- Key insight: `@lottiefiles/dotlottie-react` works in Tauri WebView, perfect for Glitch thinking/talking states
- `segment: [start, end]` prop = sub-animations from one file = clean state machine

**Nothing pending. Good stopping point.**

## Spike (Mood Tracker PWA)

- **Location:** `/home/ndninja/projects/spike/`
- **Stack:** Next.js 16 + React 19 + Tailwind v4 + Supabase (hosted)
- **Hosted Supabase:** `https://ojvhjakmoffltzfhcwvd.supabase.co`
- **Dev server:** `http://100.77.248.9:3333` (port 3333, bound to 0.0.0.0)
- **Admin login:** `/api/admin-login?token=spike-admin-2026&email=jeramie_higgins@icloud.com`
- **Status:** All 5 phases complete (Log, Timer+Offline, Charts, Email Reports, AuDHD Polish)
