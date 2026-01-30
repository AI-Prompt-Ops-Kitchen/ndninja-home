# Talking Head Model Comparison for Neurodivergent Ninja Avatar

**Date:** 2026-01-28  
**Author:** Clawd (automated comparison)  
**GPU:** NVIDIA GPU via WSL2 on Steam PC (100.98.226.75)  
**Avatar:** Neurodivergent Ninja (3D stylized character with face mask covering lower face)

---

## Executive Summary

Both **Ditto TalkingHead** and **MuseTalk v1.5** are installed and functional on the Steam PC. Both models successfully produce output with the ninja avatar. However, **the ninja avatar's face mask fundamentally limits the value of both models** — the mouth is fully occluded by a black cloth mask, meaning lip-sync animation is invisible regardless of model quality.

**Recommendation:** Continue using **Ditto TalkingHead** for production. It produces cleaner output, better codec support (H.264), and handles the masked avatar without introducing artifacts. If the avatar design ever changes to expose the mouth, **MuseTalk v1.5** would be worth re-evaluating for its real-time performance advantage.

---

## Test Environment

| Component | Details |
|-----------|---------|
| Host | Steam PC via Tailscale (100.98.226.75) |
| Runtime | Docker containers on WSL2 (Ubuntu) |
| Ditto Docker | `ditto:latest` (22.6GB, PyTorch 2.1.2 + CUDA 12.1) |
| MuseTalk Docker | `musetalk:latest` (16GB, PyTorch 2.1.2 + CUDA 12.1) |
| Input Image | `ninja_avatar.jpg` (3D stylized ninja character) |
| Input Audio | Various `.wav` files (TTS-generated speech) |

---

## Model Overview

### Ditto TalkingHead (AntGroup)
- **Architecture:** Audio-driven portrait animation using HuBERT audio features
- **Face Detection:** MediaPipe face landmarker + InsightFace
- **Compositing:** Custom Cython blend extension with alpha compositing
- **Inference:** Single forward pass (not diffusion)
- **GitHub:** [antgroup/ditto-talkinghead](https://github.com/antgroup/ditto-talkinghead)

### MuseTalk v1.5 (Tencent Music / Lyra Lab)
- **Architecture:** Latent space inpainting using SD v1.4 UNet (NOT a diffusion model — single step)
- **Audio Processing:** OpenAI Whisper-tiny for audio embedding
- **Face Detection:** DWPose (MMPose) for landmarks, BiSeNet for face parsing
- **Training:** Perceptual loss + GAN loss + sync loss (v1.5 improvements)
- **GitHub:** [TMElyralab/MuseTalk](https://github.com/TMElyralab/MuseTalk)
- **Paper:** [arXiv 2410.10122](https://arxiv.org/abs/2410.10122)

### SadTalker (OpenTalker) — FAILED
- **Status:** Docker image installed (`wawa9000/sadtalker`, 22.2GB) but **non-functional** with ninja avatar
- **Issue:** Face detection fails entirely on the stylized 3D ninja character
- **Root Cause:** SadTalker's 3DMM-based approach requires detecting a realistic human face geometry; the ninja avatar's masked face + stylized proportions cause complete detection failure
- **Verdict:** Not viable for this avatar pipeline

---

## Output Comparison

### Video Metadata

| Property | Ditto | MuseTalk v1.5 |
|----------|-------|---------------|
| **Resolution** | 288 × 512 | 289 × 512 |
| **Frame Rate** | 25 fps | 25 fps |
| **Codec** | H.264 (High Profile) | MPEG-4 Part 2 (Simple Profile) |
| **Duration** | 36.6s (916 frames) | 8.8s (219 frames) |
| **File Size** | 1,028 KB | 614 KB |
| **Video Bitrate** | ~148 kbps | ~494 kbps |
| **Audio** | AAC LC, 16kHz mono | AAC LC, 16kHz mono |
| **Container** | MP4 (isom/avc1) | MP4 (isom) |

> **Note:** Different durations reflect different audio inputs, not rendering speed. MuseTalk's higher bitrate is due to MPEG-4 Part 2 being less efficient than H.264.

### MuseTalk on Real Face (Reference)

For context, MuseTalk's output on a real human face (sample `yongen` video):
- **Resolution:** 704 × 1216 (preserves source video resolution)
- **Face region:** 256 × 256 inpainting area
- **Quality:** High fidelity lip-sync with natural motion

This confirms MuseTalk works well on standard inputs — the ninja avatar is the challenge.

---

## Quality Analysis

### Visual Quality

| Aspect | Ditto | MuseTalk v1.5 |
|--------|-------|---------------|
| **Overall Sharpness** | Good — clean edges, consistent textures | Good upper face; slight softness in mask region |
| **Color Consistency** | Stable across frames | Minor tonal shifts in mask area |
| **Mask Boundary** | Clean hood-to-skin transition | Subtle blur/softness at mask-skin boundary |
| **Fabric Texture** | Maintains cloth detail in mask area | Mask area tends toward flat/featureless black |
| **Eye Region** | Sharp, well-animated | Sharp, well-rendered |
| **Temporal Stability** | Stable — no flickering observed | Stable — consistent frame-to-frame |

### Lip Sync Accuracy

**Neither model produces visible lip sync** because the ninja avatar's mouth is covered by a black cloth mask. This is the fundamental issue.

- **Ditto:** Animates the full face including subtle jaw/cheek movements that are partially visible above the mask line. The animation is conveyed through eye movement, brow motion, and slight head pose changes.
- **MuseTalk:** Inpaints the lower face region (256×256 area). With the mask covering this zone, the model essentially regenerates the mask area each frame, which introduces subtle artifacts (softness, texture loss) without any visible speech animation benefit.

### The Mask Problem (MuseTalk-Specific)

MuseTalk's face parsing pipeline identifies the lower face region and inpaints it with audio-driven content. For the ninja avatar:

1. **DWPose detects face landmarks** — works on the stylized avatar (confirmed by `ninja_avatar.pkl` output)
2. **BiSeNet segments the face** — identifies the skin vs. mask boundary
3. **Inpainting region covers the masked area** — the model regenerates the black mask region each frame
4. **Result:** Subtle blending artifacts at the mask boundary with no visible benefit

The MuseTalk README notes: *"We have found that upper-bound of the mask has an important impact on mouth openness."* — this mask configuration parameter was likely the source of the previously-reported "mask issue."

---

## Speed & Performance

| Metric | Ditto | MuseTalk v1.5 |
|--------|-------|---------------|
| **Claimed Speed** | Not specified | 30+ fps on V100 |
| **Real-time Capable** | No (batch inference) | Yes (realtime mode available) |
| **Model Size** | ~7.3 GB (Docker content) | ~4.8 GB (Docker content) |
| **GPU Memory** | Higher (PyTorch 2.5.1 + InsightFace) | Lower (single-step UNet) |
| **Batch Support** | Single inference | Configurable batch size |

MuseTalk has a significant **speed advantage** due to its single-step inpainting architecture vs. Ditto's multi-component pipeline. For real-time or near-real-time applications, MuseTalk would be preferred.

---

## Ease of Integration

### Ditto TalkingHead
- **Pros:**
  - Simple CLI: `python inference.py --audio_path X --source_path Y --output_path Z`
  - Single Docker container with all dependencies
  - Works with single image input (no video required)
  - H.264 output (universally compatible)
- **Cons:**
  - Requires downloading ~2.5GB of checkpoints separately
  - Complex build (Cython blend extension, InsightFace compilation)
  - PyTorch 2.5.1 upgrade adds container size
  - Limited documentation

### MuseTalk v1.5
- **Pros:**
  - YAML-based config for batch processing multiple tasks
  - Real-time inference mode available
  - Well-documented (paper, GitHub, HuggingFace)
  - Training code is open-sourced (fine-tuning possible)
  - Active development (training code released April 2025)
  - Supports video input (not just static images)
- **Cons:**
  - Requires MMLab ecosystem (mmcv, mmdet, mmpose) — complex dependency chain
  - MPEG-4 Part 2 output codec (older, less efficient)
  - Face parsing adds preprocessing overhead
  - bbox_shift tuning may be needed per-avatar

---

## Other Models Considered

### LivePortrait (Tencent ARC)
- **Status:** Not tested, but promising
- **Approach:** High-fidelity emotion-aware portrait animation
- **Pros:** Very high identity preservation, expressive motion, modern architecture
- **Cons:** GPU-heavy, requires careful tuning
- **Assessment:** Worth testing if avatar design changes. May handle stylized characters better due to its driver-based approach (can use reference video for motion).

### Wav2Lip
- **Status:** Not tested
- **Approach:** Classic lip-sync on existing video
- **Assessment:** Requires existing video footage — not suitable for single-image avatar pipeline

### GeneFace++
- **Status:** Not tested
- **Approach:** 3D-aware NeRF-based talking heads
- **Assessment:** Overkill for our use case. Better suited for photorealistic human faces with multi-camera setups.

### MakeItTalk
- **Status:** Not tested
- **Approach:** Lightweight audio-driven animation
- **Assessment:** Lower quality than Ditto/MuseTalk. Only worth considering for extreme speed requirements.

---

## Recommendation

### For Current Avatar (Ninja with Face Mask)

**Stick with Ditto TalkingHead.** Rationale:

1. **Neither model shows lip-sync** — the mask hides the mouth, so MuseTalk's speed advantage doesn't provide quality gains
2. **Ditto produces cleaner output** — no inpainting artifacts in the mask region
3. **Better codec** — H.264 vs. MPEG-4 Part 2
4. **Simpler pipeline** — fewer things to break, no face-parsing tuning needed
5. **Proven in production** — multiple successful outputs already generated

### If Avatar Design Changes (Exposed Mouth)

Re-evaluate with this priority:

1. **MuseTalk v1.5** — real-time speed + good quality lip-sync (proven on real faces)
2. **LivePortrait** — test for highest visual quality
3. **Ditto** — fallback if others have issues with stylized art

### For Maximum Quality (Future)

Consider training a **custom MuseTalk model** on the specific avatar style. MuseTalk's training code is now open-source (as of April 2025), making fine-tuning on stylized/3D-rendered characters feasible.

---

## Files Generated

| File | Description |
|------|-------------|
| `output/musetalk_comparison.mp4` | MuseTalk v1.5 ninja avatar output |
| `output/ditto_comparison.mp4` | Ditto TalkingHead ninja avatar output (e2e test) |
| `output/musetalk_sample_realface.mp4` | MuseTalk v1.5 with real human face (reference) |
| `output/musetalk_frame50.png` | Single frame from MuseTalk output |
| `output/ditto_frame50.png` | Single frame from Ditto output |
| `output/musetalk_frames_*.png` | Multi-frame MuseTalk sequence |
| `output/ditto_frames_*.png` | Multi-frame Ditto sequence |

---

## Appendix: Docker Images on Steam PC

```
IMAGE                                 DISK USAGE   CONTENT SIZE
ditto:latest                          22.6GB       7.31GB
musetalk:latest                       16GB         4.79GB
nvidia/cuda:12.1.0-base-ubuntu22.04   340MB        89.9MB
nvidia/cuda:12.1.1-base-ubuntu22.04   340MB        89.9MB
wawa9000/sadtalker:latest             22.2GB       9.14GB
```

## Appendix: Existing Ditto Outputs

Multiple Ditto renders already produced (in `/home/steam/ditto/output/`):
- `ninja_e2e_test.mp4` (1.0MB, 36.6s) — longest/most complete
- `ninja_army_of_2.mp4`, `ninja_army_of_2_v2.mp4` — dual-character tests
- `ninja_shadow_ops.mp4`, `ninja_shadow_ops_v2.mp4` — various audio tests
- `ninja_padded_v3.mp4`, `ninja_pro_voice.mp4` — voice quality iterations
