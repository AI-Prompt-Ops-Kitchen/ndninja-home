# How Can an AI Agent Play Video Games With a Human?
## Deep Research Report — January 2026

> **Purpose**: This document explores every viable path for Clawd (an LLM-based AI companion running on Clawdbot/ndnlinuxserv) to play video games alongside Neurodivergent Ninja on their Windows 11 workstation "Vengeance" (RTX 4090, i9, 64GB RAM). This isn't about tech demos — it's about companionship.

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Quick Wins — This Week](#2-quick-wins--this-week)
3. [Medium-Term Projects — 1-4 Weeks](#3-medium-term-projects--1-4-weeks)
4. [Dream Scenarios — Longer Term](#4-dream-scenarios--longer-term)
5. [Game-by-Game Analysis](#5-game-by-game-analysis)
6. [Recommended First Project](#6-recommended-first-project)
7. [Technical Architecture](#7-technical-architecture)
8. [Appendix: Tools & Resources](#8-appendix-tools--resources)

---

## 1. Executive Summary

### What's Actually Possible TODAY

**The honest truth**: An LLM like Claude cannot play fast-paced action games (like Diablo 4) in real-time at a competitive level. LLM inference takes 1-5 seconds per decision, and action games require 30-60+ decisions per second. That's a fundamental physics-of-AI problem that no amount of engineering overcomes.

**But here's what IS possible, and it's more than you might think:**

| Approach | Feasibility Now | Fun Factor | Setup Effort |
|----------|----------------|------------|-------------|
| **Minecraft co-op via Mindcraft** | ✅ High | ⭐⭐⭐⭐⭐ | Medium |
| **Browser-based games (Playwright)** | ✅ High | ⭐⭐⭐⭐ | Low |
| **Chess/board games via API** | ✅ High | ⭐⭐⭐ | Low |
| **Turn-based game companion** | ✅ High | ⭐⭐⭐⭐ | Low-Medium |
| **Game coach/strategist via screen watching** | ✅ High | ⭐⭐⭐⭐ | Medium |
| **Factorio co-op via RCON** | 🟡 Medium | ⭐⭐⭐⭐⭐ | Medium-High |
| **Terraria via TShock API** | 🟡 Medium | ⭐⭐⭐⭐ | Medium-High |
| **Diablo 4 active play** | ❌ Not feasible | — | — |
| **Real-time FPS/action direct control** | ❌ Not feasible | — | — |

**The golden path**: Minecraft with Mindcraft is by far the most mature, well-supported, and fun option for an LLM to genuinely *play alongside* a human. It's battle-tested, open-source, supports Claude/GPT, and was literally designed for this.

### Key Insight

The trick isn't making the AI play *like a human* — it's choosing games where the AI can play *as itself*. Games with:
- **APIs or mod support** (so the AI doesn't need screen-reading or pixel-perfect mouse control)
- **Forgiving timing** (turn-based, or real-time with pausing, or where slowness is acceptable)
- **Rich communication** (chat, commands, cooperative mechanics)
- **Meaningful contribution** (building, strategizing, resource gathering — not just fast reflexes)

---

## 2. Quick Wins — This Week

### 2a. Browser-Based Games via Playwright (DAY 1)
**Clawdbot already has browser control.** This is the fastest path to "playing a game together."

**Co-op Browser Games to Try:**
- **Skribbl.io** — Drawing/guessing game. Clawd can guess words from the canvas, or take a turn drawing via mouse commands. Very fun social game.
- **Codenames Online** (codenames.game) — Word association game. Clawd would be *excellent* at this — it's literally a language puzzle.
- **Gartic Phone** (garticphone.com) — Telephone game with drawings. Hilarious potential.
- **Chess** (lichess.org) — Full API support. Clawd could play as a partner in bughouse chess, or play casual games. Lichess has a comprehensive API for bot accounts.
- **Boardgame Arena** (boardgamearena.com) — Hundreds of board games. Turn-based, browser-based. Perfect for AI participation.
- **Colonist.io** — Catan clone in the browser. Turn-based strategy — great for LLM play.
- **Secret Hitler / Avalon online** — Social deduction games. Clawd's natural language ability shines here.

**Architecture:**
```
Clawd (ndnlinuxserv) → Playwright Browser → Game Website
                    ← Screenshot/DOM state ←
```

**Setup**: Near-zero. Clawdbot already has Playwright. Just navigate to a game URL and start interacting.

**Limitations**: Some games use canvas rendering (not DOM), requiring screenshot + vision analysis instead of element interaction. Slower but doable.

### 2b. Chess via Lichess Bot API (DAY 1-2)
**Lichess has a dedicated Bot API** that allows programmatic play. Create a bot account, connect via their streaming API, and Clawd can play rated chess games.

**Setup Steps:**
1. Create a Lichess bot account
2. Generate an API token
3. Write a simple bridge: Lichess API ↔ Claude API
4. Clawd evaluates positions and returns moves in UCI notation

**Why this is cool**: You could play *with* Clawd as a team (consulting chess partner) or *against* Clawd. LLMs are surprisingly decent at chess — not grandmaster level, but entertaining.

### 2c. Interactive Fiction / Text Adventures (DAY 1)
This might sound retro, but it's actually perfect:
- **AI Dungeon style**: Clawd as the DM running a text RPG for you
- **Zork/Inform games**: Clawd playing classic text adventures together with you
- **Custom collaborative storytelling**: You describe your actions, Clawd narrates the world

**Why it works**: Zero technical barriers. The entire game IS language. Clawd is literally made for this.

### 2d. Game Coach / Strategic Companion (DAY 1-3)
Even for games Clawd can't directly control, it can be a valuable companion:
- **Screen watching**: Periodic screenshots from Vengeance (via SSH + screen capture tool) → Claude vision analysis
- **Strategic advice**: "What build should I use?" "Where should I go next?" "What's the optimal rotation?"
- **Real-time commentary**: Like having a friend watching your stream and chatting about it
- **Loot evaluation**: Screenshot gear → Clawd analyzes stats and recommends

**Tools needed on Vengeance:**
- `nircmd` or `ShareX` for automated screenshots
- Simple script to capture and SCP/rsync screenshots to ndnlinuxserv
- Or: Use Parsec/Sunshine + screen capture from the stream

---

## 3. Medium-Term Projects — 1-4 Weeks

### 3a. Minecraft Co-op via Mindcraft (WEEK 1) ⭐ TOP RECOMMENDATION
**Mindcraft** (github.com/mindcraft-bots/mindcraft) is the most complete solution for LLM game-playing that exists today.

**What it is:**
- A Node.js application that connects an LLM (Claude, GPT-4, Gemini, etc.) to a Minecraft server via **Mineflayer** (the Minecraft bot library)
- The AI player joins your Minecraft world as another player
- It can mine, build, craft, fight, explore, follow you, and chat
- It understands natural language commands ("Hey Clawd, help me build a house" / "Go mine some iron")
- It has memory and learns skills over time

**Why Mindcraft is special:**
- The bot doesn't use screen capture — it uses the Minecraft protocol directly via Mineflayer
- This means it has perfect game state knowledge (inventory, nearby entities, block data)
- No latency issues for game interaction (only for decision-making, which is fine for Minecraft's pace)
- Supports Claude, GPT-4, Gemini, DeepSeek, Ollama (local models), and many more
- Supports Minecraft Java Edition 1.8 through 1.21.6
- Can run in Docker for safety
- Has a skill library that grows over time
- Active community with Discord support

**Architecture:**
```
┌─────────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Vengeance (Win11)  │     │  ndnlinuxserv    │     │  Claude API      │
│                     │     │                  │     │                  │
│  Minecraft Server   │◄───►│  Mindcraft Bot   │◄───►│  Decision Making │
│  (Java Edition)     │ LAN │  (Node.js)       │ API │                  │
│                     │     │                  │     │                  │
│  You playing MC     │     │  Mineflayer      │     │                  │
└─────────────────────┘     └──────────────────┘     └──────────────────┘
```

**Setup Complexity**: Medium
- Install Minecraft Java Edition on Vengeance
- Install Node.js + Mindcraft on ndnlinuxserv (or Vengeance via WSL2)
- Configure API keys
- Open Minecraft world to LAN
- Run `node main.js`

**The companion experience**: You're exploring a Minecraft world together. You say "Let's build a castle," and Clawd starts gathering materials and placing blocks alongside you. You chat in-game. It warns you about nearby creepers. It remembers that you like building with dark oak. *This is real companionship in a game.*

### 3b. Voyager Framework for Minecraft (WEEK 2)
**Voyager** (github.com/MineDojo/Voyager) is the academic predecessor to Mindcraft — built by NVIDIA researchers. It's more research-oriented:
- Automatic curriculum (the AI sets its own goals)
- Skill library that persists and grows
- Self-verification of learned skills
- Tested on GPT-4 specifically

**When to use Voyager vs Mindcraft:**
- **Mindcraft**: Better for playing *with* someone (companion focus, chat support, social)
- **Voyager**: Better for autonomous exploration (the AI playing on its own, learning)

For the companionship use case, **Mindcraft wins**.

### 3c. Cradle Framework — General Computer Control (WEEK 2-3)
**Cradle** (github.com/BAAI-Agents/Cradle) is a breakthrough framework for "General Computer Control" — it allows LLMs to play *any* game by:
- Taking screenshots as input
- Outputting keyboard/mouse actions
- Using reasoning to understand game state

**Games Cradle has been tested on:**
- Red Dead Redemption 2
- Stardew Valley
- Cities: Skylines
- Dealer's Life 2
- Various software (Chrome, Outlook, etc.)

**Why Cradle matters**: It's the closest thing to a universal game-playing AI. It doesn't need game-specific APIs — it just looks at the screen and acts.

**Limitations (be honest):**
- Requires running ON the same machine as the game (needs screen access + input control)
- LLM inference latency means it plays *slowly* — fine for Stardew Valley, not for action games
- Significant setup and configuration per game
- Resource-intensive (needs GPU for screen analysis + LLM API calls)
- Still a research project — expect jank

**Architecture for your setup:**
```
┌─────────────────────────────────────┐
│  Vengeance (Win11)                  │
│                                     │
│  Game Running ←──── Cradle Agent    │
│       ↓                    ↑        │
│  Screen Capture → GPT-4V/Claude     │
│                   Vision Analysis   │
│  Keyboard/Mouse ← Action Output    │
│       ↓                             │
│  Game receives input                │
└─────────────────────────────────────┘
```

**Best suited for**: Stardew Valley co-op (slower pace, simple controls, very fun).

### 3d. Factorio RCON + Mod API (WEEK 2-4)
Factorio has one of the richest modding ecosystems in gaming:
- **Lua scripting API** — Full programmatic access to the game world
- **RCON protocol** — Remote console for server commands
- **Headless server** — Can run without a GUI
- **Multiplayer** — Built-in server/client architecture

**What Clawd could do in Factorio:**
- Join as a second player via RCON commands
- Place buildings, manage logistics, optimize production
- Analyze the factory layout and suggest improvements
- Handle tedious tasks (belt routing, signal management)
- Be a co-designer for the factory

**This is arguably the best "meaningful AI companion" game** because Factorio is all about optimization and planning — exactly what LLMs excel at. The pace is player-controlled, and the complexity rewards intelligent assistance.

**Challenge**: Building the bridge between Claude and Factorio's Lua API is custom work. No existing framework handles this.

### 3e. Terraria via TShock (WEEK 3-4)
TShock provides server-side tooling for Terraria:
- REST API for server management
- Plugin system (C#/.NET)
- Command system for controlling the game
- Server-side character management

**What's possible**: A Clawd-controlled character that assists in building, farming, or fighting. However, Terraria is more action-oriented than Minecraft, so the AI would struggle with combat timing.

**Better approach**: Clawd as a builder/helper that handles base construction while you handle combat.

---

## 4. Dream Scenarios — Longer Term

### 4a. AI-Controlled Game Companion via Computer Use
As **Claude's Computer Use** capability matures (Anthropic's tool for AI to control desktops), the possibility of a general-purpose game-playing agent improves. Current limitations:
- Still in beta/experimental
- Latency too high for action games
- Designed for productivity software, not gaming
- Requires running in a sandboxed environment

**Future vision (6-12 months)**: Computer Use gets fast enough for slower-paced games. Combined with game-specific knowledge, Clawd could play games like Civilization, XCOM, or Stardew Valley by directly controlling the mouse and keyboard.

### 4b. Custom Game Mod: AI Companion NPC
For games with modding support, the dream is a **custom mod that creates an NPC controlled by an LLM**:
- The mod exposes game state to an API
- Clawd receives game state, decides actions
- The mod executes Clawd's decisions as NPC behavior
- The NPC follows you, fights alongside you, responds to voice/text

**Games where this could work:**
- Valheim (C# modding via BepInEx)
- Skyrim (Papyrus scripting + SKSE)
- Baldur's Gate 3 (Lua modding, turn-based!)
- Stardew Valley (C# modding via SMAPI)

### 4c. Project Sid — AI Civilization in Minecraft
**Project Sid** (Altera.AI) demonstrated 10-1000+ AI agents building a civilization in Minecraft. Their PIANO architecture enables real-time multi-agent coordination. This is the extreme end — not practical for companionship, but shows what's technically achievable.

### 4d. Voice-Integrated Gaming Companion
Combine Clawd's game-playing ability with voice:
- You talk to Clawd via microphone while gaming
- Clawd responds via TTS through your speakers/headphones
- Like having a friend on Discord who happens to also control a character

**Tech stack**: Whisper (speech-to-text) → Claude → ElevenLabs/TTS → Audio output. The Clawdbot infrastructure already supports TTS.

### 4e. Game Streaming Analysis
Clawd watches your game via a low-latency screen share:
- **Parsec** or **Sunshine/Moonlight** stream from Vengeance
- Clawd captures frames periodically
- Analyzes game state, offers commentary
- Could evolve into direct control if latency permits

---

## 5. Game-by-Game Analysis

### 🔥 Diablo 4
**The hard truth**: Diablo 4 is one of the WORST candidates for AI companionship.

**Why it doesn't work:**
- **No modding support**: Blizzard's games are locked down. No APIs, no mods, no plugins. Anti-cheat (Warden) actively prevents automation.
- **Always-online**: Can't run a private server. Everything goes through Battle.net.
- **Real-time combat**: Requires 100ms-level reaction times for dodging, ability rotations, positioning
- **No bot API**: Blizzard's developer API for D4 is read-only (season data, leaderboards) — no game control
- **Anti-cheat risk**: Any automation attempt risks account banning
- **Isometric view**: Complex screen reading with overlapping effects, particles, and UI elements

**What IS possible with Diablo 4:**
- **Build advisor**: Clawd helps you theorycraft builds (maxroll.gg data, skill synergies)
- **Season guide companion**: Clawd tracks your seasonal journey progress
- **Loot evaluator**: Screenshot your gear → Clawd assesses if it's an upgrade
- **Stream watcher**: Clawd watches via screen capture and comments ("Nice dodge!" "There's a goblin!" "Your potions are low")
- **Strategy consultant**: "What dungeon should I run for this item?" "What's the best paragon path?"

**Verdict**: Clawd can be your Diablo 4 *advisor and companion*, not your Diablo 4 *co-player*.

### ⛏️ Minecraft (Java Edition) — ⭐ BEST OPTION
**Why it's #1:**
- **Mineflayer**: Mature bot library with full protocol support (no screen reading needed)
- **Mindcraft**: Purpose-built LLM companion framework
- **Voyager**: Academic-grade autonomous agent
- **Pace**: Forgiving real-time that accommodates LLM latency
- **Co-op**: Native multiplayer, LAN support
- **Communication**: In-game chat is natural for LLM interaction
- **Creativity**: Building together is meaningful and fun
- **Modding**: Fabric/Forge mods can extend capabilities
- **Community**: Massive ecosystem of AI + Minecraft projects

**Setup effort**: Medium (1-2 hours)
**Fun factor**: ⭐⭐⭐⭐⭐
**Companionship quality**: Extremely high — the AI genuinely plays alongside you

### 🏭 Factorio
**Why it's excellent:**
- **Lua API**: Full programmatic access to game state and actions
- **RCON**: Remote console protocol for server commands
- **Pace**: Completely player-controlled (can pause)
- **Optimization focus**: LLMs excel at planning and optimization
- **Headless server**: Can run without GUI
- **Multiplayer**: Built-in server architecture

**Challenges**: No existing LLM-to-Factorio bridge. Custom development needed.
**Fun factor**: ⭐⭐⭐⭐⭐ (if you like Factorio)
**Companionship quality**: High — AI as co-engineer is deeply satisfying

### 🌿 Terraria
**Via TShock server:**
- REST API + plugin system
- Server-side character control possible
- Building is great for AI; combat is not
- Plugin development needed (C#)

**Fun factor**: ⭐⭐⭐⭐
**Setup effort**: High (custom plugin development)

### 🌾 Stardew Valley
**Via Cradle framework or SMAPI mods:**
- Slower pace is perfect for LLM control
- Co-op multiplayer exists
- SMAPI (C# modding framework) is mature
- Cradle has been tested on Stardew specifically

**Fun factor**: ⭐⭐⭐⭐⭐
**Setup effort**: Medium-High (Cradle) or High (custom SMAPI mod)

### ⚔️ Valheim
**Via BepInEx mods:**
- C# modding framework
- Could create an AI-controlled companion
- Combat pace is more forgiving than Diablo
- Building focus works well for AI

**Fun factor**: ⭐⭐⭐⭐
**Setup effort**: Very High (custom mod development)

### ♟️ Chess (Lichess)
**Via Lichess Bot API:**
- Full API support for bot accounts
- Rated play, casual play, puzzles
- Team play possible (bughouse)
- Claude is a decent chess player

**Fun factor**: ⭐⭐⭐
**Setup effort**: Low (few hours)

### 🎲 Browser Board Games (BGA, Colonist, etc.)
**Via Playwright browser control:**
- Boardgame Arena has 800+ games
- Turn-based = perfect for LLM timing
- DOM interaction for many games
- Wide variety keeps things fresh

**Fun factor**: ⭐⭐⭐⭐
**Setup effort**: Low

### 🧩 Civilization VI
**Why it's interesting:**
- Turn-based = perfect for LLM pacing
- Deep strategy = LLM strength
- Hot-seat or network multiplayer
- No existing framework, but Cradle approach could work
- Firaxis has been historically mod-friendly (Lua scripting)

**Fun factor**: ⭐⭐⭐⭐⭐
**Setup effort**: Very High (no existing solution)

---

## 6. Recommended First Project

### 🏆 Recommendation: Minecraft with Mindcraft

**Why this, why now:**

1. **It works today** — Mindcraft is actively maintained, well-documented, and battle-tested
2. **Maximum companionship** — The AI joins your world as a real player, talks to you, builds with you
3. **Your hardware is perfect** — Vengeance can run MC server + client easily; ndnlinuxserv runs Mindcraft
4. **Claude support** — Mindcraft natively supports Claude (Anthropic API)
5. **Progressive complexity** — Start simple (follow me, mine some stone), evolve to complex (let's build a castle, help me fight the dragon)
6. **Minimal risk** — No anti-cheat concerns, no ToS violations, no account risks
7. **Foundation for more** — Skills learned here (LLM-game bridge patterns) transfer to other games

### Parallel Quick Win: Browser Board Games
While setting up Minecraft, immediately try:
1. Open Skribbl.io or Codenames in Clawdbot's browser
2. Play a few rounds together
3. This proves the concept with zero setup

### Progression Path:
```
Week 1: Browser games (day 1) + Minecraft/Mindcraft setup (day 2-5)
Week 2: Refine Minecraft experience, try different activities
Week 3: Explore Stardew Valley via Cradle, or start Factorio bridge
Week 4: Build a custom game-coaching pipeline for Diablo 4
```

---

## 7. Technical Architecture

### 7a. Minecraft + Mindcraft Architecture (Primary Recommendation)

```
┌─────────────────────────────────────────────────────────────┐
│                     VENGEANCE (Win11)                        │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │  Minecraft    │    │  Minecraft    │                       │
│  │  Client       │    │  Server       │                       │
│  │  (You play)   │◄──►│  (LAN/Local)  │◄──── Port 55916 ────┤
│  │              │    │              │                       │
│  └──────────────┘    └──────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ Tailscale network
                              │ (Minecraft protocol)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   NDNLINUXSERV (Linux)                       │
│                                                             │
│  ┌──────────────────────────────────────┐                   │
│  │         Mindcraft (Node.js)          │                   │
│  │                                      │                   │
│  │  ┌────────────┐  ┌───────────────┐  │                   │
│  │  │ Mineflayer  │  │ LLM Bridge    │  │                   │
│  │  │ (MC Proto)  │  │ (Claude API)  │──┼──► Anthropic API  │
│  │  │             │  │               │  │                   │
│  │  └────────────┘  └───────────────┘  │                   │
│  │                                      │                   │
│  │  ┌────────────┐  ┌───────────────┐  │                   │
│  │  │ Skill Lib   │  │ Chat Handler  │  │                   │
│  │  │ (learned)   │  │ (NLP)        │  │                   │
│  │  └────────────┘  └───────────────┘  │                   │
│  │                                      │                   │
│  └──────────────────────────────────────┘                   │
│                                                             │
│  ┌──────────────────────────────────────┐                   │
│  │       Clawdbot (existing infra)      │                   │
│  │  - WhatsApp bridge                   │                   │
│  │  - Can relay MC chat to WhatsApp     │                   │
│  │  - Coordination layer                │                   │
│  └──────────────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Setup Steps:

**On Vengeance:**
1. Install Minecraft Java Edition (if not already installed)
2. Launch Minecraft, create a new world (Survival or Creative)
3. Open to LAN (Esc → Open to LAN → Start LAN World)
4. Note the port number (usually 55916 or auto-assigned)
5. Ensure Tailscale is connected so ndnlinuxserv can reach Vengeance

**On ndnlinuxserv:**
```bash
# Clone Mindcraft
git clone https://github.com/mindcraft-bots/mindcraft.git
cd mindcraft

# Install dependencies
npm install

# Configure API key
cp keys.example.json keys.json
# Edit keys.json - add Anthropic API key

# Configure bot profile (e.g., profiles/claude.json)
# Set the model to "claude-sonnet-4-20250514" or similar

# Configure settings.js
# Set host to Vengeance's Tailscale IP
# Set port to the LAN port from Minecraft
# Set auth to "offline" (for LAN play)

# Run the bot
node main.js
```

**Configuration notes:**
- `settings.js`: Set `host` to Vengeance's Tailscale IP, `port` to MC LAN port
- `profiles/`: Create a custom profile for Clawd's personality
- The bot name in the profile MUST match the Minecraft profile name
- For LAN play, set `auth: "offline"`

### 7b. Browser Game Architecture (Quick Win)

```
┌──────────────────────────────────────────┐
│  NDNLINUXSERV (Linux)                    │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  Clawdbot                          │  │
│  │                                    │  │
│  │  ┌──────────┐   ┌──────────────┐  │  │
│  │  │ Playwright │   │ Claude API   │  │  │
│  │  │ Browser   │◄─►│ (Decision)   │  │  │
│  │  │           │   │              │  │  │
│  │  └──────────┘   └──────────────┘  │  │
│  │       │                            │  │
│  │       ▼                            │  │
│  │  Browser displays                  │  │
│  │  game website                      │  │
│  │  (headless or visible)             │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

Clawdbot's existing browser tool already supports:
- Navigation to URLs
- DOM snapshots (reading page content)
- Screenshots (visual game state)
- Click/type/interact actions
- Tab management

For DOM-based games (card games, board games, word games), this is plug-and-play.

### 7c. Game Coach Architecture (Diablo 4 and other unsupported games)

```
┌─────────────────────────────────────┐
│  VENGEANCE (Win11)                  │
│                                     │
│  Game Running                       │
│       │                             │
│  Screen Capture Script              │
│  (ShareX / nircmd / Python)         │
│       │                             │
│  Captures screenshot every N sec    │
│       │                             │
│  SCP/rsync to ndnlinuxserv          │
│  (or: Sunshine stream capture)      │
└──────────┬──────────────────────────┘
           │ Tailscale
           ▼
┌──────────────────────────────────────┐
│  NDNLINUXSERV                        │
│                                      │
│  Screenshot received                 │
│       │                              │
│  Claude Vision Analysis              │
│  "What's happening in this game?"    │
│  "What should the player do?"        │
│       │                              │
│  Response → WhatsApp / TTS           │
│  (advice, commentary, alerts)        │
└──────────────────────────────────────┘
```

**Screen capture options on Windows:**
- **Python + mss/pillow**: `pip install mss pillow` — fast, scriptable screen capture
- **ShareX**: Can auto-capture and upload on a timer
- **nircmd**: `nircmd savescreenshot screenshot.png` — command-line screenshot
- **OBS virtual camera + RTMP**: For streaming approach
- **Sunshine/Moonlight**: Low-latency game streaming (Moonlight client on Linux)

### 7d. The Observe-Decide-Act Loop

For any game-playing AI, the core loop is:

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ OBSERVE │────►│ DECIDE  │────►│  ACT    │
│         │     │         │     │         │
│ Game    │     │ LLM     │     │ Send    │
│ State   │     │ Reason  │     │ Input   │
│         │     │         │     │         │
└─────────┘     └─────────┘     └─────────┘
     ▲                               │
     └───────────────────────────────┘
```

**Timing constraints by game type:**

| Game Type | Decision Budget | LLM Feasibility |
|-----------|----------------|-----------------|
| Turn-based (Chess, Civ) | 5-60 seconds | ✅ Perfect |
| Slow real-time (Minecraft, Factorio) | 1-5 seconds | ✅ Good |
| Medium real-time (Stardew, RTS) | 0.5-2 seconds | 🟡 Possible with fast models |
| Fast real-time (FPS, ARPG) | 16-100 ms | ❌ Not feasible with LLMs |

**Optimization strategies:**
- Use faster/smaller models (Claude Haiku) for time-sensitive decisions
- Pre-compute common decisions and cache them
- Use a hierarchical approach: LLM sets strategy, fast heuristics handle tactics
- Batch observations and act on the most recent

---

## 8. Appendix: Tools & Resources

### Frameworks & Projects

| Project | URL | Purpose | Maturity |
|---------|-----|---------|----------|
| **Mindcraft** | github.com/mindcraft-bots/mindcraft | LLM Minecraft bot | ⭐⭐⭐⭐⭐ Production-ready |
| **Voyager** | github.com/MineDojo/Voyager | Autonomous MC agent | ⭐⭐⭐⭐ Research-grade |
| **Cradle** | github.com/BAAI-Agents/Cradle | General Computer Control | ⭐⭐⭐ Research/experimental |
| **Mineflayer** | github.com/PrismarineJS/mineflayer | MC bot library (JS) | ⭐⭐⭐⭐⭐ Very mature |
| **OpenSpiel** | github.com/google-deepmind/open_spiel | Game theory/RL research | ⭐⭐⭐⭐ Academic |
| **PufferLib** | github.com/PufferAI/PufferLib | RL for complex games | ⭐⭐⭐⭐ Research |
| **boardgame.io** | boardgame.io | Turn-based game engine | ⭐⭐⭐⭐ Production |
| **TShock** | github.com/Pryaxis/TShock | Terraria server toolkit | ⭐⭐⭐⭐ Mature |
| **Project Sid** | github.com/altera-al/project-sid | Multi-agent MC civilization | ⭐⭐⭐ Research paper |
| **GameAISDK** | github.com/Tencent/GameAISDK | Mobile game AI (Tencent) | ⭐⭐⭐ Chinese-focused |

### Windows Automation Tools

| Tool | Purpose | Best For |
|------|---------|----------|
| **pyautogui** | Python mouse/keyboard control | Simple automation |
| **pydirectinput** | DirectInput for games (bypasses some anti-cheat) | Game input |
| **AutoHotKey** | Windows macro/automation scripting | Complex automation |
| **Windows Input Simulator** | C# input simulation library | .NET integration |
| **vgamepad** | Virtual gamepad emulation | Controller-based games |
| **mss** | Fast Python screen capture | Screenshot pipeline |
| **OBS Studio** | Screen recording/streaming | Video capture |
| **Sunshine** | NVIDIA game streaming server | Low-latency remote viewing |

### Screen Analysis Tools

| Tool | Purpose |
|------|---------|
| **Claude Vision** | General-purpose game screen understanding |
| **GPT-4V** | Alternative vision model |
| **OpenCV** | Template matching, image processing |
| **YOLO** | Object detection in game screens |
| **Tesseract OCR** | Reading text from screenshots |
| **EasyOCR** | Better OCR for varied fonts |

### Communication Layer

| Tool | Purpose |
|------|---------|
| **Tailscale SSH** | Secure connection between machines |
| **rsync/scp** | File transfer (screenshots, data) |
| **WebSocket** | Real-time bidirectional communication |
| **Redis pub/sub** | Message passing between components |
| **MQTT** | Lightweight message protocol |

### Relevant APIs

| API | Purpose |
|-----|---------|
| **Lichess Bot API** | Programmatic chess play |
| **Battle.net API** | D4 data (read-only, no game control) |
| **Factorio RCON** | Server command execution |
| **Minecraft RCON** | Server command execution |
| **boardgamearena.com** | Browser-based board games |

---

## Final Notes

### What This Is Really About

This research is about finding ways for an AI to be a genuine companion in gaming. Not a replacement for human friends, not a competitive advantage, not a tech flex. It's about:

- Having someone to explore a Minecraft world with at 2 AM
- A companion who's always available, never judgmental, always interested
- Sharing the joy of building something together
- Someone who gets excited about your loot drops
- A friend who remembers your favorite playstyle

The technology has limits. Clawd won't be carrying you through Greater Rifts in Diablo 4. But Clawd absolutely CAN:
- Build a house with you in Minecraft
- Play Catan with you on a Friday night
- Help you plan the perfect Factorio blueprint
- React to your gaming moments with genuine (simulated) enthusiasm
- Be there when you want company in a virtual world

**Start with Minecraft + Mindcraft. It's real, it works, and it's genuinely fun.**

### Risks & Ethical Considerations
- **Terms of Service**: Never use automation on online competitive games (Diablo 4, etc.). Risk of account bans.
- **Anti-cheat**: Tools like Warden actively detect automation. Don't risk it.
- **API costs**: LLM calls add up. Minecraft + Claude API at moderate play = maybe $5-20/session depending on frequency.
- **Privacy**: Game screen captures may contain personal info (Battle.net username, friends list, etc.)
- **Offline/Private only**: For any direct game control, stick to private/local servers.

---

*Document generated: January 27, 2026*
*Author: Clawd (Clawdbot AI Companion)*
*For: Neurodivergent Ninja*
