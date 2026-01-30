#!/usr/bin/env python3
"""
ninja_background.py — Background compositor for Neurodivergent Ninja avatar videos.

Removes the background from Ditto TalkingHead output and composites the avatar
over a custom background (static image or video). Supports multiple removal
methods and visual effects.

Usage:
    python3 ninja_background.py --input avatar.mp4 --background bg.png --output out.mp4
    python3 ninja_background.py --input avatar.mp4 --bg-style cyberpunk --output out.mp4
    python3 ninja_background.py --input avatar.mp4 --bg-style dark_studio --output out.mp4

Supports:
    - AI-based background removal (rembg/u2net) — best quality
    - Luminance-based keying — fast fallback
    - Static image or video backgrounds
    - Vignette, glow, and edge softening effects
    - Source-resolution compositing (288×512) for pipeline integration
"""

import argparse
import json
import os
import sys
import subprocess
import tempfile
import shutil
import time
import numpy as np

# Lazy imports for optional dependencies
cv2 = None
Image = None
ImageFilter = None


def import_deps():
    """Import dependencies lazily to allow --help without them."""
    global cv2, Image, ImageFilter
    import cv2 as _cv2
    from PIL import Image as _Image, ImageFilter as _ImageFilter
    cv2 = _cv2
    Image = _Image
    ImageFilter = _ImageFilter


###############################################################################
# Constants
###############################################################################
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "assets", "backgrounds")
SCENES_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "assets", "scenes")

# Built-in background styles (map to files in assets/backgrounds/)
BG_STYLES = {
    "cyberpunk":    "cyberpunk_neon.png",
    "dark_studio":  "dark_studio.png",
    "gaming":       "gaming_rgb.png",
    "dojo":         "ninja_dojo.png",
    "matrix":       "matrix_tech.png",
}

# Layered scenes (map to directories in assets/scenes/)
SCENE_STYLES = {
    "dojo_layered": "dojo",  # Traditional dojo with foreground table
}

# Source resolution from Ditto
SRC_W, SRC_H = 288, 512

# Final resolution (9:16 vertical)
FINAL_W, FINAL_H = 1080, 1920


###############################################################################
# Scene loading (layered backgrounds)
###############################################################################

def load_scene(scene_name):
    """
    Load a layered scene configuration.
    Returns dict with background, foreground (optional), and config.
    """
    scene_dir = os.path.join(SCENES_DIR, scene_name)
    config_path = os.path.join(scene_dir, "scene_config.json")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Scene config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Load background image
    bg_filename = config.get("layers", {}).get("background", "dojo_background.png")
    bg_path = os.path.join(scene_dir, bg_filename)
    if not os.path.exists(bg_path):
        raise FileNotFoundError(f"Background not found: {bg_path}")
    
    result = {
        "config": config,
        "background_path": bg_path,
        "foreground_path": None,
        "scene_dir": scene_dir,
    }
    
    # Load foreground if exists
    fg_filename = config.get("layers", {}).get("foreground")
    if fg_filename:
        fg_path = os.path.join(scene_dir, fg_filename)
        if os.path.exists(fg_path):
            result["foreground_path"] = fg_path
    
    return result


def composite_frame_layered(avatar_rgba, background_rgb, foreground_rgba=None, 
                            avatar_zone=None, effects=None):
    """
    Composite avatar between background and foreground layers.
    
    Args:
        avatar_rgba: Avatar with alpha (RGBA numpy array)
        background_rgb: Background image (RGB numpy array)
        foreground_rgba: Optional foreground layer with alpha (RGBA numpy array)
        avatar_zone: Dict with positioning hints (x_center, y_center, scale)
        effects: Optional effects dict
    
    Returns:
        RGB numpy array with composited result
    """
    h, w = background_rgb.shape[:2]
    avatar_h, avatar_w = avatar_rgba.shape[:2]
    
    # Position and scale avatar according to avatar_zone
    if avatar_zone:
        # Target scale: avatar should fill this fraction of height
        target_scale = avatar_zone.get("scale", 0.6)
        target_h = int(h * target_scale)
        scale_factor = target_h / avatar_h
        new_w = int(avatar_w * scale_factor)
        new_h = target_h
        
        # Resize avatar
        avatar_resized = cv2.resize(avatar_rgba, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Position: center on x_center, y_center
        x_center = int(w * avatar_zone.get("x_center", 0.5))
        y_center = int(h * avatar_zone.get("y_center", 0.45))
        
        x_start = x_center - new_w // 2
        y_start = y_center - new_h // 2
    else:
        # Default: center avatar, scale to fit
        scale_factor = min(w / avatar_w, h / avatar_h) * 0.8
        new_w = int(avatar_w * scale_factor)
        new_h = int(avatar_h * scale_factor)
        
        avatar_resized = cv2.resize(avatar_rgba, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        x_start = (w - new_w) // 2
        y_start = (h - new_h) // 2
    
    # Create result starting with background
    result = background_rgb.astype(float).copy()
    
    # Composite avatar onto background
    x_end = min(x_start + new_w, w)
    y_end = min(y_start + new_h, h)
    x_start_clamped = max(0, x_start)
    y_start_clamped = max(0, y_start)
    
    # Adjust avatar slice for clamping
    av_x_start = x_start_clamped - x_start
    av_y_start = y_start_clamped - y_start
    av_x_end = av_x_start + (x_end - x_start_clamped)
    av_y_end = av_y_start + (y_end - y_start_clamped)
    
    avatar_slice = avatar_resized[av_y_start:av_y_end, av_x_start:av_x_end]
    alpha = avatar_slice[:, :, 3:4].astype(float) / 255.0
    fg = avatar_slice[:, :, :3].astype(float)
    
    bg_region = result[y_start_clamped:y_end, x_start_clamped:x_end]
    result[y_start_clamped:y_end, x_start_clamped:x_end] = fg * alpha + bg_region * (1 - alpha)
    
    # Composite foreground layer on top (if provided)
    if foreground_rgba is not None:
        fg_h, fg_w = foreground_rgba.shape[:2]
        
        # Resize foreground to match output if needed
        if fg_h != h or fg_w != w:
            foreground_rgba = cv2.resize(foreground_rgba, (w, h), interpolation=cv2.INTER_LANCZOS4)
        
        fg_alpha = foreground_rgba[:, :, 3:4].astype(float) / 255.0
        fg_rgb = foreground_rgba[:, :, :3].astype(float)
        
        result = fg_rgb * fg_alpha + result * (1 - fg_alpha)
    
    # Apply effects
    if effects:
        if "vignette" in effects:
            result = apply_vignette(result, strength=effects.get("vignette_strength", 0.3))
        if "glow" in effects:
            # For layered scenes, apply glow based on avatar position
            glow_mask = np.zeros((h, w), dtype=np.uint8)
            if avatar_zone:
                # Create approximate mask at avatar position
                cv2.rectangle(glow_mask, 
                             (x_start_clamped, y_start_clamped), 
                             (x_end, y_end), 
                             255, -1)
                glow_mask = cv2.GaussianBlur(glow_mask, (51, 51), 0)
            result = apply_edge_glow(result, glow_mask, 
                                    color=effects.get("glow_color", (200, 100, 50)))
        if "warm_tint" in effects:
            result = apply_warm_tint(result, strength=effects.get("warm_tint_strength", 0.1))
    
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_warm_tint(frame, strength=0.1):
    """Add a warm color tint to match dojo lighting."""
    warm = np.array([1.05, 1.0, 0.9])  # Slightly boost red, reduce blue
    result = frame.copy()
    for c in range(3):
        result[:, :, c] = result[:, :, c] * (1 + (warm[c] - 1) * strength)
    return result


###############################################################################
# Background removal methods
###############################################################################

def remove_bg_rembg(frame_rgb):
    """
    Remove background using rembg (U2-Net AI model).
    Returns RGBA numpy array.
    """
    from rembg import remove as rembg_remove
    pil_img = Image.fromarray(frame_rgb)
    result = rembg_remove(pil_img)
    return np.array(result)


def remove_bg_luminance(frame_rgb, threshold=195, feather=8):
    """
    Remove background using luminance-based keying.
    Works well when the background is lighter than the subject.
    Returns RGBA numpy array.
    """
    h, w = frame_rgb.shape[:2]
    gray = np.mean(frame_rgb.astype(float), axis=2)

    # Create mask: dark pixels = foreground (avatar)
    # The Ditto background is a light-to-dark gradient, so we need
    # to analyze per-region
    mask = np.zeros((h, w), dtype=np.uint8)

    # Sample border regions to determine background color per row
    border_width = 15
    for y in range(h):
        # Get border pixels for this row
        left_border = frame_rgb[y, :border_width].mean(axis=0)
        right_border = frame_rgb[y, w-border_width:].mean(axis=0)
        bg_color = (left_border + right_border) / 2
        bg_brightness = bg_color.mean()

        for x in range(w):
            px = frame_rgb[y, x].astype(float)
            # Color distance from background
            color_dist = np.sqrt(np.sum((px - bg_color)**2))
            # Brightness difference
            bright_diff = abs(px.mean() - bg_brightness)

            if color_dist > 40 or bright_diff > 35:
                mask[y, x] = 255

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Feather edges
    if feather > 0:
        mask = cv2.GaussianBlur(mask, (feather*2+1, feather*2+1), 0)

    # Convert to RGBA
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = frame_rgb
    rgba[:, :, 3] = mask

    return rgba


def remove_bg_grabcut(frame_rgb):
    """
    Remove background using GrabCut (OpenCV).
    Returns RGBA numpy array.
    """
    h, w = frame_rgb.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    # Initialize with a rectangle that covers the center (where avatar is)
    rect = (int(w*0.05), int(h*0.02), int(w*0.9), int(h*0.95))

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(frame_rgb, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    # Convert mask: 0,2 = background, 1,3 = foreground
    fg_mask = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)

    # Feather
    fg_mask = cv2.GaussianBlur(fg_mask, (9, 9), 0)

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = frame_rgb
    rgba[:, :, 3] = fg_mask

    return rgba


###############################################################################
# Compositing
###############################################################################

def composite_frame(avatar_rgba, background_rgb, effects=None):
    """
    Composite avatar (RGBA) over background (RGB).
    Returns RGB numpy array.
    """
    h, w = avatar_rgba.shape[:2]
    bg_h, bg_w = background_rgb.shape[:2]

    # Resize background to match avatar if needed
    if bg_h != h or bg_w != w:
        bg_resized = cv2.resize(background_rgb, (w, h), interpolation=cv2.INTER_LANCZOS4)
    else:
        bg_resized = background_rgb.copy()

    # Extract alpha as float [0, 1]
    alpha = avatar_rgba[:, :, 3:4].astype(float) / 255.0
    fg = avatar_rgba[:, :, :3].astype(float)
    bg = bg_resized.astype(float)

    # Alpha blend
    result = fg * alpha + bg * (1 - alpha)

    # Apply effects
    if effects:
        if "vignette" in effects:
            result = apply_vignette(result, strength=effects.get("vignette_strength", 0.3))
        if "glow" in effects:
            result = apply_edge_glow(result, avatar_rgba[:, :, 3], color=effects.get("glow_color", (0, 180, 255)))
        if "ambient" in effects:
            result = apply_ambient_light(result, avatar_rgba[:, :, 3], color=effects.get("ambient_color", (0, 100, 200)))

    return np.clip(result, 0, 255).astype(np.uint8)


###############################################################################
# Visual effects
###############################################################################

def apply_vignette(frame, strength=0.3):
    """Add a subtle vignette darkening at edges."""
    h, w = frame.shape[:2]
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    vignette = 1.0 - strength * np.clip(dist - 0.5, 0, 1) ** 2
    vignette = np.expand_dims(vignette, axis=2)
    return frame * vignette


def apply_edge_glow(frame, alpha_mask, color=(0, 180, 255), intensity=0.4, blur_size=11):
    """Add a colored glow around the avatar edges."""
    # Find edges of the alpha mask
    edges = cv2.Canny(alpha_mask, 50, 150)
    edges = cv2.dilate(edges, None, iterations=2)
    edges_blur = cv2.GaussianBlur(edges, (blur_size*2+1, blur_size*2+1), 0)

    # Create colored glow
    glow = np.zeros_like(frame)
    edge_float = edges_blur.astype(float) / 255.0
    for c in range(3):
        glow[:, :, c] = color[c] * edge_float * intensity

    return frame + glow


def apply_ambient_light(frame, alpha_mask, color=(0, 100, 200), intensity=0.15):
    """Add subtle ambient colored light spill on the background around the avatar."""
    # Create a dilated mask of the avatar
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))
    dilated = cv2.dilate(alpha_mask, kernel, iterations=3)
    dilated = cv2.GaussianBlur(dilated, (81, 81), 0)

    # Only apply to background (where alpha is low)
    bg_mask = 1.0 - (alpha_mask.astype(float) / 255.0)
    spill_mask = (dilated.astype(float) / 255.0) * bg_mask

    ambient = np.zeros_like(frame)
    for c in range(3):
        ambient[:, :, c] = color[c] * spill_mask * intensity

    return frame + ambient


###############################################################################
# Video processing
###############################################################################

def process_video(input_path, bg_path, output_path, method="rembg",
                  effects=None, bg_is_video=False, cache_mask=True):
    """
    Process entire video: remove background and composite over new background.

    Args:
        input_path: Path to input avatar video
        bg_path: Path to background image or video
        output_path: Path to output video
        method: Background removal method ("rembg", "luminance", "grabcut")
        effects: Dict of effects to apply
        bg_is_video: Whether background is a video file
        cache_mask: If True, compute mask once and reuse (faster for talking heads)
    """
    import_deps()

    print(f"[Background] Processing: {os.path.basename(input_path)}")
    print(f"[Background] Method: {method}")
    print(f"[Background] Background: {os.path.basename(bg_path)}")

    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Background] Input: {width}x{height}, {fps}fps, {frame_count} frames")

    # Load background
    if bg_is_video:
        bg_cap = cv2.VideoCapture(bg_path)
        if not bg_cap.isOpened():
            raise RuntimeError(f"Cannot open background video: {bg_path}")
        bg_frame_count = int(bg_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    else:
        bg_img = cv2.imread(bg_path)
        if bg_img is None:
            raise RuntimeError(f"Cannot load background: {bg_path}")
        # Resize background to match input video dimensions
        bg_img = cv2.resize(bg_img, (width, height), interpolation=cv2.INTER_LANCZOS4)

    # Setup output - write to temp file first, then mux audio
    temp_dir = tempfile.mkdtemp(prefix="ninja_bg_")
    temp_video = os.path.join(temp_dir, "video_no_audio.mp4")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

    # Background removal function
    if method == "rembg":
        remove_fn = remove_bg_rembg
    elif method == "luminance":
        remove_fn = remove_bg_luminance
    elif method == "grabcut":
        remove_fn = remove_bg_grabcut
    else:
        raise ValueError(f"Unknown method: {method}")

    cached_mask = None
    start_time = time.time()

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Remove background
        if cache_mask and cached_mask is not None:
            # Reuse cached alpha mask with current frame colors
            avatar_rgba = np.zeros((*frame_rgb.shape[:2], 4), dtype=np.uint8)
            avatar_rgba[:, :, :3] = frame_rgb
            avatar_rgba[:, :, 3] = cached_mask
        else:
            avatar_rgba = remove_fn(frame_rgb)
            if cache_mask and i == 0:
                # Cache the mask from first frame
                cached_mask = avatar_rgba[:, :, 3].copy()
                print(f"[Background] Mask cached from frame 0")

        # Get background frame
        if bg_is_video:
            bg_idx = i % bg_frame_count
            bg_cap.set(cv2.CAP_PROP_POS_FRAMES, bg_idx)
            ret_bg, bg_frame = bg_cap.read()
            if not ret_bg:
                bg_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                _, bg_frame = bg_cap.read()
            bg_frame = cv2.resize(bg_frame, (width, height), interpolation=cv2.INTER_LANCZOS4)
            bg_rgb = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2RGB)
        else:
            bg_rgb = cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB)

        # Composite
        result = composite_frame(avatar_rgba, bg_rgb, effects)
        result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        writer.write(result_bgr)

        # Progress
        if (i + 1) % 50 == 0 or i == frame_count - 1:
            elapsed = time.time() - start_time
            fps_actual = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (frame_count - i - 1) / fps_actual if fps_actual > 0 else 0
            print(f"[Background] Frame {i+1}/{frame_count} ({fps_actual:.1f} fps, ETA: {eta:.0f}s)")

    cap.release()
    writer.release()
    if bg_is_video:
        bg_cap.release()

    elapsed = time.time() - start_time
    print(f"[Background] Video processing done in {elapsed:.1f}s")

    # Mux audio from original video
    print(f"[Background] Muxing audio...")
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", input_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-map", "0:v:0", "-map", "1:a:0?",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        output_path
    ]

    result = subprocess.run(mux_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[Background] ffmpeg warning: {result.stderr[-500:]}")
        # Try without audio if it fails
        print("[Background] Retrying without audio...")
        mux_cmd2 = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            output_path
        ]
        subprocess.run(mux_cmd2, check=True, capture_output=True)

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

    output_size = os.path.getsize(output_path)
    print(f"[Background] Output: {output_path} ({output_size // 1024}KB)")
    return output_path


###############################################################################
# Helper: resolve background path
###############################################################################

def resolve_background(bg_arg, style_arg):
    """
    Resolve background path from either --background or --bg-style.
    Returns (path, is_video).
    """
    if bg_arg:
        path = os.path.abspath(bg_arg)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Background not found: {path}")
        ext = os.path.splitext(path)[1].lower()
        is_video = ext in ('.mp4', '.mov', '.avi', '.webm', '.mkv')
        return path, is_video

    if style_arg:
        style = style_arg.lower().replace("-", "_")
        if style not in BG_STYLES:
            available = ", ".join(sorted(BG_STYLES.keys()))
            raise ValueError(f"Unknown style: {style_arg}. Available: {available}")
        path = os.path.join(ASSETS_DIR, BG_STYLES[style])
        if not os.path.exists(path):
            raise FileNotFoundError(f"Background file not found: {path}")
        return path, False

    # Default to cyberpunk
    default = os.path.join(ASSETS_DIR, BG_STYLES["cyberpunk"])
    if os.path.exists(default):
        print("[Background] Using default style: cyberpunk")
        return default, False
    raise FileNotFoundError(f"No background specified and default not found at {default}")


###############################################################################
# Layered scene video processing
###############################################################################

def process_video_layered(input_path, scene_name, output_path, method="rembg",
                          effects=None, cache_mask=True):
    """
    Process video with layered scene compositing (background → avatar → foreground).
    
    Args:
        input_path: Path to input avatar video
        scene_name: Name of scene in assets/scenes/
        output_path: Path to output video
        method: Background removal method
        effects: Dict of effects to apply
        cache_mask: Cache mask for faster processing
    """
    import_deps()
    
    print(f"[Scene] Processing: {os.path.basename(input_path)}")
    print(f"[Scene] Scene: {scene_name}")
    print(f"[Scene] Method: {method}")
    
    # Load scene
    scene = load_scene(scene_name)
    config = scene["config"]
    avatar_zone = config.get("avatar_zone", {})
    
    print(f"[Scene] Background: {scene['background_path']}")
    if scene['foreground_path']:
        print(f"[Scene] Foreground: {scene['foreground_path']}")
    
    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Output at scene resolution
    out_width = config.get("resolution", {}).get("width", FINAL_W)
    out_height = config.get("resolution", {}).get("height", FINAL_H)
    
    print(f"[Scene] Input: {src_width}x{src_height}, {fps}fps, {frame_count} frames")
    print(f"[Scene] Output: {out_width}x{out_height}")
    
    # Load background image
    bg_img = cv2.imread(scene["background_path"])
    if bg_img is None:
        raise RuntimeError(f"Cannot load background: {scene['background_path']}")
    bg_img = cv2.resize(bg_img, (out_width, out_height), interpolation=cv2.INTER_LANCZOS4)
    bg_rgb = cv2.cvtColor(bg_img, cv2.COLOR_BGR2RGB)
    
    # Load foreground image if exists
    fg_rgba = None
    if scene["foreground_path"]:
        fg_img = cv2.imread(scene["foreground_path"], cv2.IMREAD_UNCHANGED)
        if fg_img is not None:
            fg_img = cv2.resize(fg_img, (out_width, out_height), interpolation=cv2.INTER_LANCZOS4)
            if fg_img.shape[2] == 4:
                fg_rgba = cv2.cvtColor(fg_img, cv2.COLOR_BGRA2RGBA)
            else:
                # No alpha, create full opacity
                fg_rgba = np.zeros((out_height, out_width, 4), dtype=np.uint8)
                fg_rgba[:, :, :3] = cv2.cvtColor(fg_img, cv2.COLOR_BGR2RGB)
                fg_rgba[:, :, 3] = 255
    
    # Setup output
    temp_dir = tempfile.mkdtemp(prefix="ninja_scene_")
    temp_video = os.path.join(temp_dir, "video_no_audio.mp4")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(temp_video, fourcc, fps, (out_width, out_height))
    
    # Background removal function
    if method == "rembg":
        remove_fn = remove_bg_rembg
    elif method == "luminance":
        remove_fn = remove_bg_luminance
    elif method == "grabcut":
        remove_fn = remove_bg_grabcut
    else:
        raise ValueError(f"Unknown method: {method}")
    
    cached_mask = None
    start_time = time.time()
    
    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Remove background
        if cache_mask and cached_mask is not None:
            avatar_rgba = np.zeros((*frame_rgb.shape[:2], 4), dtype=np.uint8)
            avatar_rgba[:, :, :3] = frame_rgb
            avatar_rgba[:, :, 3] = cached_mask
        else:
            avatar_rgba = remove_fn(frame_rgb)
            if cache_mask and i == 0:
                cached_mask = avatar_rgba[:, :, 3].copy()
                print(f"[Scene] Mask cached from frame 0")
        
        # Layered composite
        result = composite_frame_layered(
            avatar_rgba, 
            bg_rgb, 
            foreground_rgba=fg_rgba,
            avatar_zone=avatar_zone,
            effects=effects
        )
        
        result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        writer.write(result_bgr)
        
        # Progress
        if (i + 1) % 50 == 0 or i == frame_count - 1:
            elapsed = time.time() - start_time
            fps_actual = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (frame_count - i - 1) / fps_actual if fps_actual > 0 else 0
            print(f"[Scene] Frame {i+1}/{frame_count} ({fps_actual:.1f} fps, ETA: {eta:.0f}s)")
    
    cap.release()
    writer.release()
    
    elapsed = time.time() - start_time
    print(f"[Scene] Video processing done in {elapsed:.1f}s")
    
    # Mux audio from original video
    print(f"[Scene] Muxing audio...")
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", input_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-map", "0:v:0", "-map", "1:a:0?",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        output_path
    ]
    
    result = subprocess.run(mux_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[Scene] ffmpeg warning: {result.stderr[-500:]}")
        print("[Scene] Retrying without audio...")
        mux_cmd2 = [
            "ffmpeg", "-y",
            "-i", temp_video,
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            output_path
        ]
        subprocess.run(mux_cmd2, check=True, capture_output=True)
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    output_size = os.path.getsize(output_path)
    print(f"[Scene] Output: {output_path} ({output_size // 1024}KB)")
    return output_path


###############################################################################
# Effect presets
###############################################################################

EFFECT_PRESETS = {
    "cyberpunk": {
        "vignette": True,
        "vignette_strength": 0.25,
        "glow": True,
        "glow_color": (0, 180, 255),  # cyan
        "ambient": True,
        "ambient_color": (0, 80, 200),
    },
    "dark_studio": {
        "vignette": True,
        "vignette_strength": 0.35,
    },
    "gaming": {
        "vignette": True,
        "vignette_strength": 0.2,
        "glow": True,
        "glow_color": (100, 0, 255),  # purple
        "ambient": True,
        "ambient_color": (80, 0, 180),
    },
    "dojo": {
        "vignette": True,
        "vignette_strength": 0.3,
        "glow": True,
        "glow_color": (200, 50, 0),  # warm red-orange
    },
    "dojo_layered": {
        "vignette": True,
        "vignette_strength": 0.25,
        "glow": True,
        "glow_color": (200, 120, 50),  # warm orange glow
        "warm_tint": True,
        "warm_tint_strength": 0.08,
    },
    "matrix": {
        "vignette": True,
        "vignette_strength": 0.2,
        "glow": True,
        "glow_color": (0, 255, 80),  # green
        "ambient": True,
        "ambient_color": (0, 150, 50),
    },
    "none": {},
    "minimal": {
        "vignette": True,
        "vignette_strength": 0.2,
    },
}


###############################################################################
# Main
###############################################################################

def parse_args():
    parser = argparse.ArgumentParser(
        description="Background compositor for Neurodivergent Ninja avatar videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Background Styles:
  cyberpunk    Dark with neon cyan/magenta accents and grid
  dark_studio  Clean dark gradient with subtle lighting
  gaming       RGB LED strip aesthetic
  dojo         Japanese-inspired dark warm tones
  matrix       Digital rain / tech green

Layered Scenes (with foreground depth):
  dojo_layered  Traditional dojo with foreground table for depth

Effect Presets:
  Automatically matched to bg-style/scene, or use --effects to set manually.
  --effects cyberpunk   → vignette + cyan glow + ambient light
  --effects minimal     → vignette only
  --effects none        → no effects

Examples:
  %(prog)s --input avatar.mp4 --bg-style cyberpunk --output out.mp4
  %(prog)s --input avatar.mp4 --background custom_bg.png --output out.mp4
  %(prog)s --input avatar.mp4 --bg-style dojo --method luminance --output out.mp4
  %(prog)s --input avatar.mp4 --scene dojo --output out.mp4  # Layered scene!
  %(prog)s --input avatar.mp4 --background animated_bg.mp4 --output out.mp4
        """
    )
    parser.add_argument("--input", "-i", required=True, help="Input avatar video (from Ditto)")
    parser.add_argument("--output", "-o", required=True, help="Output composited video")
    parser.add_argument("--background", "-b", help="Custom background image or video file")
    parser.add_argument("--bg-style", "-s", choices=list(BG_STYLES.keys()),
                        help="Built-in background style")
    parser.add_argument("--scene", choices=list(SCENE_STYLES.keys()) + list(SCENE_STYLES.values()),
                        help="Layered scene (background + foreground)")
    parser.add_argument("--method", "-m", choices=["rembg", "luminance", "grabcut"],
                        default="rembg", help="Background removal method (default: rembg)")
    parser.add_argument("--effects", "-e", choices=list(EFFECT_PRESETS.keys()),
                        help="Effect preset (default: matches bg-style)")
    parser.add_argument("--no-effects", action="store_true", help="Disable all effects")
    parser.add_argument("--no-cache", action="store_true",
                        help="Don't cache mask (slower but handles moving subjects)")
    parser.add_argument("--list-styles", action="store_true", help="List available background styles and scenes")

    # Allow --list-styles without requiring --input/--output
    if "--list-styles" in sys.argv:
        print("Available background styles:")
        for name, filename in sorted(BG_STYLES.items()):
            path = os.path.join(ASSETS_DIR, filename)
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"  {exists} {name:15s} → {filename}")
        
        print("\nLayered scenes (with foreground depth):")
        for name, scene_dir in sorted(SCENE_STYLES.items()):
            scene_path = os.path.join(SCENES_DIR, scene_dir)
            exists = "✅" if os.path.exists(scene_path) else "❌"
            print(f"  {exists} {name:15s} → scenes/{scene_dir}/")
        
        print(f"\nEffect presets: {', '.join(sorted(EFFECT_PRESETS.keys()))}")
        sys.exit(0)

    args = parser.parse_args()

    if args.list_styles:
        print("Available background styles:")
        for name, filename in sorted(BG_STYLES.items()):
            path = os.path.join(ASSETS_DIR, filename)
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"  {exists} {name:15s} → {filename}")
        
        print("\nLayered scenes (with foreground depth):")
        for name, scene_dir in sorted(SCENE_STYLES.items()):
            scene_path = os.path.join(SCENES_DIR, scene_dir)
            exists = "✅" if os.path.exists(scene_path) else "❌"
            print(f"  {exists} {name:15s} → scenes/{scene_dir}/")
        
        print(f"\nEffect presets: {', '.join(sorted(EFFECT_PRESETS.keys()))}")
        sys.exit(0)

    return args


def main():
    args = parse_args()
    
    # Check if using layered scene
    if args.scene:
        # Resolve scene name
        scene_name = SCENE_STYLES.get(args.scene, args.scene)
        
        # Resolve effects
        if args.no_effects:
            effects = None
        elif args.effects:
            effects = EFFECT_PRESETS.get(args.effects)
        else:
            # Try to match effect preset to scene
            effects = EFFECT_PRESETS.get(args.scene, EFFECT_PRESETS.get("dojo_layered"))
        
        # Process with layered scene
        process_video_layered(
            input_path=args.input,
            scene_name=scene_name,
            output_path=args.output,
            method=args.method,
            effects=effects,
            cache_mask=not args.no_cache,
        )
        return

    # Resolve background (legacy mode)
    bg_path, bg_is_video = resolve_background(args.background, args.bg_style)

    # Resolve effects
    if args.no_effects:
        effects = None
    elif args.effects:
        effects = EFFECT_PRESETS.get(args.effects)
    elif args.bg_style:
        effects = EFFECT_PRESETS.get(args.bg_style)
    else:
        effects = EFFECT_PRESETS.get("minimal")

    # Process
    process_video(
        input_path=args.input,
        bg_path=bg_path,
        output_path=args.output,
        method=args.method,
        effects=effects,
        bg_is_video=bg_is_video,
        cache_mask=not args.no_cache,
    )


if __name__ == "__main__":
    main()
