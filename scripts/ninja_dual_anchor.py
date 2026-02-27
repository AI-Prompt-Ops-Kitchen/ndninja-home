#!/usr/bin/env python3
"""
Ninja News Network — Dual Anchor Pipeline (Dual-Render)

Two Pixar-style AI avatars (Ninja + Glitch) at a news desk trading gaming
news commentary. Uses three camera angles like a real broadcast:
  - Right angle: Ninja prominent (used when Ninja speaks)
  - Left angle:  Glitch prominent (used when Glitch speaks)
  - Center:      Both equal (used for opens, reactions, transitions)

DUAL-RENDER: Each character is cropped from the reference image, rendered
separately via parallel Kling Avatar v2 sessions (speaker with audio,
listener with silent WAV), then composited back onto the original artwork.
This eliminates ghost mouthing and body artifacts completely.

Pipeline: Parse dialogue → TTS per line → select camera angle →
          crop characters → parallel Kling renders → composite → concat

Usage:
    python3 ninja_dual_anchor.py --script-file dialogue.txt --output ninja_dual
    python3 ninja_dual_anchor.py --script-file dialogue.txt --single-render
"""

import argparse
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import wave
from datetime import datetime
from pathlib import Path

# Add scripts dir to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from ninja_content import (
    generate_tts,
    generate_kling_avatar_video,
    get_audio_duration,
    inject_expressive_tags,
)

# ---------------------------------------------------------------------------
# Character Configuration
# ---------------------------------------------------------------------------
CHARACTERS = {
    "NINJA": {
        "name": "Ninja",
        "voice_id": "aQspKon0UdKOuBZQQrEE",
        "voice_style": "expressive",
    },
    "GLITCH": {
        "name": "Glitch",
        "voice_id": "FGY2WhTYpPnrIDTdsKH5",  # Laura — premade, sassy/quirky, consistent
        "voice_style": "natural",
    },
}

# ---------------------------------------------------------------------------
# Multi-Angle Camera Setup — update paths when artwork is ready
# ---------------------------------------------------------------------------
# Layout: Glitch sits LEFT, Ninja sits RIGHT at the news desk
CAMERA_ANGLES = {
    # Right-angle POV: Ninja is prominent (foreground right), Glitch background left
    # → Use when NINJA speaks
    "NINJA_SPEAKS": str(Path.home() / "uploads" / "IMG_2419.jpeg"),

    # Left-angle POV: Glitch is prominent (foreground left), Ninja background right
    # → Use when GLITCH speaks
    "GLITCH_SPEAKS": str(Path.home() / "uploads" / "IMG_2425.jpeg"),  # 9:16 portrait (watermark-free)

    # Left-angle landscape variant (for future long-form 16:9)
    "GLITCH_SPEAKS_LANDSCAPE": str(Path.home() / "uploads" / "IMG_2424.jpeg"),  # 16:9 landscape (watermark-free)

    # Center straight-on: Both characters equal, full desk view
    # → Use for opening shot, transitions, reactions
    # Portrait (9:16) for Shorts, landscape (16:9) for long-form
    "CENTER": str(Path.home() / "uploads" / "IMG_2423.jpeg"),         # 9:16 portrait
    "CENTER_LANDSCAPE": str(Path.home() / "uploads" / "IMG_2426.jpeg"),  # 16:9 landscape (watermark-free)
}

# Prompts per camera angle — describes both characters in scene
ANGLE_PROMPTS = {
    "NINJA_SPEAKS": (
        "Two animated Pixar characters at a news desk. The ninja character on the right "
        "is speaking enthusiastically to camera with expressive digital LED eyes that blink "
        "naturally, widen with excitement, and squint when smiling. Lively head movements. "
        "The cyberpunk girl on the left listens and reacts with subtle nods. "
        "Arms and hands resting flat on desk, stable body posture. "
        "Professional broadcast studio. Static camera, stable framing."
    ),
    "GLITCH_SPEAKS": (
        "Two animated Pixar characters at a news desk. The cyberpunk girl on the left "
        "is speaking cheerfully to camera with expressive pink-tinted goggles, natural "
        "blinking, playful head movements. Fun energetic delivery. "
        "The ninja character on the right listens with engaged expression. "
        "Arms and hands resting flat on desk, stable body posture. "
        "Professional broadcast studio. Static camera, stable framing."
    ),
    "CENTER": (
        "Two animated Pixar characters at a news desk, center-framed wide shot. "
        "Both characters are equally visible and engaged. The ninja on the right and "
        "cyberpunk girl on the left are both animated with natural blinking, subtle "
        "movements, and expressive reactions. Arms and hands resting flat on desk, "
        "stable body posture. Professional broadcast studio. Static camera, stable framing."
    ),
}

# Negative prompt — prevents body artifacts, arm clipping, desk reflections
NEGATIVE_PROMPT = (
    "blur, distort, low quality, stiff, robotic, body distortion, clipping, "
    "melting limbs, morphing arms, arm through surface, arm through desk, "
    "warped reflections, distorted hands"
)

# Listener-specific negative prompt — also prevents ghost mouthing
LISTENER_NEGATIVE_PROMPT = (
    "blur, distort, low quality, stiff, robotic, body distortion, clipping, "
    "melting limbs, morphing arms, arm through surface, arm through desk, "
    "warped reflections, distorted hands, "
    "talking, speaking, open mouth, lip movement, mouth open, mouthing words, lip sync"
)

# CFG scale — higher = stricter prompt adherence (helps with body stability)
CFG_SCALE = 0.7
LISTENER_CFG_SCALE = 0.9  # Higher for listener to enforce closed mouth

# ---------------------------------------------------------------------------
# Video Chat Format Configuration
# ---------------------------------------------------------------------------
# Wife's genius idea (Feb 24, 2026): Stack characters vertically like a
# FaceTime/Zoom call instead of side-by-side news desk. Eliminates seam
# problem entirely. Each character is a fully independent render.

VIDEOCHAT_NINJA_REF = str(Path.home() / "assets" / "overlays" / "videochat_ref_ninja.png")
VIDEOCHAT_GLITCH_REF = str(Path.home() / "assets" / "overlays" / "Glitch_Facetime_Design.png")
VIDEOCHAT_OVERLAY_DIR = Path.home() / "assets" / "overlays"

# Pre-rendered listener loops — eliminates 50% of Kling renders.
# Each ~10s loop is trimmed/repeated to match speaker duration at composite time.
LISTENER_LOOPS = {
    "NINJA": [
        str(Path.home() / "assets/listener_loops/ninja_idle_primary.mp4"),
    ],
    "GLITCH": [
        str(Path.home() / "assets/listener_loops/glitch_idle_shrug.mp4"),
        str(Path.home() / "assets/listener_loops/glitch_idle_nod.mp4"),
    ],
}

# Per-character prompts for video chat format
VIDEOCHAT_SPEAKER_PROMPTS = {
    "NINJA": (
        "Character on a video call, webcam framing. Speaking enthusiastically to camera. "
        "Expressive eyes that blink and emote naturally, lively head movements, natural smile. "
        "Maintain eye contact with camera. Stable body, no camera movement."
    ),
    "GLITCH": (
        "Character on a video call, webcam framing. Speaking cheerfully to camera. "
        "Expressive eyes, natural blinking, playful head movements. Fun energetic delivery. "
        "Maintain eye contact with camera. Stable body, no camera movement."
    ),
}

VIDEOCHAT_LISTENER_PROMPTS = {
    "NINJA": (
        "Character on a video call, webcam framing. Listening silently, NOT speaking. "
        "Mouth closed, lips together at all times. No talking, no lip movement. "
        "Subtle nodding, natural eye blinks, engaged expression. "
        "Slight reactive head movements showing interest. Stable body, no camera movement."
    ),
    "GLITCH": (
        "Character on a video call, webcam framing. Listening silently, NOT speaking. "
        "Mouth closed, lips together at all times. No talking, no lip movement. "
        "Subtle nodding, natural eye blinks, engaged expression. "
        "Slight reactive head movements showing interest. Stable body, no camera movement."
    ),
}

# ---------------------------------------------------------------------------
# Dual-Render Character Crops
# ---------------------------------------------------------------------------
# Instead of cropping characters, we PAINT OVER the other character in the
# full reference image, then send the whole 9:16 frame to Kling. This way:
# - Character stays at exact pixel position (no crop/pad/offset issues)
# - Kling only sees ONE face (no ghost mouthing)
# - Output is already the correct 9:16 size (no scaling needed)
# - Composite is a simple split between the two renders
#
# CHARACTER_MASKS: region to paint over to HIDE that character.
# Format: (x_frac, y_frac, w_frac, h_frac) — what to cover with bg color.

CHARACTER_MASKS = {
    "NINJA_SPEAKS": {
        # Right angle: Ninja prominent right, Glitch background left
        "GLITCH": (0.0, 0.02, 0.40, 0.95),   # mask out Glitch (left side)
        "NINJA": (0.42, 0.02, 0.58, 0.95),    # mask out Ninja (right side)
    },
    "GLITCH_SPEAKS": {
        # Left angle: Glitch prominent left, Ninja background right
        "NINJA": (0.52, 0.02, 0.48, 0.95),    # mask out Ninja (right side)
        "GLITCH": (0.0, 0.02, 0.55, 0.95),    # mask out Glitch (left side)
    },
    "CENTER": {
        # Center: both roughly equal
        "GLITCH": (0.0, 0.02, 0.45, 0.95),    # mask out Glitch (left half)
        "NINJA": (0.50, 0.02, 0.50, 0.95),    # mask out Ninja (right half)
    },
}

# Vertical split line for compositing (x_frac). Left of split comes from
# the render where GLITCH is visible, right comes from NINJA's render.
# Should be in the empty gap between the two characters.
COMPOSITE_SPLIT = {
    "NINJA_SPEAKS": 0.40,
    "GLITCH_SPEAKS": 0.52,
    "CENTER": 0.47,
}

# Per-character prompts for dual-render (single character in frame)
SPEAKER_PROMPTS = {
    "NINJA": (
        "Single animated Pixar ninja character speaking enthusiastically to camera. "
        "Expressive digital LED eyes that blink naturally, widen with excitement. "
        "Lively head movements, natural micro-expressions. Energetic delivery. "
        "Stable body posture, arms and hands resting flat on desk."
    ),
    "GLITCH": (
        "Single animated Pixar cyberpunk girl speaking cheerfully to camera. "
        "Expressive pink-tinted goggles, natural blinking, playful head movements. "
        "Fun energetic delivery with personality. "
        "Stable body posture, arms and hands resting flat on desk."
    ),
}

LISTENER_PROMPTS = {
    "NINJA": (
        "Single animated Pixar ninja character listening attentively at news desk. "
        "Subtle nodding, natural LED eye blinks, engaged listening expression. "
        "Slight reactive head movements showing interest. "
        "Stable seated posture, arms and hands resting on desk."
    ),
    "GLITCH": (
        "Single animated Pixar cyberpunk girl listening at news desk. "
        "Subtle nodding, natural eye blinks behind goggles, engaged expression. "
        "Slight reactive head movements, occasional small smile. "
        "Stable seated posture, arms and hands resting on desk."
    ),
}

FEATHER_PX = 40  # Pixels of soft edge blending (0 = hard edge)

OUTPUT_DIR = Path.home() / "output"

# Background color for padding
BG_COLOR = "0x1a1a2e"

# ---------------------------------------------------------------------------
# Dialogue Parsing
# ---------------------------------------------------------------------------

def parse_dialogue(script_text: str) -> list[dict]:
    """Parse a dialogue script with NINJA: and GLITCH: labels into turns.

    Input format:
        NINJA: What's up ninjas! Big news today.
        GLITCH: Oh yeah, this one is wild.
        NINJA: So PlayStation just dropped...

    Returns:
        [{"speaker": "NINJA", "text": "What's up ninjas! Big news today."}, ...]
    """
    turns = []
    current_speaker = None
    current_lines = []

    for line in script_text.splitlines():
        line = line.strip()
        if not line:
            continue

        match = re.match(r'^(NINJA|GLITCH):\s*(.*)$', line, re.IGNORECASE)
        if match:
            # Save previous turn
            if current_speaker and current_lines:
                turns.append({
                    "speaker": current_speaker.upper(),
                    "text": " ".join(current_lines).strip(),
                })
            current_speaker = match.group(1).upper()
            current_lines = [match.group(2)] if match.group(2) else []
        elif current_speaker:
            # Continuation of current speaker's turn
            current_lines.append(line)

    # Don't forget the last turn
    if current_speaker and current_lines:
        turns.append({
            "speaker": current_speaker.upper(),
            "text": " ".join(current_lines).strip(),
        })

    if not turns:
        print("   WARNING: No dialogue turns parsed from script")

    return turns


# ---------------------------------------------------------------------------
# Silent WAV Generator
# ---------------------------------------------------------------------------

def generate_silent_wav(duration_sec: float, output_path: str, sample_rate: int = 44100) -> str:
    """Generate a silent WAV file of exact duration. 44100Hz mono 16-bit."""
    num_frames = int(duration_sec * sample_rate)
    with wave.open(output_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{num_frames}h', *([0] * num_frames)))
    return output_path


def generate_60hz_tone_wav(duration_sec: float, output_path: str, sample_rate: int = 44100) -> str:
    """Generate a pure 60Hz sine wave at near-silence volume.

    DISCOVERY (Feb 24, 2026): This is the key to eliminating ghost mouthing
    in the listener's Kling Avatar render.

    Why this works:
    - Pure digital silence (all zeros) → Kling treats as missing/corrupt audio,
      hallucinated mouth movement
    - Pink/white noise → random amplitude spikes in speech frequencies (300-3400Hz)
      occasionally trigger lip sync
    - 60Hz pure sine → perfectly constant signal, well below speech range,
      zero amplitude variation. Lip sync model sees "audio exists, no speech."

    Validated through 4 iterations: silent→full mouthing, anti-prompts→mostly fixed,
    pink noise→jitter, 60Hz sine→CLEAN.
    """
    num_frames = int(duration_sec * sample_rate)
    frequency = 60.0   # Hz — well below speech range (300-3400Hz)
    amplitude = 30      # out of 32767 — barely above noise floor
    samples = []
    for i in range(num_frames):
        t = i / sample_rate
        sample = int(amplitude * math.sin(2 * math.pi * frequency * t))
        samples.append(sample)
    with wave.open(output_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{num_frames}h', *samples))
    return output_path


# ---------------------------------------------------------------------------
# Camera Angle Selection
# ---------------------------------------------------------------------------

def select_angle(speaker: str, turn_index: int, total_turns: int) -> tuple[str, str, str]:
    """Select camera angle image and prompt for a dialogue turn.

    Logic:
    - First turn (intro): CENTER if available, else speaker's angle
    - Last turn (outro): CENTER if available, else speaker's angle
    - Normal turns: speaker's angle (Ninja→right cam, Glitch→left cam)

    Returns (image_path, prompt, angle_key).
    """
    # Determine desired angle
    is_bookend = turn_index == 0 or turn_index == total_turns - 1
    if is_bookend and CAMERA_ANGLES["CENTER"]:
        angle_key = "CENTER"
    elif speaker == "NINJA":
        angle_key = "NINJA_SPEAKS"
    else:
        angle_key = "GLITCH_SPEAKS"

    image = CAMERA_ANGLES.get(angle_key)
    prompt = ANGLE_PROMPTS.get(angle_key, "")

    # Fallback chain: if desired angle not available, try alternatives
    if not image or not Path(image).exists():
        for fallback_key in ["NINJA_SPEAKS", "GLITCH_SPEAKS", "CENTER"]:
            fallback = CAMERA_ANGLES.get(fallback_key)
            if fallback and Path(fallback).exists():
                image = fallback
                angle_key = fallback_key
                prompt = ANGLE_PROMPTS.get(
                    f"{speaker}_SPEAKS",
                    ANGLE_PROMPTS.get(fallback_key, ""),
                )
                break

    if not image or not Path(image).exists():
        raise FileNotFoundError(
            f"No camera angle images found! Update CAMERA_ANGLES paths in {__file__}"
        )

    return image, prompt, angle_key


# ---------------------------------------------------------------------------
# Dual-Render Functions
# ---------------------------------------------------------------------------

def setup_fal_key():
    """Ensure FAL_KEY environment variable is set for fal_client."""
    if os.environ.get('FAL_KEY'):
        return True
    fal_key = os.environ.get('FAL_AI_API_KEY')
    if not fal_key:
        env_file = Path("/home/ndninja/projects/content-automation/.env")
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith('FAL_AI_API_KEY='):
                        fal_key = line.strip().split('=', 1)[1].strip('"\'')
                        break
    if not fal_key:
        try:
            import keyring
            fal_key = keyring.get_password("fal_ai", "api_key")
        except Exception:
            pass
    if fal_key:
        os.environ['FAL_KEY'] = fal_key
        return True
    print("   ERROR: fal.ai API key not found. Set FAL_KEY or FAL_AI_API_KEY.")
    return False


def mask_other_character(reference_path, character_to_hide, angle_key, work_dir):
    """Create a version of the reference with one character painted over.

    Instead of cropping (which causes alignment issues), we keep the FULL
    9:16 reference image and just paint a dark rectangle over the character
    we want to hide. Kling gets a full-size image with only one visible face.

    Args:
        character_to_hide: "NINJA" or "GLITCH" — which character to mask out.

    Returns image path, or None if no mask defined.
    """
    from PIL import Image, ImageDraw, ImageFilter

    masks = CHARACTER_MASKS.get(angle_key, {})
    region = masks.get(character_to_hide)
    if not region:
        return None

    x_frac, y_frac, w_frac, h_frac = region
    img = Image.open(reference_path)
    iw, ih = img.size

    # Convert fractions to pixels
    x = int(x_frac * iw)
    y = int(y_frac * ih)
    w = int(w_frac * iw)
    h = int(h_frac * ih)

    # Sample background color from the edges of the mask region
    # (average a strip along the mask boundary for a natural fill)
    draw = ImageDraw.Draw(img)

    # Use a gradient fill: sample colors from the edges and blend inward
    # For simplicity, use the studio background color
    bg_color = (26, 26, 46)  # matches BG_COLOR 0x1a1a2e

    # Paint over the character region
    draw.rectangle([x, y, x + w, y + h], fill=bg_color)

    # Soften the mask edges with a slight blur on the boundary
    # (prevents a hard rectangle edge from confusing Kling)
    out_path = str(work_dir / f"masked_{character_to_hide.lower()}_{angle_key.lower()}.jpg")
    img.save(out_path, quality=95)
    img.close()

    print(f"      Masked {character_to_hide}: {w}x{h} painted at ({x},{y})")
    return out_path


def composite_dual_render(speaker_video, listener_video, speaker,
                          angle_key, output_path, feather_px=FEATHER_PX):
    """Composite two full-frame Kling renders via vertical split.

    Both videos are full 9:16 frames (same size as the original reference).
    The speaker's render has the OTHER character painted over (dark bg).
    The listener's render has the SPEAKER painted over (dark bg).

    We take:
    - The speaker's side from the speaker's video (where they are visible)
    - The listener's side from the listener's video (where they are visible)

    For CENTER/NINJA_SPEAKS angles: Glitch is on the LEFT, Ninja on the RIGHT.
    For GLITCH_SPEAKS: Glitch is on the LEFT, Ninja is on the RIGHT.

    The split fraction from COMPOSITE_SPLIT defines where to cut.
    A feathered blend smooths the seam.
    Audio comes from the speaker video.
    """
    split_frac = COMPOSITE_SPLIT.get(angle_key, 0.47)

    # Get video dimensions
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "stream=width,height",
         "-of", "csv=p=0:s=x", speaker_video],
        capture_output=True, text=True,
    )
    dims = probe.stdout.strip().split("\n")[0]
    vw, vh = [int(x) for x in dims.split("x")]

    split_px = int(split_frac * vw)
    F = feather_px

    # Get duration from speaker video
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", speaker_video],
        capture_output=True, text=True,
    )
    duration = probe.stdout.strip()

    # Determine which video has Glitch visible (left side) and Ninja visible (right side)
    # The "speaker" video has the speaker visible and the other character painted over
    # The "listener" video has the listener visible and the speaker painted over
    if speaker == "NINJA":
        # Ninja speaks: ninja_video has Ninja visible (right), glitch_video has Glitch visible (left)
        right_video = speaker_video   # Ninja visible on right
        left_video = listener_video   # Glitch visible on left
        audio_video = speaker_video
    else:
        # Glitch speaks: glitch_video has Glitch visible (left), ninja_video has Ninja visible (right)
        left_video = speaker_video    # Glitch visible on left
        right_video = listener_video  # Ninja visible on right
        audio_video = speaker_video

    if F > 0:
        # Feathered vertical split using overlay with alpha gradient
        # 1. Use the left video as full base
        # 2. Crop the right portion from right_video (from split_px - F onward)
        # 3. Apply an alpha gradient on its left edge so it fades in
        # 4. Overlay on top of left video at the split position
        overlap_start = max(split_px - F, 0)
        right_crop_w = vw - overlap_start
        blend_zone = split_px - overlap_start  # pixels of fade-in

        filter_complex = (
            # Base: full left video
            f"[0:v]format=rgba[base];"
            # Right side: crop from overlap_start, apply alpha gradient on left edge
            f"[1:v]format=rgba,"
            f"crop={right_crop_w}:{vh}:{overlap_start}:0,"
            f"geq="
            f"r='r(X,Y)':"
            f"g='g(X,Y)':"
            f"b='b(X,Y)':"
            f"a='if(lt(X,{blend_zone}),255*X/{max(blend_zone,1)},255)'"
            f"[right_fade];"
            # Overlay right_fade onto base
            f"[base][right_fade]overlay={overlap_start}:0:shortest=1,"
            f"format=yuv420p[out]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", left_video,    # [0] left side source (full frame base)
            "-i", right_video,   # [1] right side source (overlay)
            "-i", audio_video,   # [2] audio source
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "2:a",
            "-t", duration,
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ]
    else:
        # Hard split: left half from left_video, right half from right_video
        filter_complex = (
            f"[0:v]crop={split_px}:{vh}:0:0[left];"
            f"[1:v]crop={vw - split_px}:{vh}:{split_px}:0[right];"
            f"[left][right]hstack[out]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", left_video,
            "-i", right_video,
            "-i", audio_video,
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "2:a",
            "-t", duration,
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ERROR: Composite failed: {result.stderr[:300]}")
        return None

    print(f"   Composite done: {Path(output_path).name}")
    return output_path


def composite_videochat(ninja_video, glitch_video, speaker, output_path):
    """Composite two clips in video chat format — vertical stack + UI overlay.

    Each character gets their own 1080x912 panel, stacked vertically in a
    1080x1920 frame with a 40px gap and 32px status bar. A PNG overlay adds
    the video call UI (borders, name pills, LIVE badge, call timer).

    Args:
        ninja_video: Path to Ninja's rendered clip
        glitch_video: Path to Glitch's rendered clip
        speaker: "NINJA" or "GLITCH" — determines which overlay variant to use
        output_path: Where to save the composite
    """
    # Select overlay based on active speaker
    overlay_suffix = "ninja" if speaker == "NINJA" else "glitch"
    overlay_path = str(VIDEOCHAT_OVERLAY_DIR / f"videochat_overlay_{overlay_suffix}.png")
    if not Path(overlay_path).exists():
        overlay_path = str(VIDEOCHAT_OVERLAY_DIR / "videochat_overlay_neutral.png")

    cmd = [
        "ffmpeg", "-y",
        "-i", ninja_video,     # [0] Ninja (top panel)
        "-i", glitch_video,    # [1] Glitch (bottom panel)
        "-i", overlay_path,    # [2] UI overlay PNG
        "-filter_complex",
        "[0:v]scale=1080:912:force_original_aspect_ratio=increase,crop=1080:912[top];"
        "[1:v]scale=1080:912:force_original_aspect_ratio=increase,crop=1080:912[bot];"
        "[top][bot]vstack=inputs=2,pad=1080:1920:0:32:color=0x0D1117[bg];"
        "[bg][2:v]overlay=0:0:format=auto[v]",
        "-map", "[v]", "-map", "0:a" if speaker == "NINJA" else "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ERROR: Video chat composite failed: {result.stderr[:300]}")
        return None

    print(f"   Composite done (videochat): {Path(output_path).name}")
    return output_path


def get_listener_loop(character: str, turn_index: int) -> str:
    """Return a pre-rendered listener loop path, cycling through available loops."""
    loops = LISTENER_LOOPS[character]
    return loops[turn_index % len(loops)]


def prepare_listener_clip(loop_path: str, duration: float, output_path: str) -> str | None:
    """Trim or loop a pre-rendered listener clip to match target duration.

    If the loop is longer than needed, trim it.
    If shorter, loop it with -stream_loop then trim.
    """
    # Get loop duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", loop_path],
        capture_output=True, text=True,
    )
    loop_dur = float(probe.stdout.strip()) if probe.returncode == 0 else 10.0

    if loop_dur >= duration:
        # Simple trim
        cmd = [
            "ffmpeg", "-y",
            "-i", loop_path,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an",  # Drop loop audio — composite uses speaker audio only
            output_path,
        ]
    else:
        # Loop then trim
        loops_needed = math.ceil(duration / loop_dur)
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(loops_needed - 1),
            "-i", loop_path,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an",
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ERROR: prepare_listener_clip failed: {result.stderr[:200]}")
        return None
    return output_path


def videochat_render_turn(turn_index, turn, work_dir, kling_model="pro", use_loops=True):
    """Render one dialogue turn in VIDEO CHAT format.

    Speaker gets Pro Kling + TTS audio. Listener uses pre-rendered loops
    (or falls back to Standard Kling + 60Hz tone when use_loops=False).

    Returns path to composited clip, or None on failure.
    """
    import fal_client
    import requests as req

    speaker = turn["speaker"]
    non_speaker = "GLITCH" if speaker == "NINJA" else "NINJA"
    audio_path = turn["audio_path"]
    duration = turn["duration"]

    loop_tag = "loop" if use_loops else "kling"
    print(f"   VIDEOCHAT RENDER: {speaker} speaks, {non_speaker} listens ({loop_tag})")

    # --- Speaker: always a fresh Kling render ---
    speaker_ref_path = VIDEOCHAT_NINJA_REF if speaker == "NINJA" else VIDEOCHAT_GLITCH_REF
    print(f"   Uploading speaker ref + audio...")
    speaker_img_url = fal_client.upload(open(speaker_ref_path, "rb").read(), "image/png")
    speech_audio_url = fal_client.upload(open(audio_path, "rb").read(), "audio/mpeg")

    sp_model = f"fal-ai/kling-video/ai-avatar/v2/{kling_model}"
    print(f"   Submitting {speaker} (speaking, {kling_model}) to Kling...")
    speaker_handle = fal_client.submit(
        sp_model,
        arguments={
            "image_url": speaker_img_url,
            "audio_url": speech_audio_url,
            "prompt": VIDEOCHAT_SPEAKER_PROMPTS[speaker],
            "negative_prompt": NEGATIVE_PROMPT,
            "cfg_scale": CFG_SCALE,
        },
    )

    # --- Listener: pre-rendered loop (default) or fresh Kling render ---
    ls_video_path = str(work_dir / f"turn_{turn_index:02d}_{non_speaker.lower()}_listen.mp4")

    if use_loops:
        loop_path = get_listener_loop(non_speaker, turn_index)
        print(f"   Listener: using loop {Path(loop_path).name} (no Kling call)")
        prepared = prepare_listener_clip(loop_path, duration, ls_video_path)
        if not prepared:
            print(f"   ERROR: Failed to prepare listener loop — aborting turn")
            return None
    else:
        # Fallback: full Kling render for listener (original behavior)
        tone_path = str(work_dir / f"tone_{turn_index:02d}.wav")
        generate_60hz_tone_wav(duration, tone_path)

        listener_ref_path = VIDEOCHAT_GLITCH_REF if speaker == "NINJA" else VIDEOCHAT_NINJA_REF
        listener_img_url = fal_client.upload(open(listener_ref_path, "rb").read(), "image/png")
        tone_audio_url = fal_client.upload(open(tone_path, "rb").read(), "audio/wav")

        ls_model = "fal-ai/kling-video/ai-avatar/v2/standard"
        print(f"   Submitting {non_speaker} (listening, standard) to Kling...")
        listener_handle = fal_client.submit(
            ls_model,
            arguments={
                "image_url": listener_img_url,
                "audio_url": tone_audio_url,
                "prompt": VIDEOCHAT_LISTENER_PROMPTS[non_speaker],
                "negative_prompt": LISTENER_NEGATIVE_PROMPT,
                "cfg_scale": LISTENER_CFG_SCALE,
            },
        )

    # --- Wait for speaker render ---
    t0 = time.time()
    speaker_result = speaker_handle.get()
    sp_dur = speaker_result.get("duration", "?")
    print(f"   {speaker} render done ({sp_dur}s, {time.time()-t0:.0f}s wall)")

    # --- Wait for listener render (only if not using loops) ---
    if not use_loops:
        listener_result = listener_handle.get()
        ls_dur = listener_result.get("duration", "?")
        print(f"   {non_speaker} render done ({ls_dur}s, {time.time()-t0:.0f}s wall)")

        r = req.get(listener_result["video"]["url"])
        with open(ls_video_path, "wb") as f:
            f.write(r.content)

    # --- Download speaker video ---
    sp_video_path = str(work_dir / f"turn_{turn_index:02d}_{speaker.lower()}_speak.mp4")
    r = req.get(speaker_result["video"]["url"])
    with open(sp_video_path, "wb") as f:
        f.write(r.content)

    # --- Composite into video chat layout ---
    clip_path = str(work_dir / f"turn_{turn_index:02d}_videochat.mp4")
    ninja_video = sp_video_path if speaker == "NINJA" else ls_video_path
    glitch_video = ls_video_path if speaker == "NINJA" else sp_video_path

    result = composite_videochat(ninja_video, glitch_video, speaker, clip_path)
    if result:
        turn["clip_path"] = clip_path
    return result


def dual_render_turn(turn_index, turn, work_dir, kling_model="pro"):
    """Render one dialogue turn using dual parallel Kling Avatar sessions.

    Paint-over approach (v3):
    1. Create two versions of the full reference image:
       - Speaker's version: other character painted over with dark bg
       - Listener's version: speaker painted over with dark bg
    2. Submit both to Kling in parallel (full 9:16 frames)
    3. Download both animated videos
    4. Composite via vertical split (each side from the render where that character is visible)

    Returns path to composited clip, or None on failure.
    """
    import fal_client
    import requests as req

    speaker = turn["speaker"]
    non_speaker = "GLITCH" if speaker == "NINJA" else "NINJA"
    angle_key = turn["angle_key"]
    reference_path = turn["angle_image"]
    audio_path = turn["audio_path"]
    duration = turn["duration"]

    print(f"   DUAL RENDER: {speaker} speaks, {non_speaker} listens")

    # 1. Create masked images (paint over the character we DON'T want Kling to see)
    # Speaker's image: hide the non-speaker so Kling only animates the speaker
    speaker_masked = mask_other_character(
        reference_path, non_speaker, angle_key, work_dir,
    )
    # Listener's image: hide the speaker so Kling only animates the listener
    listener_masked = mask_other_character(
        reference_path, speaker, angle_key, work_dir,
    )

    if not speaker_masked:
        print(f"   ERROR: No mask config for {non_speaker} in {angle_key}")
        return None

    # 2. Generate silent WAV for listener
    silent_path = str(work_dir / f"silent_{turn_index:02d}.wav")
    generate_silent_wav(duration, silent_path)

    # 3. Upload assets to fal.ai
    print(f"   Uploading masked images + audio to fal.ai...")
    sp_img_url = fal_client.upload(open(speaker_masked, "rb").read(), "image/jpeg")
    sp_audio_url = fal_client.upload(open(audio_path, "rb").read(), "audio/mpeg")

    ls_img_url = None
    ls_audio_url = None
    if listener_masked:
        ls_img_url = fal_client.upload(
            open(listener_masked, "rb").read(), "image/jpeg"
        )
        ls_audio_url = fal_client.upload(
            open(silent_path, "rb").read(), "audio/wav"
        )

    # 4. Submit parallel Kling jobs
    model_id = f"fal-ai/kling-video/ai-avatar/v2/{kling_model}"
    sp_prompt = SPEAKER_PROMPTS.get(speaker, "Character speaking to camera.")
    ls_prompt = LISTENER_PROMPTS.get(non_speaker, "Character listening.")

    print(f"   Submitting {speaker} (speaking) to Kling {kling_model}...")
    speaker_handle = fal_client.submit(
        model_id,
        arguments={
            "image_url": sp_img_url,
            "audio_url": sp_audio_url,
            "prompt": sp_prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "cfg_scale": CFG_SCALE,
        },
    )

    listener_handle = None
    if ls_img_url:
        print(f"   Submitting {non_speaker} (listening) to Kling {kling_model}...")
        listener_handle = fal_client.submit(
            model_id,
            arguments={
                "image_url": ls_img_url,
                "audio_url": ls_audio_url,
                "prompt": ls_prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "cfg_scale": CFG_SCALE,
            },
        )

    print(f"   Both renders submitted — waiting for parallel completion...")

    # 5. Collect results (both run in parallel on fal.ai)
    t0 = time.time()
    speaker_result = speaker_handle.get()
    sp_dur = speaker_result.get("duration", "?")
    print(f"   {speaker} render done ({sp_dur}s, {time.time()-t0:.0f}s wall)")

    ls_video_path = None
    if listener_handle:
        listener_result = listener_handle.get()
        ls_dur = listener_result.get("duration", "?")
        print(f"   {non_speaker} render done ({ls_dur}s, {time.time()-t0:.0f}s wall)")

    # 6. Download videos
    sp_video_path = str(work_dir / f"turn_{turn_index:02d}_{speaker.lower()}_sp.mp4")
    r = req.get(speaker_result["video"]["url"])
    with open(sp_video_path, "wb") as f:
        f.write(r.content)
    print(f"   Downloaded {speaker} video ({len(r.content)/1024/1024:.1f}MB)")

    if listener_handle:
        ls_video_path = str(
            work_dir / f"turn_{turn_index:02d}_{non_speaker.lower()}_ls.mp4"
        )
        r = req.get(listener_result["video"]["url"])
        with open(ls_video_path, "wb") as f:
            f.write(r.content)
        print(f"   Downloaded {non_speaker} video ({len(r.content)/1024/1024:.1f}MB)")

    # 7. Composite via vertical split
    output_path = str(work_dir / f"turn_{turn_index:02d}_dual.mp4")

    if ls_video_path:
        result = composite_dual_render(
            sp_video_path, ls_video_path,
            speaker, angle_key,
            output_path,
        )
    else:
        # Speaker-only fallback — just use the speaker video directly
        import shutil
        shutil.copy2(sp_video_path, output_path)
        print(f"   Using speaker-only video (no listener render)")
        result = output_path

    if not result:
        print(f"   ERROR: Composite failed, using raw speaker video")
        import shutil
        shutil.copy2(sp_video_path, output_path)

    return output_path


# ---------------------------------------------------------------------------
# Core Pipeline Functions
# ---------------------------------------------------------------------------

def generate_turn_clips(turns: list[dict], work_dir: Path,
                        kling_model: str = "pro",
                        single_render: bool = False,
                        format: str = "newsdesk",
                        use_loops: bool = True) -> list[dict]:
    """Generate clips for each dialogue turn.

    Formats:
      videochat (recommended): Independent renders per character, vertical stack,
        60Hz tone for listener, Standard tier for listener. No seam issues.
      newsdesk (legacy): Side-by-side news desk with paint-over masking.
      single: One Kling render per turn (may have ghost mouthing).
    """
    total = len(turns)
    if format == "videochat":
        mode = "VIDEOCHAT"
    elif single_render:
        mode = "SINGLE"
    else:
        mode = "DUAL-RENDER"
    print(f"\n   Generating clips for {total} dialogue turns ({mode})...")

    if not single_render:
        if not setup_fal_key():
            print("   FATAL: Cannot proceed without fal.ai API key")
            return turns

    for i, turn in enumerate(turns):
        speaker = turn["speaker"]
        char = CHARACTERS[speaker]

        print(f"\n   --- Turn {i+1}/{total}: {speaker} speaks ---")

        # Step 1: TTS
        audio_path = str(work_dir / f"turn_{i:02d}_audio.mp3")
        print(f"   TTS: {char['name']} → {turn['text'][:60]}...")
        generate_tts(
            turn["text"], audio_path,
            voice_id=char["voice_id"],
            voice_style=char["voice_style"],
        )
        turn["audio_path"] = audio_path
        turn["duration"] = get_audio_duration(audio_path)
        print(f"   Duration: {turn['duration']:.1f}s")

        # Step 2: Select camera angle
        angle_image, angle_prompt, angle_key = select_angle(speaker, i, total)
        turn["angle_image"] = angle_image
        turn["angle_key"] = angle_key
        print(f"   Camera: {Path(angle_image).name} ({angle_key})")

        if format == "videochat":
            # Video chat format: speaker gets Kling render, listener uses pre-rendered loops
            # (unless --no-loops: falls back to Kling + 60Hz tone for both)
            clip_path = videochat_render_turn(i, turn, work_dir, kling_model, use_loops=use_loops)
            if not clip_path or not Path(clip_path).exists():
                print(f"   ERROR: Videochat render failed for turn {i+1}")
                turn["clip_path"] = None
                continue
            turn["clip_path"] = clip_path
        elif single_render:
            # Old mode: single Kling render with both characters
            clip_path = str(work_dir / f"turn_{i:02d}_{speaker.lower()}.mp4")
            print(f"   Kling: Single render with {char['name']} speaking...")
            generate_kling_avatar_video(
                angle_image, audio_path, clip_path,
                model=kling_model,
                prompt=angle_prompt,
                negative_prompt=NEGATIVE_PROMPT,
                cfg_scale=CFG_SCALE,
            )
            turn["clip_path"] = clip_path
        else:
            # Dual-render newsdesk: crop each character, parallel Kling, composite
            clip_path = dual_render_turn(i, turn, work_dir, kling_model)
            if not clip_path or not Path(clip_path).exists():
                print(f"   ERROR: Dual render failed for turn {i+1}")
                turn["clip_path"] = None
                continue
            turn["clip_path"] = clip_path

    return turns


def normalize_clip(clip_path: str, output_path: str, duration: float,
                   target_w: int = 1080, target_h: int = 1920) -> str:
    """Scale and pad a clip to exact target dimensions (default 9:16 for Shorts).

    Handles any input aspect ratio from Kling output.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", clip_path,
        "-vf", (
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color={BG_COLOR}"
        ),
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{duration:.3f}",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ERROR normalizing: {result.stderr[:200]}")
        return None
    return output_path


def assemble_dual_anchor(composite_paths: list[str], output_path: str) -> str:
    """Concatenate all composited turns into final video using FFmpeg concat demuxer."""
    print(f"\n   Assembling {len(composite_paths)} segments into final video...")

    concat_file = Path(output_path).parent / "concat_list.txt"
    with open(concat_file, "w") as f:
        for p in composite_paths:
            f.write(f"file '{p}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ERROR assembling: {result.stderr[:200]}")
        return None
    return output_path


# ---------------------------------------------------------------------------
# Main Pipeline Orchestrator
# ---------------------------------------------------------------------------

def run_dual_anchor_pipeline(script_text: str, output_name: str = "ninja_dual",
                              kling_model: str = "pro",
                              single_render: bool = False,
                              format: str = "videochat",
                              use_loops: bool = True) -> str | None:
    """Full dual-anchor pipeline: parse → TTS → angle select → render → concat.

    Formats:
      videochat (default): FaceTime-style vertical stack. Recommended.
      newsdesk: Side-by-side news desk with feathered split.
      --single-render: Old single-session mode (legacy).

    Returns path to final video, or None on failure.
    """
    if format == "videochat":
        render_mode = "VideoChat"
    elif single_render:
        render_mode = "Single-Render"
    else:
        render_mode = "Dual-Render"
    print("\n" + "=" * 60)
    print(f"  NINJA NEWS NETWORK — DUAL ANCHOR PIPELINE ({render_mode})")
    print("=" * 60)
    print(f"  Model: Kling Avatar v2 {kling_model}")
    loops_status = "ON (pre-rendered)" if use_loops else "OFF (fresh Kling renders)"
    print(f"  Listener loops: {loops_status}")
    print(f"  Characters: {CHARACTERS['NINJA']['name']} + {CHARACTERS['GLITCH']['name']}")

    # Show available camera angles
    for key, path in CAMERA_ANGLES.items():
        status = "READY" if path and Path(path).exists() else "MISSING"
        print(f"  Camera [{key}]: {status} — {path or 'not set'}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()

    with tempfile.TemporaryDirectory(prefix="ninja_dual_") as tmpdir:
        work_dir = Path(tmpdir)

        # 1. Parse dialogue
        turns = parse_dialogue(script_text)
        if not turns:
            print("ERROR: No dialogue turns found in script")
            return None
        print(f"\n   Parsed {len(turns)} dialogue turns:")
        for t in turns:
            print(f"     {t['speaker']}: {t['text'][:70]}...")

        # 2. Generate all clips (TTS + Kling render per turn)
        turns = generate_turn_clips(turns, work_dir, kling_model, single_render,
                                       format=format, use_loops=use_loops)

        # 3. Normalize clips to consistent dimensions
        normalized = []
        print(f"\n   Normalizing {len(turns)} clips...")
        for i, turn in enumerate(turns):
            clip = turn.get("clip_path")
            if not clip or not Path(clip).exists():
                print(f"   WARNING: Skipping missing clip for turn {i+1}")
                continue
            norm_path = str(work_dir / f"norm_{i:02d}.mp4")
            result = normalize_clip(clip, norm_path, turn["duration"])
            if result:
                normalized.append(result)
            else:
                print(f"   WARNING: Skipping failed normalize for turn {i+1}")

        if not normalized:
            print("ERROR: All clips failed")
            return None

        # 4. Concatenate into final video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_path = str(OUTPUT_DIR / f"{output_name}_{timestamp}.mp4")
        result = assemble_dual_anchor(normalized, final_path)

        if not result:
            print("ERROR: Assembly failed")
            return None

    elapsed = time.time() - start_time
    total_duration = sum(t.get("duration", 0) for t in turns)
    if format == "videochat":
        if use_loops:
            cost_per_sec = 0.115  # Speaker only — listener from pre-rendered loops
        else:
            cost_per_sec = 0.115 + 0.056  # Speaker Pro + listener Standard (no loops)
    elif single_render:
        cost_per_sec = 0.115 if kling_model == "pro" else 0.056
    else:
        cost_multiplier = 2
        cost_per_sec = (0.115 if kling_model == "pro" else 0.056) * cost_multiplier

    print("\n" + "=" * 60)
    print(f"  DONE! Output: {final_path}")
    print(f"  Total duration: {total_duration:.1f}s")
    print(f"  Render time: {elapsed/60:.1f} min")
    print(f"  Turns: {len(turns)} ({sum(1 for t in turns if t['speaker']=='NINJA')} Ninja, "
          f"{sum(1 for t in turns if t['speaker']=='GLITCH')} Glitch)")
    print(f"  Est. Kling cost: ~${total_duration * cost_per_sec:.2f} "
          f"({total_duration:.0f}s × ${cost_per_sec}/s)")
    print(f"  Camera angles used: {len(set(t.get('angle_image','') for t in turns))}")
    print("=" * 60)

    return final_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ninja News Network — Dual Anchor Pipeline"
    )
    parser.add_argument("--script-file", required=True,
                        help="Path to dialogue script file (NINJA:/GLITCH: labels)")
    parser.add_argument("--output", default="ninja_dual",
                        help="Output filename prefix (default: ninja_dual)")
    parser.add_argument("--kling-model", default="pro", choices=["standard", "pro"],
                        help="Kling Avatar model (default: pro)")
    parser.add_argument("--format", default="videochat",
                        choices=["videochat", "newsdesk"],
                        help="Output format (default: videochat)")
    parser.add_argument("--single-render", action="store_true",
                        help="Use single Kling render per turn (legacy, may have ghost mouthing)")
    parser.add_argument("--no-loops", action="store_true",
                        help="Disable pre-rendered listener loops (fall back to Kling renders)")
    args = parser.parse_args()

    script_text = Path(args.script_file).read_text()
    result = run_dual_anchor_pipeline(
        script_text,
        output_name=args.output,
        kling_model=args.kling_model,
        single_render=args.single_render,
        format=args.format,
        use_loops=not args.no_loops,
    )

    if result:
        print(f"\nDONE! Output: {result}")
        sys.exit(0)
    else:
        print("\nPipeline failed!")
        sys.exit(1)
