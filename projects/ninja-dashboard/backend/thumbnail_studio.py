"""Thumbnail Studio — standalone thumbnail generation for the Dojo.

Reuses Nano Banana Pro (Gemini image gen) from ninja_thumbnail.py
with additional features: style presets, inspiration images, gallery, attach-to-job.
"""
import asyncio
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

# Import generation helpers from ninja_thumbnail.py
SCRIPTS_DIR = Path("/data/scripts") if Path("/data/scripts").exists() else Path.home() / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from ninja_thumbnail import _detect_topic_icons, _extract_headline, generate_thumbnail

THUMBNAILS_DIR = Path(os.environ.get("THUMBNAILS_DIR", Path.home() / "output" / "thumbnails"))
UPLOADS_SUBDIR = THUMBNAILS_DIR / "uploads"

# In-memory generation tracking (fire-and-forget, no DB needed)
_active_generations: dict[str, dict] = {}

router = APIRouter(prefix="/api/thumbnail-studio", tags=["thumbnail-studio"])


def _safe_resolve(filename: str) -> Optional[Path]:
    """Resolve filename within THUMBNAILS_DIR, blocking directory traversal."""
    try:
        resolved = (THUMBNAILS_DIR / filename).resolve()
    except Exception:
        return None
    if not resolved.is_relative_to(THUMBNAILS_DIR.resolve()):
        return None
    return resolved


def _gallery_items(limit: int = 20) -> list[dict]:
    """List recent thumbnails sorted by mtime descending."""
    if not THUMBNAILS_DIR.exists():
        return []
    items = []
    for f in THUMBNAILS_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            stat = f.stat()
            items.append({
                "filename": f.name,
                "size_kb": round(stat.st_size / 1024, 1),
                "created_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "path": str(f),
            })
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return items[:limit]


async def _run_generation(
    gen_id: str,
    topic: str,
    style: str,
    aspect_ratio: str,
    headline: Optional[str],
    inspiration_path: Optional[str],
    ws_manager,
) -> None:
    """Run thumbnail generation in background thread, broadcast WS events."""
    try:
        _active_generations[gen_id]["status"] = "generating"
        await ws_manager.broadcast("thumbnail_generating", {"id": gen_id, "topic": topic})

        # Build output filename
        short_id = gen_id[:8]
        output_name = f"thumb_studio_{short_id}_{style}.png"
        output_path = str(THUMBNAILS_DIR / output_name)

        # Determine reference image
        ref_image = inspiration_path
        if not ref_image:
            default_ref = Path.home() / "assets" / "reference" / "ninja_helmet_v3_futuristic.jpg"
            if default_ref.exists():
                ref_image = str(default_ref)

        # Override headline in the generate function by monkey-patching topic
        # We'll call generate_thumbnail with the topic but customize via env/params
        final_headline = headline or _extract_headline(topic)

        # Run blocking generation in thread pool
        def _gen():
            from google import genai
            from google.genai import types

            api_key = os.environ.get("GOOGLE_API_KEY")
            client = genai.Client(api_key=api_key)

            topic_icons = _detect_topic_icons(topic)
            style_prompts = {
                "engaging": "looking directly at viewer, digital goggle eyes showing curious/interested expression, one hand gesturing toward the topic",
                "shocked": "digital goggle eyes wide with shock/surprise expression, hands up in amazement, dramatic reaction",
                "thinking": "hand on chin, digital goggle eyes showing contemplative/squinting expression, looking slightly upward",
                "pointing": "confidently pointing at the main subject, digital goggle eyes showing determined expression",
                "excited": "energetic pose, both hands animated, digital goggle eyes showing excited/happy expression with upward curved LED eyes",
            }
            ninja_pose = style_prompts.get(style, style_prompts["engaging"])

            prompt = f"""Create a YouTube thumbnail image with these exact specifications:

SUBJECT: A 3D Pixar-style animated ninja character - cute but cool, wearing DIGITAL GOGGLES/VISOR over eyes with glowing LED digital eyes visible through the goggles (the goggles ARE the character's eyes - no human eyes visible), black hood and mask covering lower face, black tactical outfit with gray armor plating and blue LED accents, katana on back. Pixar/Disney animation style with soft rounded features. {ninja_pose}

CRITICAL: The ninja MUST wear digital goggles/visor - this is the character's signature look. The goggle lenses show expressive digital/LED eyes that convey emotion. No human eyes - only digital goggle eyes.

COMPOSITION:
- Character on the right side (1/3 of frame)
- Left 2/3 shows a visual representation of: {topic}
- {topic_icons}
- Bold, eye-catching colors
- High contrast for mobile visibility

STYLE:
- 3D Pixar/Disney animation style (like The Incredibles or Big Hero 6)
- Soft, appealing character design with expressive digital goggle eyes
- {aspect_ratio} aspect ratio
- Clean, uncluttered composition
- Tech/gaming YouTube aesthetic
- Dramatic lighting with blue accent rim lights
- Slightly exaggerated expressions for thumbnail appeal

TEXT ELEMENTS (IMPORTANT - include these in the image):
- Large, bold headline text: "{final_headline}" - positioned prominently (top or left area), white or bright yellow text with black outline/shadow for readability
- Small "NEURODIVERGENT NINJA" or ninja star logo/branding in corner (subtle but visible)
- Text should be short, punchy, and scroll-stopping
- Use bold sans-serif font style (like Impact or Bebas Neue aesthetic)

Make it scroll-stopping and clickable!"""

            # Build content parts
            contents = []
            ref_data = None
            if ref_image and Path(ref_image).exists():
                with open(ref_image, "rb") as f:
                    ref_data = f.read()

            if inspiration_path and Path(inspiration_path).exists():
                with open(inspiration_path, "rb") as f:
                    insp_data = f.read()
                contents.append(types.Part.from_bytes(data=insp_data, mime_type="image/jpeg"))
                contents.append(f"Use this image as style/composition inspiration. {prompt}")
            elif ref_data:
                contents.append(types.Part.from_bytes(data=ref_data, mime_type="image/jpeg"))
                contents.append(f"Using this exact ninja character design (same face, outfit, colors), create a thumbnail: {prompt}")
            else:
                contents.append(prompt)

            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",  # Nano Banana Pro 2
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"],
                    image_config=types.ImageConfig(
                        aspectRatio=aspect_ratio,
                    ),
                ),
            )

            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(part.inline_data.data)
                    return output_path
            return None

        result_path = await asyncio.to_thread(_gen)

        if result_path:
            _active_generations[gen_id]["status"] = "ready"
            _active_generations[gen_id]["filename"] = Path(result_path).name
            await ws_manager.broadcast("thumbnail_ready", {
                "id": gen_id,
                "filename": Path(result_path).name,
                "topic": topic,
            })
        else:
            _active_generations[gen_id]["status"] = "error"
            _active_generations[gen_id]["error"] = "No image in response"
            await ws_manager.broadcast("thumbnail_error", {
                "id": gen_id,
                "error": "No image in response",
            })

    except Exception as e:
        _active_generations[gen_id]["status"] = "error"
        _active_generations[gen_id]["error"] = str(e)[:500]
        await ws_manager.broadcast("thumbnail_error", {
            "id": gen_id,
            "error": str(e)[:500],
        })


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate_studio_thumbnail(payload: dict) -> dict:
    topic = payload.get("topic", "").strip()
    if not topic:
        raise HTTPException(400, "topic is required")

    style = payload.get("style", "engaging")
    aspect_ratio = payload.get("aspect_ratio", "9:16")
    headline = payload.get("headline") or None

    gen_id = str(uuid.uuid4())
    _active_generations[gen_id] = {
        "status": "queued",
        "topic": topic,
        "style": style,
        "aspect_ratio": aspect_ratio,
    }

    # Get ws_manager from app state (injected at startup)
    from main import ws_manager
    asyncio.create_task(_run_generation(gen_id, topic, style, aspect_ratio, headline, None, ws_manager))

    return {"id": gen_id, "status": "generating"}


@router.post("/generate-from-image")
async def generate_from_image(
    topic: str = Form(...),
    style: str = Form("engaging"),
    aspect_ratio: str = Form("9:16"),
    headline: str = Form(None),
    file: UploadFile = File(...),
) -> dict:
    # Save uploaded inspiration image
    UPLOADS_SUBDIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "ref.jpg").suffix or ".jpg"
    upload_name = f"insp_{uuid.uuid4().hex[:8]}{ext}"
    upload_path = UPLOADS_SUBDIR / upload_name

    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)

    gen_id = str(uuid.uuid4())
    _active_generations[gen_id] = {
        "status": "queued",
        "topic": topic,
        "style": style,
        "aspect_ratio": aspect_ratio,
    }

    from main import ws_manager
    asyncio.create_task(
        _run_generation(gen_id, topic, style, aspect_ratio, headline or None, str(upload_path), ws_manager)
    )

    return {"id": gen_id, "status": "generating"}


@router.get("/gallery")
async def get_gallery() -> list[dict]:
    return await asyncio.to_thread(_gallery_items)


@router.get("/status/{gen_id}")
async def get_generation_status(gen_id: str) -> dict:
    gen = _active_generations.get(gen_id)
    if not gen:
        raise HTTPException(404, "Generation not found")
    return {"id": gen_id, **gen}


@router.get("/image/{filename}")
async def serve_thumbnail_image(filename: str) -> Response:
    path = _safe_resolve(filename)
    if not path or not path.exists() or not path.is_file():
        raise HTTPException(404, "Thumbnail not found")

    ext = path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(ext, "image/png")

    import aiofiles
    async with aiofiles.open(path, "rb") as f:
        content = await f.read()
    return Response(content=content, media_type=mime, headers={"Cache-Control": "no-cache"})


@router.get("/download/{filename}")
async def download_thumbnail(filename: str) -> FileResponse:
    path = _safe_resolve(filename)
    if not path or not path.exists() or not path.is_file():
        raise HTTPException(404, "Thumbnail not found")
    return FileResponse(path=path, media_type="image/png", filename=path.name)


@router.delete("/{filename}")
async def delete_thumbnail(filename: str) -> dict:
    path = _safe_resolve(filename)
    if not path or not path.exists():
        raise HTTPException(404, "Thumbnail not found")
    path.unlink()
    return {"deleted": filename}


@router.post("/attach/{filename}")
async def attach_to_job(filename: str, payload: dict) -> dict:
    job_id = payload.get("job_id")
    if not job_id:
        raise HTTPException(400, "job_id is required")

    thumb_path = _safe_resolve(filename)
    if not thumb_path or not thumb_path.exists():
        raise HTTPException(404, "Thumbnail not found")

    from jobs import get_job, update_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Copy thumbnail next to the video as {stem}.thumb.png
    output_path = job.get("output_path")
    if output_path and Path(output_path).exists():
        video_path = Path(output_path)
        dest = video_path.parent / f"{video_path.stem}.thumb.png"
        shutil.copy2(thumb_path, dest)
        new_thumb_path = str(dest)
    else:
        # No video yet — just reference the studio thumbnail directly
        new_thumb_path = str(thumb_path)

    update_job(job_id, thumb_path=new_thumb_path)

    from main import ws_manager
    updated_job = get_job(job_id)
    await ws_manager.broadcast("job_updated", updated_job)

    return {"attached": True, "job_id": job_id, "thumb_path": new_thumb_path}
