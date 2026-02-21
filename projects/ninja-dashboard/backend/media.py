"""Byte-range video/thumb serving + safe_resolve — ported from preview_server.py."""
import asyncio
from pathlib import Path
from typing import AsyncGenerator, Optional, Tuple

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse, Response

import os

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", Path.home() / "output"))
CHUNK_SIZE = 64 * 1024  # 64 KB — good for iPhone Safari streaming


def safe_resolve(filename: str, base_dir: Path = OUTPUT_DIR) -> Optional[Path]:
    """Resolve filename within base_dir, blocking directory traversal."""
    try:
        resolved = (base_dir / filename).resolve()
    except Exception:
        return None
    if not resolved.is_relative_to(base_dir.resolve()):
        return None
    return resolved


def get_thumbnail_for_video(video_path: Path) -> Optional[Path]:
    """Find a matching thumbnail for a video (same stem with thumb/thumbnail suffix)."""
    if not video_path:
        return None
    stem = video_path.stem
    parent = video_path.parent
    for pattern in [
        f"{stem}.thumb.png", f"{stem}.thumb.jpg",
        f"{stem}_thumb.png", f"{stem}_thumb.jpg",
        f"{stem}_thumb_v2.png", f"{stem}_thumb_v2.jpg",
    ]:
        thumb = parent / pattern
        if thumb.exists():
            return thumb
    # Also check for thumbnails sharing the base name prefix (before timestamp)
    base = stem.rsplit("_", 2)[0] if "_" in stem else stem
    for ext in ("png", "jpg"):
        for thumb in parent.glob(f"{base}*thumb*.{ext}"):
            return thumb
    return None


def _parse_range_header(range_header: str, file_size: int) -> Tuple[int, int]:
    """Parse Range: bytes=start-end header."""
    try:
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0]) if byte_range[0] else 0
        end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
        end = min(end, file_size - 1)
        start = max(0, start)
        return start, end
    except (ValueError, IndexError):
        return 0, file_size - 1


async def _stream_file(path: Path, start: int, end: int) -> AsyncGenerator[bytes, None]:
    """Async generator that streams a byte range from a file in 64 KB chunks."""
    loop = asyncio.get_event_loop()

    def _read_chunks() -> list[bytes]:
        chunks = []
        with open(path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = f.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
        return chunks

    chunks = await loop.run_in_executor(None, _read_chunks)
    for chunk in chunks:
        yield chunk


async def serve_video(filename: str, request: Request) -> StreamingResponse:
    """Serve a video file with HTTP 206 byte-range support (required for iPhone Safari)."""
    video_path = safe_resolve(filename, OUTPUT_DIR)
    if not video_path or not video_path.exists() or not video_path.is_file():
        raise HTTPException(404, "Video not found")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        start, end = _parse_range_header(range_header, file_size)
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(
            _stream_file(video_path, start, end),
            status_code=206,
            headers=headers,
        )
    else:
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        }
        return StreamingResponse(
            _stream_file(video_path, 0, file_size - 1),
            status_code=200,
            headers=headers,
        )


async def serve_video_download(filename: str) -> Response:
    """Serve a video file as a download (Content-Disposition: attachment)."""
    video_path = safe_resolve(filename, OUTPUT_DIR)
    if not video_path or not video_path.exists() or not video_path.is_file():
        raise HTTPException(404, "Video not found")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=video_path.name,
    )


async def serve_thumb(filename: str) -> Response:
    """Serve a thumbnail image."""
    thumb_path = safe_resolve(filename, OUTPUT_DIR)
    if not thumb_path or not thumb_path.exists() or not thumb_path.is_file():
        raise HTTPException(404, "Thumbnail not found")

    ext = thumb_path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")

    import aiofiles
    async with aiofiles.open(thumb_path, "rb") as f:
        content = await f.read()
    return Response(content=content, media_type=mime, headers={"Cache-Control": "no-cache"})
