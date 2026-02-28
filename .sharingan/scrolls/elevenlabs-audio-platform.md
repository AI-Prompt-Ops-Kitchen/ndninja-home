---
name: elevenlabs-audio-platform
domain: AI/Audio
level: mangekyo
description: Complete ElevenLabs platform reference — TTS, Sound Effects API, voice design, expressiveness tags, audio isolation. Powers the entire Ninja content pipeline voice layer.
sources:
  - type: docs
    title: "ElevenLabs Models Reference"
    url: "https://elevenlabs.io/docs/overview/models"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "ElevenLabs TTS Best Practices & Voice Settings"
    url: "https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "Sound Effects API Reference (Create SFX)"
    url: "https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "Sound Effects Capabilities & Prompting Guide"
    url: "https://elevenlabs.io/docs/overview/capabilities/sound-effects"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "Sound Effects Quickstart Cookbook"
    url: "https://elevenlabs.io/docs/eleven-api/guides/cookbooks/sound-effects"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "Audio Isolation API Reference"
    url: "https://elevenlabs.io/docs/api-reference/audio-isolation/convert"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "ElevenLabs Python SDK (GitHub)"
    url: "https://github.com/elevenlabs/elevenlabs-python"
    date: "2026-02-24"
    confidence: high
  - type: docs
    title: "ElevenLabs TTS Overview & Output Formats"
    url: "https://elevenlabs.io/docs/overview/capabilities/text-to-speech"
    date: "2026-02-24"
    confidence: high
  - type: blog
    title: "ElevenLabs v3 Audio Tags Announcement"
    url: "https://elevenlabs.io/blog/v3-audiotags"
    date: "2026-02-24"
    confidence: high
  - type: article
    title: "ElevenLabs Pricing Breakdown (eesel.ai)"
    url: "https://www.eesel.ai/blog/elevenlabs-pricing"
    date: "2026-02-24"
    confidence: medium
  - type: code
    title: "Python SDK SFX Client Source"
    url: "https://github.com/elevenlabs/elevenlabs-python/blob/main/src/elevenlabs/text_to_sound_effects/client.py"
    date: "2026-02-24"
    confidence: high
last_updated: 2026-02-24
can_do_from_cli: true
cross_links:
  - remotion-video-code
  - dual-avatar-production
  - kokoro-tts
  - kling-avatar-api
---

# ElevenLabs Audio Platform

## Mental Model

ElevenLabs is a unified AI audio platform with four core products:
1. **Text-to-Speech (TTS)** — human-quality voice synthesis with emotional tags (powers all Ninja videos)
2. **Sound Effects (SFX)** — text-to-audio generation for whooshes, impacts, stings, ambient loops
3. **Voice Design & Cloning** — create custom voices from descriptions or audio samples
4. **Audio Isolation** — strip background noise from recordings (voice isolator)

Everything is billed via a **credits system** (formerly "characters"). TTS costs 1 credit/char for standard models, 0.5 credits/char for Turbo/Flash. SFX costs 40 credits/second of generated audio.

## Prerequisites

```bash
# Install SDK
pip install elevenlabs python-dotenv

# Environment variable
export ELEVENLABS_API_KEY="your_key_here"
# Or in .env file: ELEVENLABS_API_KEY=your_key_here
```

**Current pipeline:** API key loaded from `~/.env` via `get_api_keys()` in `ninja_content.py`.
**Voice ID:** `aQspKon0UdKOuBZQQrEE` (Neurodivergent Ninja Remix, used with eleven_v3).
**Model:** `eleven_v3` for all YouTube content.

---

## Core Workflows

### Workflow 1: Text-to-Speech (Current Pipeline)

The pipeline in `ninja_content.py` already handles TTS end-to-end:

```python
# Current production pattern (ninja_content.py line 556-567)
response = requests.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
    headers={
        "xi-api-key": keys['elevenlabs'],
        "Content-Type": "application/json"
    },
    json={
        "text": tagged_text,          # Script with [excited] etc. injected
        "model_id": "eleven_v3",
        "voice_settings": {
            "stability": 0.0,          # Creative mode for max expressiveness
            "similarity_boost": 0.85   # High to preserve voice identity
        }
    }
)
# Returns: raw MP3 bytes in response.content
```

**Post-processing chain** (lines 575-612):
1. Save raw MP3
2. `ffmpeg silenceremove` — trim pauses >0.6s down to 0.3s (prevents dead air)
3. `ffmpeg adelay` — add 0.5s padding at start (prevents first-word cutoff)
4. Cleanup temp files

**SDK alternative** (cleaner, supports streaming):
```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

audio = client.text_to_speech.convert(
    text="[excited] What's up my fellow Ninjas!",
    voice_id="aQspKon0UdKOuBZQQrEE",
    model_id="eleven_v3",
    output_format="mp3_44100_128",
    voice_settings={
        "stability": 0.0,
        "similarity_boost": 0.85
    }
)

# audio is Iterator[bytes] — write to file:
with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

**Async version:**
```python
from elevenlabs.client import AsyncElevenLabs

client = AsyncElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
audio = await client.text_to_speech.convert(
    text="[excited] Breaking news!",
    voice_id="aQspKon0UdKOuBZQQrEE",
    model_id="eleven_v3",
    output_format="mp3_44100_128",
)
```

### Workflow 2: Sound Effects Generation (NEW — for SFX Pipeline)

**This is the missing piece.** The content pipeline currently uses MCP-generated SFX which are weak. ElevenLabs SFX v2 produces professional 48kHz audio.

**API endpoint:**
```
POST https://api.elevenlabs.io/v1/sound-generation
Content-Type: application/json
xi-api-key: <your_key>
```

**Request body:**
```json
{
    "text": "Epic cinematic whoosh transition, fast and impactful",
    "duration_seconds": 2.0,
    "prompt_influence": 0.7,
    "model_id": "eleven_text_to_sound_v2",
    "loop": false
}
```

**Parameters:**
| Parameter | Type | Required | Range | Default | Notes |
|-----------|------|----------|-------|---------|-------|
| `text` | string | YES | — | — | Descriptive prompt for the sound |
| `duration_seconds` | float | no | 0.5–30 | auto | Leave empty for model to auto-detect ideal length |
| `prompt_influence` | float | no | 0.0–1.0 | 0.3 | Higher = more literal, lower = more creative |
| `model_id` | string | no | — | `eleven_text_to_sound_v2` | V2 is current best |
| `loop` | bool | no | — | false | Seamless loop (v2 only) |
| `output_format` | query | no | — | mp3_44100_128 | Same format options as TTS |

**Response:** Binary audio bytes (application/octet-stream), MP3 format.

**Cost:** 40 credits per second of generated audio. A 3-second whoosh = 120 credits.

**Python SDK pattern:**
```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs()

# Generate a transition whoosh
audio = client.text_to_sound_effects.convert(
    text="Fast cinematic whoosh, sci-fi style, short and punchy",
    duration_seconds=1.5,
    prompt_influence=0.7,
)

with open("whoosh.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

**Async SDK:**
```python
from elevenlabs.client import AsyncElevenLabs

client = AsyncElevenLabs()
audio = await client.text_to_sound_effects.convert(
    text="News broadcast intro sting, dramatic, 3 seconds",
    duration_seconds=3.0,
    prompt_influence=0.8,
)
```

**Pipeline integration snippet** (drop into ninja_content.py):
```python
def generate_sfx(prompt, output_path, duration=None, prompt_influence=0.7):
    """Generate a sound effect using ElevenLabs SFX v2."""
    keys = get_api_keys()
    payload = {
        "text": prompt,
        "prompt_influence": prompt_influence,
        "model_id": "eleven_text_to_sound_v2",
    }
    if duration:
        payload["duration_seconds"] = duration

    response = requests.post(
        "https://api.elevenlabs.io/v1/sound-generation",
        headers={
            "xi-api-key": keys['elevenlabs'],
            "Content-Type": "application/json"
        },
        json=payload
    )

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"   SFX saved: {output_path} ({os.path.getsize(output_path)/1024:.0f}KB)")
        return output_path
    else:
        print(f"   SFX error {response.status_code}: {response.text}")
        return None
```

**SFX prompt recipes for content pipeline:**
```python
SFX_LIBRARY = {
    "intro_whoosh":   "Fast cinematic whoosh, sci-fi style, punchy, 1 second",
    "outro_whoosh":   "Reverse whoosh with subtle reverb tail, smooth, 1.5 seconds",
    "news_sting":     "Short dramatic news broadcast intro sting, electronic, energetic",
    "impact_hit":     "Deep bass impact hit with sub-bass rumble, cinematic",
    "transition":     "Smooth glitch transition sound, digital, quick",
    "reveal":         "Epic reveal sound with rising tension then impact, dramatic",
    "subscribe_pop":  "Bright pop notification sound, friendly, short",
    "text_swoosh":    "Quick text swoosh animation sound, light and modern",
    "breaking_news":  "Urgent breaking news alert tone, broadcast style, tense",
    "ambient_tech":   "Subtle futuristic ambient hum, loopable, sci-fi dashboard",
}
```

### Workflow 3: Expressiveness & Performance Tags (v3 Audio Tags)

Audio tags are the PRIMARY expressiveness mechanism for `eleven_v3`. They are NOT spoken aloud — the model interprets them as stage directions for vocal performance.

**Syntax:** Place tags in square brackets before or inline with text.
```
[excited] What's up my fellow Ninjas!
I can't believe [gasps] they actually did it!
[whispers] But here's the real secret...
```

#### Complete Tag Reference

**Emotion Tags:**
- `[excited]` — high energy, enthusiastic (PRIMARY tag for Ninja content)
- `[calm]` — steady, controlled delivery
- `[sad]` — melancholy, subdued tone
- `[angry]` — intense, forceful delivery
- `[nervous]` — anxious, slightly shaky
- `[curious]` — questioning, wondering tone
- `[sarcastic]` — dry, ironic delivery
- `[frustrated]` — annoyed, exasperated
- `[sorrowful]` — deep sadness, grief
- `[mischievously]` — playful, scheming tone

**Reaction Tags:**
- `[laughs]` — natural laughter
- `[laughs harder]` — escalated laughter
- `[starts laughing]` — laughter building from speech
- `[wheezing]` — breathless laughter
- `[gasps]` — surprise reaction
- `[sighs]` — exhaustion or resignation
- `[exhales]` — breath release
- `[gulps]` — nervous swallow
- `[swallows]` — similar to gulps
- `[snorts]` — derisive or amused snort
- `[crying]` — emotional tears

**Delivery Tags:**
- `[whispers]` / `[whispering]` — quiet, intimate delivery
- `[slow]` — deliberately paced
- `[rushed]` — fast, urgent delivery
- `[stammers]` — hesitant, stumbling speech
- `[drawn out]` — elongated delivery
- `[pause]` — beat of silence
- `[dramatic tone]` — heightened theatrical delivery
- `[awe]` — wonder and amazement

**Sound Effect Tags (inline):**
- `[gunshot]` — firearm sound
- `[applause]` — clapping crowd
- `[clapping]` — hand claps
- `[explosion]` — boom effect

**Character / Accent Tags:**
- `[strong X accent]` — e.g., `[strong British accent]`, `[strong French accent]`
- `[pirate voice]` — themed character voice
- `[sings]` — switches to singing delivery
- `[woo]` — exclamation

#### What inject_expressive_tags() Currently Does (ninja_content.py lines 474-519)

The function auto-injects tags at key script points:
- **Intro lines** ("what's up", "hey ninja") → `[excited]`
- **Outro lines** ("thanks for watching", "peace out") → `[excited]`
- **Hype moments** ("just dropped", "huge news", "breaking") → `[excited]`
- **Skips** if any tags already present in script

**Known tags in the code:** `[excited]`, `[laughs]`, `[whispers]`, `[whispering]`, `[sighs]`, `[slow]`, `[gasps]`, `[calm]`, `[sad]`, `[angry]`, `[curious]`, `[nervous]`, `[sarcastic]`, `[pause]`

#### What's MISSING from inject_expressive_tags()

1. **No [gasps] injection** — the code defines it in `known_tags` but never injects it. Surprise/shock moments should get `[gasps]` (the docstring says it does, but the code only has `[excited]`).
2. **No variety** — every emotional moment gets `[excited]`. Should use `[curious]` for "but here's the thing" transitions, `[calm]` for closing thoughts.
3. **No [whispers]** injection — great for "secret" or "insider tip" moments.
4. **No [laughs]** injection — good for self-deprecating humor moments.
5. **No [pause]** for dramatic beats** — key reveals should have `[pause]` before the punchline.
6. **No [dramatic tone]** for ranking reveals** like "and the number one spot goes to..."
7. **Missing patterns:** "but wait", "plot twist", "here's the thing", "honestly", "no way"

**Recommended improvement:**
```python
# Add to inject_expressive_tags() after the hype/reveal block:

# Surprise / shock
elif any(p in lower for p in ["no way", "what?!", "are you kidding", "insane",
                               "unbelievable", "can't believe"]):
    tagged_lines.append(f"[gasps] {line.strip()}")
# Curiosity / transition
elif any(p in lower for p in ["but here's the thing", "what's interesting",
                               "the question is", "now here's where"]):
    tagged_lines.append(f"[curious] {line.strip()}")
# Whisper / secret
elif any(p in lower for p in ["secret", "insider", "between you and me",
                               "don't tell anyone"]):
    tagged_lines.append(f"[whispers] {line.strip()}")
# Dramatic pause before reveals
elif any(p in lower for p in ["number one", "the winner is", "the best part",
                               "drumroll"]):
    tagged_lines.append(f"[pause] [dramatic tone] {line.strip()}")
```

#### Stability Settings for Tag Effectiveness

| Setting | Value | Effect on Tags | When to Use |
|---------|-------|----------------|-------------|
| **Unhinged** | **0.15** | **Maximum emotional range, fangirl energy, screaming hype** | **Glitch freak-out moments, hype reactions** |
| Creative | 0.0 | Very high tag responsiveness, slight accent drift risk | Ninja standard delivery |
| Low Creative | 0.3 | Expressive but controlled, no artifacts | Sarcastic/deadpan Glitch, controlled anger |
| Natural | 0.5 | Balanced — tags work but delivery is steadier | Long-form narration |
| Robust | 1.0 | Tags barely register, very consistent | Audiobooks, corporate |

**IMPORTANT FINDING (Feb 27, 2026):** Stability 0.0 can cause accent drift (random Australian, static artifacts). For experimentation, **start at 0.15** and go lower only if needed. 0.15 gives the unhinged fangirl energy without the distortion.

**Per-character defaults:**
- **Ninja (standard):** stability 0.0, similarity 0.85 (proven in production)
- **Ninja (hype/breaking):** stability 0.15, similarity 0.85 — `[shouts]` only, NO `[screaming]` (causes audio artifacts on custom voice)
- **Ninja (angry/rant):** stability 0.15, similarity 0.85 — `[angry]` + `[shouts]` + `[sighs]`
- **Glitch (sarcasm/deadpan):** stability 0.3, similarity 0.75
- **Glitch (hype/freak-out):** stability 0.15, similarity 0.75 — `[screaming]` OK on Laura

**IMPORTANT (Feb 27, 2026):** `[screaming]` tag works on Laura (premade) but causes screeching artifacts on Ninja's custom voice at 0.15 stability. Stick to `[shouts]` for Ninja hype moments. Glitch can handle `[screaming]` fine.

#### Text Formatting Tricks (v3 only)

- **Ellipses (...)** — adds pauses and weight: `"And the winner is... [pause] Genshin Impact!"`
- **CAPS** — increases emphasis: `"This is ABSOLUTELY insane"`
- **Dashes (—)** — short pauses: `"The game — and I'm not exaggerating — is incredible"`
- **No SSML support** — v3 does NOT support `<break>` tags (v2 only)

#### MAX HYPE Formula (Validated Feb 27, 2026)

**CRITICAL FINDING:** Tags alone are NOT enough for high-energy delivery. A single `[excited]` at the start of a long sentence produces flat output — the energy fades after the first few words. The model needs constant reinforcement.

**The formula that works (tested A/B vs flat delivery):**

1. **Short punchy sentences** — break long lines into 5-8 word bursts
2. **CAPS on key words** — `TWO PULLS` not `two pulls`
3. **Tags every few words** — not just one at the start: `[excited] YO! [gasps] I just pulled— [excited] TWO PULLS!`
4. **Dashes (—) instead of ellipses (...)** — dashes create urgency, ellipses create contemplation
5. **Reaction tags mid-sentence** — `[gasps]`, `[laughs]`, `[laughs harder]`, `[wheezing]` between phrases
6. **Both speakers on Creative (stability 0.0)** — not just Ninja

**What DOESN'T work:**
- Single tag at start of a long line → energy dies after first 3 words
- Ellipses for hype moments → sounds contemplative, not excited
- Tags only at sentence boundaries → model treats them as one-shot direction
- Glitch on Natural (0.5) while using sarcasm/anger tags → too restrained

**Before (flat):**
```
[excited] So I just logged into WuWa for the 3.1 update... pulled for Luuk Herssen... and got him in TWO PULLS.
```

**After (max hype):**
```
[excited] YO! [gasps] I just logged into WuWa for 3.1— pulled for Luuk Herssen— [excited] and I got him in TWO PULLS! [laughs] TWO PULLS!
```

**Tag density rule of thumb:** At least one tag per 8-10 words for sustained energy. For freak-out moments, one tag per 4-5 words.

### Workflow 4: Voice Design & Cloning

**For future Glitch voice creation:**

```python
# Instant Voice Clone (IVC) — quick, from 1-3 audio samples
voice = client.voices.ivc.create(
    name="Glitch",
    description="Young Australian female, warm, nerdy, slightly playful",
    files=["./glitch_sample_1.mp3", "./glitch_sample_2.mp3"],
)
print(f"Voice ID: {voice.voice_id}")  # Use this in TTS calls

# Voice Design — generate from description (no samples needed)
# Uses model_id: eleven_ttv_v3 (Text to Voice v3)
audio = client.text_to_speech.convert(
    text="Hey there! I'm Glitch, your pocket ninja assistant.",
    voice_id="generated_voice_id",
    model_id="eleven_v3",
)
```

**Important for Glitch:** IVCs work better with v3 than Professional Voice Clones (PVCs). PVCs are "not fully optimized for Eleven v3" currently. Include emotional range in training samples.

**Current voice:** Laura (premade, `FGY2WhTYpPnrIDTdsKH5`) — locked in Feb 26, 2026.

#### Glitch Voice Recipes (Validated Feb 27, 2026)

**Winning configs by mood:**

| Mood | Stability | Tags | Example |
|------|-----------|------|---------|
| **Angry** (A-tier) | 0.3 | `[angry]`, `[shouts]`, `[sighs]` | `[angry] This is RIGGED! [shouts] TWO HUNDRED pulls and NOTHING! [sighs] Not even a four star.` |
| **Hype/Freak-out** (A-tier) | 0.15 | `[shouts]`, `[screaming]`, `[laughs harder]` | `[shouts] OH MY GOD OH MY GOD!! [screaming] A COLLAB?! [laughs harder] I CAN NOT— I literally CAN NOT right now!!` |
| **Sarcastic** (B+) | 0.3 | `[flatly]`, `[angry]`, `[sighs]` | `[flatly] Oh wonderful— another gacha banner. [angry] Because my wallet wasn't ALREADY crying! [sighs]` |
| **Deadpan** (B) | 0.3 | `[deadpan]`, `[sighs]` | `[deadpan] Oh great. Another banner I can not afford. [sighs] Shocking. Truly did not see that coming.` |

**What does NOT work for Glitch:**
- `[excited]` alone — sounds forced and fake on Laura. Use `[shouts]` or `[screaming]` instead
- `[gasps]` at start of hype lines — front-loads a weird intake that kills momentum
- `[laughs]` tacked onto the end — sounds unnatural. Use `[laughs harder]` mid-sentence instead
- `[playfully]` for hype — too restrained, sounds like a children's show host
- Stability 0.0 — accent drift (random Australian) and static artifacts on Laura
- Turbo v2.5 model — NO audio tag support, flat delivery, wrong model entirely

**What WORKS for Glitch:**
- `[shouts]` and `[angry]` are Laura's strongest tags — lean into these
- `[screaming]` for total freak-out moments — pair with stability 0.15
- `[flatly]` → `[angry]` pivot for sarcasm that escalates
- ALL CAPS + dashes for urgency: "I CAN NOT— I literally CAN NOT"
- Stability 0.15 for hype, 0.3 for sarcasm/anger (never 0.0 for Glitch)
- Keep variety: alternate v4-style ("OH MY GOD") and v5-style ("SHUT UP SHUT UP") openers

### Workflow 5: Audio Isolation (Voice Isolator)

Strip background noise from recordings. Useful for cleaning up recorded audio before processing.

```
POST https://api.elevenlabs.io/v1/audio-isolation
Content-Type: multipart/form-data
xi-api-key: <your_key>
```

**Request:** multipart form with `audio` file field.
**Supported formats:** WAV, MP3, FLAC, OGG, AAC.
**Response:** Clean audio bytes (application/octet-stream).

```python
# SDK pattern
result = client.audio_isolation.convert(audio=open("noisy.mp3", "rb"))
with open("clean.mp3", "wb") as f:
    for chunk in result:
        f.write(chunk)

# Or streaming version
result = client.audio_isolation.stream(audio=open("noisy.mp3", "rb"))
```

**Use case:** Clean up mobile recordings uploaded via the upload server before feeding to Kling avatar pipeline.

---

## API Reference — Complete Endpoint Table

| Endpoint | Method | Auth | Purpose | Response |
|----------|--------|------|---------|----------|
| `/v1/text-to-speech/{voice_id}` | POST | xi-api-key | Generate speech | MP3 bytes |
| `/v1/text-to-speech/{voice_id}/stream` | POST | xi-api-key | Stream speech | Chunked MP3 |
| `/v1/sound-generation` | POST | xi-api-key | Generate SFX | MP3 bytes |
| `/v1/audio-isolation` | POST | xi-api-key | Remove noise | Audio bytes |
| `/v1/audio-isolation/stream` | POST | xi-api-key | Stream clean audio | Chunked bytes |
| `/v1/voices` | GET | xi-api-key | List voices | JSON |
| `/v1/voices/ivc` | POST | xi-api-key | Clone voice (instant) | JSON |
| `/v1/models` | GET | xi-api-key | List models | JSON |

**Auth header:** `xi-api-key: <your_elevenlabs_api_key>`
**Base URL:** `https://api.elevenlabs.io`

---

## Voice Model Comparison

| Model ID | Name | Languages | Latency | Char Limit | Tags | Cost | Best For |
|----------|------|-----------|---------|------------|------|------|----------|
| `eleven_v3` | V3 | 70+ | Standard | 5,000 | YES (full) | 1 credit/char | YouTube content, expressive delivery |
| `eleven_multilingual_v2` | Multilingual V2 | 29 | Standard | 10,000 | Partial | 1 credit/char | Long-form, audiobooks, stable |
| `eleven_flash_v2_5` | Flash V2.5 | 32 | ~75ms | 40,000 | No | 0.5 credit/char | Real-time apps, conversational AI |
| `eleven_turbo_v2_5` | Turbo V2.5 | 32 | 250ms | 40,000 | No | 0.5 credit/char | Balanced speed+quality |
| `eleven_flash_v2` | Flash V2 | 1 (EN) | ~75ms | 30,000 | No | 0.5 credit/char | English-only real-time |
| `eleven_turbo_v2` | Turbo V2 | 1 (EN) | 250ms | 30,000 | No | 0.5 credit/char | English-only balanced |
| `eleven_monolingual_v1` | English V1 | 1 (EN) | — | — | No | — | DEPRECATED |
| `eleven_multilingual_v1` | Multi V1 | — | — | — | No | — | DEPRECATED |

**Special models:**
- `eleven_text_to_sound_v2` — Sound effects generation (40 credits/sec)
- `music_v1` — Music generation from text prompts
- `scribe_v2` — Speech-to-text transcription (90+ languages)
- `eleven_ttv_v3` — Text-to-Voice design (create voices from descriptions)

**Pipeline decision:** Use `eleven_v3` for ALL YouTube content. Use `eleven_turbo_v2_5` if you need fast drafts. Use Kokoro for free local drafts.

---

## Output Formats

| Format | Sample Rate | Bitrate | Quality | Notes |
|--------|-------------|---------|---------|-------|
| `mp3_22050_32` | 22.05kHz | 32kbps | Low | Smallest file |
| `mp3_44100_64` | 44.1kHz | 64kbps | Medium | Good for drafts |
| `mp3_44100_128` | 44.1kHz | 128kbps | High | **Pipeline default** |
| `mp3_44100_192` | 44.1kHz | 192kbps | Highest | Creator plan+ only |
| `pcm_16000` | 16kHz | 256kbps | Lossless | For further processing |
| `pcm_22050` | 22.05kHz | 352kbps | Lossless | Higher quality PCM |
| `pcm_24000` | 24kHz | 384kbps | Lossless | Good for Kling input |
| `pcm_44100` | 44.1kHz | 705kbps | Lossless | Studio quality |
| `ulaw_8000` | 8kHz | 64kbps | Phone | Telephony only |
| `opus_48000_*` | 48kHz | 32-192kbps | Variable | Web streaming |

---

## Pricing & Cost Optimization

### Plan Tiers (2026)

| Plan | Monthly | Credits/mo | Voices | Overage/1K chars |
|------|---------|------------|--------|-----------------|
| Free | $0 | 10,000 | 3 | N/A |
| Starter | $5 | 30,000 | 10 | N/A |
| Creator | $22 | 100,000 | 30 | $0.30 |
| Pro | $99 | 500,000 | 100 | $0.24 |
| Scale | $330 | 2,000,000 | 500 | $0.18 |
| Business | $1,320 | 11,000,000 | — | $0.12 |

**Unused credits roll over** for up to 2 months.

### Cost Per Video (typical Ninja Short ~130 words, ~700 characters)

| Component | Credits Used | Cost (Pro plan) |
|-----------|-------------|-----------------|
| TTS (v3, 700 chars) | 700 | ~$0.17 |
| Intro whoosh (1s SFX) | 40 | ~$0.01 |
| Outro whoosh (1.5s SFX) | 60 | ~$0.01 |
| News sting (2s SFX) | 80 | ~$0.02 |
| **Total per Short** | **~880** | **~$0.21** |

On Pro plan (500K credits/mo), that's ~568 Shorts per month — more than enough.

### Cost Optimization Tips

1. **Turbo/Flash models cost 50% less** (0.5 credit/char) — use for drafts
2. **Don't specify SFX duration** unless needed — auto-detect often produces tighter clips
3. **Cache generated SFX** — whooshes/transitions are reusable, generate once
4. **Pre-build an SFX library** rather than generating per video
5. **Use Kokoro for draft TTS** ($0), ElevenLabs only for final render

---

## Current Pipeline Integration Analysis

### What ninja_content.py Already Does Well

1. **Voice style presets** (expressive/natural/calm) with correct v3 stability values
2. **Auto-injects tags** via `inject_expressive_tags()` — adds `[excited]` at intros/outros/hype
3. **Post-processing** — silence trimming + start padding prevents audio issues
4. **Raw requests.post** — works, but doesn't leverage SDK streaming/retry

### What's Missing / Needs Improvement

1. **No SFX generation** — entirely absent from pipeline. Need `generate_sfx()` function
2. **Tag variety** — only `[excited]` is injected. Missing `[gasps]`, `[curious]`, `[whispers]`, `[pause]`
3. **No SDK usage** — raw HTTP instead of `elevenlabs` SDK (no retry, no streaming, no async)
4. **No output_format param** — defaults to whatever API returns instead of explicit `mp3_44100_128`
5. **No SFX caching** — should build a library of common SFX and reuse
6. **No dual-voice support** — Glitch needs separate voice_id routing
7. **Long-form chunking** — no `previous_request_id` for maintaining prosody across segments

### Recommended Pipeline Additions

```python
# 1. Add to ninja_content.py imports
from pathlib import Path

# 2. SFX cache directory
SFX_CACHE = Path("/home/ndninja/assets/sfx_cache")
SFX_CACHE.mkdir(exist_ok=True)

# 3. Generate or load cached SFX
def get_sfx(name, prompt, duration=None):
    """Get SFX from cache or generate new."""
    cache_path = SFX_CACHE / f"{name}.mp3"
    if cache_path.exists():
        return str(cache_path)
    return generate_sfx(prompt, str(cache_path), duration=duration)

# 4. Dual-voice routing
VOICE_MAP = {
    "ninja": "aQspKon0UdKOuBZQQrEE",   # Neurodivergent Ninja Remix
    "glitch": "PLACEHOLDER_GLITCH_ID",    # TBD — Laura or custom clone
}
```

---

## Integration Points

### Content Pipeline (ninja_content.py)
- **TTS:** `generate_tts()` — production-ready, uses v3 + Creative stability
- **SFX:** TODO — add `generate_sfx()` using the pattern above
- **Tags:** `inject_expressive_tags()` — expand tag variety

### Dual-Anchor Format
- **Ninja voice:** `aQspKon0UdKOuBZQQrEE` with eleven_v3
- **Glitch voice:** Laura (placeholder) or custom IVC
- **SFX between segments:** news sting, transition swooshes
- **Per-anchor TTS calls:** separate `generate_tts()` call per character

### Glitch Project
- **Voice creation:** IVC from recorded samples (Australian accent direction)
- **Expressiveness:** v3 tags for emotional responses (crisis mode, celebration, frustration)
- **Low-latency option:** `eleven_turbo_v2_5` for real-time Glitch responses

### Kokoro TTS Decision Matrix
| Scenario | Use | Why |
|----------|-----|-----|
| YouTube Shorts | ElevenLabs v3 | Expressiveness + tags = viewer retention |
| Draft audio review | Kokoro | Free, instant, good enough for preview |
| Sharingan podcast digests | Kokoro | Free, not audience-facing |
| Glitch desktop notifications | Kokoro | Low-latency, free |
| Glitch voice conversations | ElevenLabs Turbo v2.5 | Quality + speed balance |
| Dual-anchor video | ElevenLabs v3 | Needs emotional range for both characters |

---

## Limitations & Gaps

- **v3 char limit:** 5,000 characters per request (split long scripts into segments)
- **No SSML in v3:** `<break>` tags only work in v2 models. Use `...` and `—` for pauses in v3
- **PVC quality on v3:** Professional Voice Clones not fully optimized yet — use IVC
- **SFX v2 max duration:** 30 seconds per generation
- **SFX credit cost:** 40 credits/second adds up for longer ambient tracks — use looping
- **Tags are suggestions:** Effectiveness varies by voice. Some voices respond better to certain tags
- **No guaranteed reproducibility:** Even with seed parameter, subtle variations persist
- **Rate limits:** Depend on plan tier (not publicly documented per-endpoint)

---

## Tips & Best Practices

### TTS Quality
1. **Always use Creative stability (0.0) for YouTube** — maximum tag responsiveness
2. **Keep similarity_boost high (0.8+)** when using Creative to preserve voice identity
3. **Include emotional context in the script itself** — "she said nervously" type cues help even without tags
4. **Punctuation matters in v3** — periods create full stops, commas create brief pauses, ellipses add weight
5. **CAPS for emphasis** — "This is ABSOLUTELY incredible" hits differently than lowercase

### SFX Quality
1. **Use audio terminology** in prompts: "whoosh", "braam", "sting", "impact", "ambient", "foley"
2. **Be specific:** "Heavy wooden door creaking open slowly" beats "door sound"
3. **Higher prompt_influence (0.7+)** for predictable results, lower for creative exploration
4. **Generate components separately** and combine in FFmpeg for complex soundscapes
5. **Use looping** for ambient backgrounds (tech hum, crowd noise) — saves credits vs long generations

### Pipeline Architecture
1. **Pre-generate an SFX library** of 10-15 common sounds, cache them, reuse across videos
2. **Use SDK for new code** — retry logic, streaming, proper error handling built in
3. **Async generation** — generate TTS and SFX in parallel when building video
4. **Specify output_format explicitly** — `mp3_44100_128` for consistency
5. **For long-form:** Use `previous_request_id` parameter to chain segments with natural prosody
