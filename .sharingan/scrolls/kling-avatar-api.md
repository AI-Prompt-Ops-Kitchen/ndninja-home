# Kling Avatar & Video API — Sharingan Scroll
**Mastery:** 3-Tomoe (production-tested, comprehensive reference)
**Last updated:** 2026-02-23
**Sources:** fal.ai API docs, fal.ai developer guide, fal.ai prompt guide, Kling 3.0 prompting guide, Kling 3.0 launch blog, klingai.com pricing, TeamDay model comparison, SelectHub HeyGen vs Kling, WaveSpeed Synthesia comparison
**Sources count:** 9

---

## Overview
Kling is an AI video generation platform by Kuaishou. fal.ai provides exclusive API access. We use Avatar v2 Pro for the Neurodivergent Ninja content pipeline — generating talking-head avatar videos from a reference image + audio.

## Model Lineup & Pricing (Feb 2026)

| Model | Endpoint | $/sec | Resolution | FPS | Best For |
|-------|----------|-------|------------|-----|----------|
| **Avatar v2 Standard** | `fal-ai/kling-video/ai-avatar/v2/standard` | $0.056 | 720p | 30 | Draft previews, testing |
| **Avatar v2 Pro** | `fal-ai/kling-video/ai-avatar/v2/pro` | $0.115 | 1080p | 48 | **Production renders** |
| **i2v v2.6 Pro** | `fal-ai/kling-video/v2.6/pro/image-to-video` | $0.07 (no audio) / $0.14 (audio) | 1080p | — | Reaction clips, B-roll |
| **O3 Standard** | `fal-ai/kling-video/o3/standard/text-to-video` | $0.168 (no audio) / $0.224 (audio) | 1080p | — | Multi-character scenes |
| **O3 Pro** | `fal-ai/kling-video/o3/pro/text-to-video` | $0.28 (audio) / $0.392 (voice ctrl) | 1080p+ | — | Cinematic multi-char |

### Cost Calculator (Common Scenarios)
| Scenario | Duration | Cost |
|----------|----------|------|
| 1 Short (60s) — Avatar Pro | 60s | ~$6.90 |
| 1 Short (60s) — Avatar Standard | 60s | ~$3.37 |
| Dual-anchor segment (7s) | 7s speaker + 7s listener | ~$1.29 |
| Dual-anchor Short (75s, ~10 segments) | 75s | ~$12.90 |
| Single test clip (10s) — Standard | 10s | ~$0.56 |

## API Parameters (Avatar v2)

| Param | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `image_url` | string | YES | — | Public URL (use `fal_client.upload()`) |
| `audio_url` | string | YES | — | MP3/WAV/AAC, max 5MB, 2-60s |
| `prompt` | string | no | `"."` | Expression/animation guidance |
| `duration` | enum | no | `"5"` | `"5"` or `"10"` seconds |
| `aspect_ratio` | enum | no | `"16:9"` | `"16:9"`, `"9:16"`, `"1:1"` |
| `negative_prompt` | string | no | `"blur, distort, and low quality"` | What to avoid |
| `cfg_scale` | float | no | `0.5` | Classifier Free Guidance strength |

## Complete Python Examples

### Production Pattern (Sync with Logging)
```python
import fal_client
import httpx

# Upload local files (returns reusable URLs — upload once, use many times)
image_url = fal_client.upload(open("avatar.jpg", "rb").read(), "image/jpeg")
audio_url = fal_client.upload(open("speech.mp3", "rb").read(), "audio/mpeg")

EXPRESSIVENESS_PROMPT = (
    "Animated Pixar character speaking enthusiastically to camera. "
    "Expressive digital LED eyes that blink naturally, widen with excitement, "
    "and squint when smiling. Lively head movements and natural micro-expressions. "
    "Energetic YouTuber presentation style."
)

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(f"  [{log['message']}]")

result = fal_client.subscribe(
    "fal-ai/kling-video/ai-avatar/v2/pro",
    arguments={
        "image_url": image_url,
        "audio_url": audio_url,
        "prompt": EXPRESSIVENESS_PROMPT,
        "aspect_ratio": "9:16",       # Shorts format
        "negative_prompt": "blur, distort, low quality, stiff, robotic",
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
video_url = result["video"]["url"]
print(f"Video: {video_url} ({result['duration']}s)")

# Download the result
resp = httpx.get(video_url)
with open("output.mp4", "wb") as f:
    f.write(resp.content)
```

### Parallel Batch Pattern (Non-Blocking)
```python
import fal_client

segments = [
    {"audio": "seg1.mp3", "prompt": "Excited presenter..."},
    {"audio": "seg2.mp3", "prompt": "Thoughtful pause..."},
    {"audio": "seg3.mp3", "prompt": "Energetic closing..."},
]

# Fire all at once — fal_client.submit() is non-blocking
handles = []
for seg in segments:
    audio_url = fal_client.upload(open(seg["audio"], "rb").read(), "audio/mpeg")
    handle = fal_client.submit(
        "fal-ai/kling-video/ai-avatar/v2/pro",
        arguments={
            "image_url": image_url,  # reuse cached upload
            "audio_url": audio_url,
            "prompt": seg["prompt"],
            "aspect_ratio": "9:16",
        },
    )
    handles.append(handle)

# Collect all results (blocks per handle, but they run in parallel on fal)
results = [h.get() for h in handles]
```

### Webhook Pattern (Fire and Forget)
```python
import fal_client

result = fal_client.submit(
    "fal-ai/kling-video/ai-avatar/v2/pro",
    arguments={
        "image_url": image_url,
        "audio_url": audio_url,
        "prompt": "Expressive Pixar character...",
    },
    webhook_url="https://your-app.com/api/kling-callback",
)
request_id = result.request_id  # Store this to match the callback
```

## Image & Audio Requirements

**Image:** Min 512x512px, face 60-70% of frame, even lighting, minimal shadows, front-facing or slight angle. PNG/JPG/WebP.

**Audio:** Clear speech, minimal background noise. MP3/WAV/AAC. Optimal 5-30s clips. Natural pacing = better lip sync. Pair with ElevenLabs v3 for best results.

## Prompt Engineering (CRITICAL for Quality)

### Our Proven Expressiveness Prompt
```
Animated Pixar character speaking enthusiastically to camera. Expressive digital LED
eyes that blink naturally, widen with excitement, and squint when smiling. Lively head
movements and natural micro-expressions. Energetic YouTuber presentation style.
```
**Without:** Dead digital stare, no blinking = uncanny valley.
**With:** Character blinks, emotes, feels alive = massive quality upgrade.
**REQUIRES Pro model** — Standard lacks the expressiveness fidelity.

### The 4-Component Framework
1. **Subject** — Character context ("Animated Pixar ninja at gaming news desk")
2. **Expression** — Emotional range ("friendly, engaging, occasional surprised reactions")
3. **Movement** — Animation intensity ("subtle head movements, natural nodding, eye contact")
4. **Style** — Source aesthetics ("preserve the 3D render quality and digital goggles")

### Category-Specific Templates

| Use Case | Prompt Template |
|----------|----------------|
| **Gaming News (ours)** | "Animated Pixar character speaking enthusiastically to camera. Expressive digital LED eyes that blink naturally. Energetic YouTuber presentation style." |
| **Reaction/Listening** | "Animated Pixar character seated at desk listening attentively. Mouth closed, subtle nodding, natural blinking, occasional smile. Relaxed but engaged." |
| **Corporate** | "Professional trainer with clear articulation, occasional gestures emphasizing key points, maintain eye contact for engagement." |
| **Educational** | "Patient, encouraging teacher with thoughtful pauses after complex info, subtle nods when transitioning topics." |
| **Cartoon/2D** | "Expressive, exaggerated movements typical of 2D animation, clean line preservation." |

### Advanced Techniques
- **Emotional Transitions:** "Begin neutral, transition to excitement (00:15-00:30), show empathy (00:45-01:10)"
- **Character Consistency:** "Confident posture, slight head tilt when questioning, occasional eyebrow raise"
- **Hands:** Specify "hands below frame" or "hands out of shot" — full-body motion is unreliable
- **Negative Prompt:** Always add `"stiff, robotic"` to default negative prompt for avatar work

### Prompt Mistakes to Avoid
- Contradictory instructions (serious + frequent smiling)
- Over-specification (max 3-5 aspects per prompt)
- Vague terms ("good/nice" instead of "professional/enthusiastic/contemplative")
- Prompting for hand gestures (unreliable, often distorted)
- Ignoring source image context (prompt must complement the image)

## Reaction/Idle Clips (Non-Speaking Character)

### Problem
Avatar v2 is audio-driven — passing speaker audio to listener causes phantom mouth movement.

### Solution: Image-to-Video (NOT Avatar)
Use `fal-ai/kling-video/v2.6/pro/image-to-video` with `generate_audio=false`.

```python
result = fal_client.subscribe(
    "fal-ai/kling-video/v2.6/pro/image-to-video",
    arguments={
        "prompt": "Animated Pixar character seated at desk listening. Mouth closed, "
                  "subtle nodding, natural blinking, amused expression.",
        "start_image_url": character_image_url,
        "duration": "5",
        "generate_audio": False,
        "negative_prompt": "blur, distort, low quality, talking, speaking, mouth movement",
    },
)
```
**Key:** Add "mouth closed" to prompt AND "talking, speaking, mouth movement" to negative prompt.

## Dual-Anchor Pipeline (Composite Approach)

1. **Speaker:** Avatar v2 Pro (audio-driven lip sync + expressiveness prompt)
2. **Listener:** i2v v2.6 Pro (prompt-driven reaction, generate_audio=false)
3. **Composite:** `ffmpeg -i speaker.mp4 -i listener.mp4 -filter_complex hstack -map 0:a out.mp4`
4. **Concat:** `ffmpeg -f concat -i segments.txt -c copy final.mp4`

**Cost per dual segment (~7s):** Speaker $0.80 + Listener $0.49 = ~$1.29

## Kling 3.0 / O3: Text-to-Video Only (NOT Avatar)

**IMPORTANT: Kling 3.0/O3 does NOT have an Avatar endpoint.** Avatar lip-sync remains at v2. The v3/O3 models are text-to-video and image-to-video only.

### Confirmed Endpoints (Feb 2026)

| Model | Endpoint | Status |
|-------|----------|--------|
| **Avatar v2 Standard** | `fal-ai/kling-video/ai-avatar/v2/standard` | Active (production) |
| **Avatar v2 Pro** | `fal-ai/kling-video/ai-avatar/v2/pro` | Active (production) |
| **Avatar v3 (any)** | `fal-ai/kling-video/ai-avatar/v3/*` | **DOES NOT EXIST** (404) |
| **O3 Standard t2v** | `fal-ai/kling-video/o3/standard/text-to-video` | Active |
| **O3 Pro t2v** | `fal-ai/kling-video/o3/pro/text-to-video` | Active |
| **V3 Standard t2v** | `fal-ai/kling-video/v3/standard/text-to-video` | Active |

### What V3/O3 Actually Offers
- **Multi-character coreference:** 3+ characters in same scene without face/outfit blending
- **Element referencing:** Upload reference images; model extracts traits + appearance
- **Voice control syntax:** `[Character A, raspy deep voice]: "dialogue here"`
- **Multi-shot storyboarding:** Up to 6 shots in single output, up to 15s
- **Native audio:** Lip sync built-in (Chinese, English, Japanese, Korean, Spanish)
- **Exclusive to fal.ai** — not available on other API platforms

### V3/O3 Pricing

| Model | $/sec (no audio) | $/sec (audio) | $/sec (voice ctrl) |
|-------|-------------------|---------------|---------------------|
| O3 Standard | $0.168 | $0.224 | — |
| O3 Pro | $0.28 | — | $0.392 |
| V3 Standard | TBD | TBD | TBD |

### Kling 3.0 Prompt Style
Write prompts like **scene direction**, not object lists:
```
[Ninja, energetic male voice]: "Breaking news from the gaming world!"
Camera pulls back to reveal the full news desk.
[Glitch, amused feminine voice]: "Tell me more, this sounds exciting."
```

### Kling 3.0 for Dual-Anchor: NOT YET

**Verdict:** V3/O3 lip sync is **prompt-driven** (text directions → model generates mouth movement). Our pipeline is **audio-driven** (real TTS audio → precise lip sync). Prompt-driven sync quality is unpredictable — it generates speech from text, it doesn't match to pre-recorded audio.

**When to reconsider:**
- If fal.ai releases Avatar v3 with audio-driven lip sync
- If O3 adds an `audio_url` parameter for external audio matching
- If prompt-driven sync quality reaches parity with audio-driven (test periodically)

**Current best path:** Stay on Avatar v2 Pro for both anchors. V3/O3 is useful for B-roll cinematics, not avatar lip-sync.

### Note on Higsfield
Higsfield (sometimes cited as a separate avatar model) wraps Kling underneath — it is NOT a distinct model. No separate API endpoint needed.

## fal.ai Avatar Model Comparison (Feb 2026)

### A/B Test Results — OmniHuman v1.5 vs Kling v2 Pro (Feb 24, 2026)

**Tested with both OG masked ninja AND new desk presenter (visible mouth) avatars.**

| Factor | **Kling v2 Pro** (WINNER) | **OmniHuman v1.5** | **Creatify Aurora** | **VEED Fabric 1.0** |
|--------|:---:|:---:|:---:|:---:|
| **Endpoint** | `fal-ai/kling-video/ai-avatar/v2/pro` | `fal-ai/bytedance/omnihuman/v1.5` | `creatify/aurora` | `veed/fabric-1.0` |
| **Price/sec** | $0.115 | $0.16 (+39%) | $0.10-0.14 | $0.08-0.15 |
| **Max Resolution** | 1080p | 1080p | 720p | 720p |
| **Max Duration** | No hard cap | **30s @1080p** / 60s @720p | ~60s | **30s** |
| **Speed** | ~215s (test) | ~166s (test) | Slow (3/5) | Fastest (5/5) |
| **Lip Sync** | Proven good | Good (4/5) | Best (5/5) | Good (4/5) |
| **Body Movement** | Good | Best (5/5) | Good | Limited |
| **Emotion** | Good (Pro mode) | Best (5/5) | Very good | Moderate |
| **Cartoon/Pixar** | **Proven** | Strong, but mouth artifacts on masked chars | Uncertain (ad-focused) | Explicitly strong |
| **Dual Character** | No | Yes (audio driving) | No | No |
| **FPS** | 30 | 25 | 24 | Standard |

**Test clips saved:** `output/omnihuman_avatar_test.mp4`, `output/kling_avatar_test.mp4`, `output/omnihuman_newdesign_avatar_test.mp4`, `output/kling_newdesign_avatar_test.mp4`

### Key Findings

1. **Image quality is dead even** — side-by-side with the new desk presenter design, no visible quality difference between OmniHuman and Kling Pro
2. **OmniHuman adds phantom mouth to masked characters** — it hallucinated a lip onto the OG ninja mask. Not usable with the masked avatar
3. **Movement slightly better on OmniHuman** but not enough to justify the cost premium
4. **30-second cap at 1080p is a dealbreaker** — our 60s Shorts would need stitching, adding pipeline complexity for zero quality gain
5. **OmniHuman's dual-character feature is interesting** for news desk format, but the 30s cap makes it impractical for production

### Verdict
**Stick with Kling v2 Pro.** The $0.045/sec savings, no duration cap, and proven cartoon character support outweigh OmniHuman's marginal movement advantage. Revisit if ByteDance lifts the 30s@1080p cap.

### When to Reconsider
- **OmniHuman:** If duration cap increases to 60s+ at 1080p, worth retesting for dual-anchor format
- **Aurora:** If they add documented cartoon/stylized character support
- **Fabric:** Useful as cheap draft mode ($0.08/sec @480p) if rapid prototyping needed, but 30s cap blocks production use

## Platform Comparison (Feb 2026)

| Platform | Strengths | Weaknesses | Price |
|----------|-----------|------------|-------|
| **Kling (via fal.ai)** | Best for animation/cartoon, API-first, pay-per-use | No built-in editor, API-only | $0.056-0.392/sec |
| **HeyGen** | Avatar IV hyper-realism, 175+ languages, real-time translate | Subscription model, less flexible for cartoon | $24-180/mo |
| **Synthesia** | Enterprise SOC2, 140+ languages, SCORM export | Expensive, enterprise focus | $22-67/mo |
| **JoggAI** | Native dual avatar, ElevenLabs integration | Newer platform, less proven | Varies |

**Our choice:** Kling via fal.ai — cartoon avatar support, pay-per-use API, proven in production.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 400 | Invalid/inaccessible URLs | Use `fal_client.upload()` for local files |
| 401 | Bad API key | Check `FAL_KEY` env var |
| 429 | Rate limited | Exponential backoff: `time.sleep(2 ** attempt)` |
| 504 | Timeout on long gen | Use webhook or `fal_client.submit()` pattern |
| Poor lip sync | Noisy audio | Clean audio, use ElevenLabs v3 |
| Stiff animation | Missing prompt | Add expressiveness prompt (see above) |
| Dead eyes | Using Standard model | Switch to Pro — Standard can't do expressive |

## Cost Optimization Cheat Sheet

1. **Test with Standard** ($0.056/sec) — upgrade to Pro ($0.115/sec) for final only
2. **Test with 10s clips** before full-length renders
3. **Cache image uploads** — `fal_client.upload()` returns reusable URLs
4. **Parallel submit** — `fal_client.submit()` fires concurrent jobs on fal
5. **Batch segment renders** — fire all segments at once, collect results
6. **Pro is 2x Standard** but expressiveness prompt only truly shines on Pro
7. **Reaction clips via i2v** ($0.07/sec) are cheaper than Avatar Pro ($0.115/sec)

## Integration Points (Our Pipeline)

| Component | Value |
|-----------|-------|
| **Pipeline script** | `/home/ndninja/scripts/ninja_content.py` → `generate_kling_avatar_video()` |
| **Voice** | ElevenLabs v3, voice ID `aQspKon0UdKOuBZQQrEE` |
| **OG Avatar** | `/home/ndninja/assets/reference/ninja_helmet_v4_hires.jpg` |
| **New Avatar** | `/home/ndninja/uploads/IMG_2411.jpeg` (desk presenter, needs Pro) |
| **Env var** | `FAL_AI_API_KEY` or `FAL_KEY` |
| **Aspect ratio** | `9:16` for Shorts, `16:9` for long-form |
