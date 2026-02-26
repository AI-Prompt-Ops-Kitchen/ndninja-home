"""The Dojo — Content Pipeline Dashboard backend.
FastAPI app: all routes + WebSocket manager.
Run with: uvicorn main:app --host 0.0.0.0 --port 8090 --workers 1
"""
import asyncio
import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from jobs import create_job, delete_job, get_job, init_db, list_jobs, transition, update_job
from media import OUTPUT_DIR, get_thumbnail_for_video, safe_resolve, serve_thumb, serve_video
from pipeline import BROLL_DIR, run_pipeline
from scriptgen import generate_script

from broll_library import (
    register_clip,
    get_clip,
    list_library_clips,
    update_clip,
    soft_delete_clip,
    bump_last_used,
    add_tags,
    remove_tag,
    list_all_tags,
    list_all_games,
    bulk_add_tags,
    bulk_set_permanent,
    bulk_soft_delete,
)
from broll_previews import extract_metadata, generate_clip_assets
from auto_tagger import auto_tag_clip

from broll_db import (
    create_candidate,
    get_candidate,
    get_full_session,
    get_slot,
    init_broll_db,
    update_candidate,
    update_session,
    update_slot,
)
from broll_discovery import clip_youtube, download_clip, run_discovery
from thumbnail_studio import router as thumbnail_studio_router, THUMBNAILS_DIR

# Rasengan event emitter (fire-and-forget, never blocks)
def _rasengan_emit(event_type: str, payload: dict | None = None) -> None:
    try:
        import httpx
        url = os.environ.get("RASENGAN_URL", "http://rasengan:8050")
        httpx.post(f"{url}/events", json={"event_type": event_type, "source": "dojo", "payload": payload or {}}, timeout=2.0)
    except Exception:
        pass

UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", Path.home() / "uploads"))
UPLOADS_DIR.mkdir(exist_ok=True)
BROLL_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="The Dojo — Ninja Content Pipeline")
app.include_router(thumbnail_studio_router)

# Allow Vite dev server on 5173 during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class WSManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, event_type: str, data: object) -> None:
        msg = json.dumps({"type": event_type, "data": data})
        dead: set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.add(ws)
        self._connections -= dead


ws_manager = WSManager()


# ---------------------------------------------------------------------------
# Kuchiyose — Summon tracking (in-memory, --workers 1 safe)
# ---------------------------------------------------------------------------

@dataclass
class Summon:
    summon_id: str
    name: str
    animal: str
    color: str
    specialty: str
    status: str  # active | thinking | done | error
    agent_type: str
    session_id: str
    summoned_at: float = field(default_factory=time.time)

_summons: dict[str, Summon] = {}


async def _prune_dismissed_summon(summon_id: str) -> None:
    """Remove a dismissed summon after 30s (gives frontend time for exit animation)."""
    await asyncio.sleep(30)
    _summons.pop(summon_id, None)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup() -> None:
    init_db()
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        init_broll_db()
    except Exception as e:
        print(f"⚠️ B-roll Wingman DB init failed (feature degraded): {e}")
    # Recover any jobs that were stuck when the server last died.
    all_jobs = list_jobs()

    # Uploads that were in progress — no way to resume, mark as error
    for job in [j for j in all_jobs if j["status"] == "uploading"]:
        await asyncio.to_thread(
            update_job, job["id"], status="error",
            error_msg="Server restarted during upload — retry upload",
        )

    # Generating jobs — check if output was produced before crash
    stuck = [j for j in all_jobs if j["status"] == "generating"]
    for job in stuck:
        output_path = await asyncio.to_thread(_find_output_for_job, job["id"])
        if output_path:
            from media import get_thumbnail_for_video
            thumb = get_thumbnail_for_video(Path(output_path))
            await asyncio.to_thread(
                transition, job["id"], "ready_for_review",
                output_path=output_path,
                thumb_path=str(thumb) if thumb else None,
            )
        else:
            await asyncio.to_thread(
                update_job, job["id"], status="error",
                error_msg="Server restarted during generation — retry to re-run",
            )


def _find_output_for_job(job_id: str) -> Optional[str]:
    """Scan output dir for a completed mp4 matching this job's prefix."""
    from pipeline import OUTPUT_DIR
    prefix = f"ninja_dash_{job_id[:8]}_"
    mp4s = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
    for mp4 in mp4s[:10]:
        if mp4.stem.startswith(prefix):
            return str(mp4)
    return None


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws_manager.connect(ws)
    try:
        # Send full job list + active summons immediately on connect
        jobs = await asyncio.to_thread(list_jobs)
        await ws.send_text(json.dumps({"type": "job_list", "data": jobs}))
        if _summons:
            await ws.send_text(json.dumps({
                "type": "summon_list",
                "data": [asdict(s) for s in _summons.values()],
            }))

        # Stay alive; client sends "ping" every 25s to prevent idle timeout
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.post("/api/summons/event")
async def api_summon_event(payload: dict) -> dict:
    """Receive summon events from the kuchiyose hook."""
    event_type = payload.get("event_type", "")
    data = payload.get("payload", {})
    summon_id = data.get("summon_id", "")

    if not summon_id:
        raise HTTPException(400, "payload.summon_id required")

    if event_type == "agent.summoned":
        summon = Summon(
            summon_id=summon_id,
            name=data.get("name", "Kuchiyose"),
            animal=data.get("animal", "scroll"),
            color=data.get("color", "cyan-400"),
            specialty=data.get("specialty", ""),
            status=data.get("status", "active"),
            agent_type=data.get("agent_type", ""),
            session_id=data.get("session_id", ""),
        )
        _summons[summon_id] = summon
        await ws_manager.broadcast("summon_appeared", asdict(summon))
        return {"ok": True, "summon_id": summon_id}

    elif event_type == "agent.dismissed":
        summon = _summons.get(summon_id)
        if summon:
            summon.status = "done"
            await ws_manager.broadcast("summon_dismissed", asdict(summon))
            asyncio.create_task(_prune_dismissed_summon(summon_id))
        return {"ok": True, "summon_id": summon_id}

    return {"ok": False, "error": f"Unknown event_type: {event_type}"}


@app.get("/api/summons")
async def api_list_summons() -> list[dict]:
    return [asdict(s) for s in _summons.values()]


@app.get("/api/jobs")
async def api_list_jobs() -> list[dict]:
    return await asyncio.to_thread(list_jobs)


@app.post("/api/jobs/article")
async def api_submit_article(payload: dict) -> dict:
    url: Optional[str] = payload.get("url") or None
    text: Optional[str] = payload.get("text") or None
    target_length_sec: int = int(payload.get("target_length_sec", 60))
    broll_count: int = int(payload.get("broll_count", 4))
    broll_duration: float = float(payload.get("broll_duration", 10.0))
    dual_anchor: bool = bool(payload.get("dual_anchor", False))

    if not url and not text:
        raise HTTPException(400, "Provide url or text")

    job = await asyncio.to_thread(create_job, url, text, target_length_sec, broll_count, broll_duration, dual_anchor)
    await ws_manager.broadcast("job_created", job)
    asyncio.get_event_loop().run_in_executor(None, _rasengan_emit, "dojo.job_created", {"job_id": job["id"], "dual_anchor": dual_anchor})

    # Scriptgen runs in the background — UI will receive WS update when done
    asyncio.create_task(_run_scriptgen(job["id"], url, text, target_length_sec, dual_anchor=dual_anchor))

    return job


@app.post("/api/jobs/{job_id}/script-edit")
async def api_edit_script(job_id: str, payload: dict) -> dict:
    script_text: str = payload.get("script_text", "")
    job = await asyncio.to_thread(update_job, job_id, script_text=script_text)
    if not job:
        raise HTTPException(404, "Job not found")
    await ws_manager.broadcast("job_updated", job)
    return job


@app.post("/api/jobs/{job_id}/script-approve")
async def api_approve_script(job_id: str) -> dict:
    job = await asyncio.to_thread(get_job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job = await asyncio.to_thread(transition, job_id, "generating")
    await ws_manager.broadcast("job_updated", job)
    asyncio.create_task(_run_pipeline_task(job_id, job.get("script_text") or ""))
    return job


@app.post("/api/jobs/{job_id}/approve")
async def api_approve_video(job_id: str) -> dict:
    job = await asyncio.to_thread(get_job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Create .approved sentinel file (keeps systemd watcher compatibility)
    output_path = job.get("output_path")
    if output_path:
        video_path = Path(output_path)
        if video_path.exists():
            (video_path.parent / f"{video_path.stem}.approved").touch()

    job = await asyncio.to_thread(transition, job_id, "approved")
    await ws_manager.broadcast("job_updated", job)
    return job


@app.post("/api/jobs/{job_id}/discard")
async def api_discard_job(job_id: str) -> dict:
    job = await asyncio.to_thread(get_job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Create .rejected sentinel file
    output_path = job.get("output_path")
    if output_path:
        video_path = Path(output_path)
        if video_path.exists():
            (video_path.parent / f"{video_path.stem}.rejected").touch()

    job = await asyncio.to_thread(transition, job_id, "discarded")
    await ws_manager.broadcast("job_updated", job)
    return job


@app.post("/api/jobs/{job_id}/retry")
async def api_retry_job(job_id: str) -> dict:
    job = await asyncio.to_thread(get_job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    retry_count = (job.get("retry_count") or 0) + 1
    job = await asyncio.to_thread(
        transition, job_id, "generating",
        retry_count=retry_count, error_msg=None,
    )
    await ws_manager.broadcast("job_updated", job)
    asyncio.create_task(_run_pipeline_task(job_id, job.get("script_text") or ""))
    return job


@app.get("/api/download/{filename:path}")
async def api_download_video(filename: str):
    from media import serve_video_download
    return await serve_video_download(filename)


@app.get("/api/video/{filename:path}")
async def api_stream_video(filename: str, request: Request):
    return await serve_video(filename, request)


@app.get("/api/thumb/{filename:path}")
async def api_serve_thumb(filename: str):
    return await serve_thumb(filename)


@app.get("/api/broll")
async def api_list_broll() -> list[dict]:
    clips = []
    for f in sorted(BROLL_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        clips.append({
            "filename": f.name,
            "size_mb": round(stat.st_size / 1_048_576, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        })
    return clips


@app.post("/api/broll/upload")
async def api_upload_broll(file: UploadFile = File(...)) -> dict:
    safe_name = Path(file.filename or "clip").name
    if not safe_name.lower().endswith((".mp4", ".mov", ".webm")):
        raise HTTPException(400, "Only video files accepted for B-roll")
    dest = BROLL_DIR / safe_name
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        n = 1
        while dest.exists():
            dest = BROLL_DIR / f"{stem}_{n}{suffix}"
            n += 1
        safe_name = dest.name
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(64 * 1024):
            await f.write(chunk)

    # Register in B-roll library + kick off background enrichment
    asyncio.create_task(_enrich_broll_clip(safe_name, str(dest), source="upload"))

    return {"filename": safe_name, "path": str(dest)}


@app.post("/api/broll/clip-youtube")
async def api_clip_youtube(payload: dict) -> dict:
    url = payload.get("url")
    start = payload.get("start")
    end = payload.get("end")
    filename = payload.get("filename") or None

    if not url or not start or not end:
        raise HTTPException(400, "url, start, and end are required")

    try:
        result = await clip_youtube(url, start, end, filename)
        # Register in library with source URL
        if result.get("filename"):
            asyncio.create_task(_enrich_broll_clip(
                result["filename"],
                str(BROLL_DIR / result["filename"]),
                source="autoclip",
                source_url=url,
            ))
        return result
    except Exception as e:
        raise HTTPException(500, str(e)[:500])


@app.delete("/api/jobs/{job_id}")
async def api_delete_job(job_id: str) -> dict:
    job = await asyncio.to_thread(get_job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] in ("pending", "script_ready", "generating"):
        raise HTTPException(400, "Cannot delete an active job")
    await asyncio.to_thread(delete_job, job_id)
    await ws_manager.broadcast("job_deleted", {"id": job_id})
    return {"deleted": job_id}


@app.delete("/api/broll/{filename}")
async def api_delete_broll(filename: str) -> dict:
    path = safe_resolve(filename, BROLL_DIR)
    if not path or not path.exists():
        raise HTTPException(404, "Clip not found")
    path.unlink()
    return {"deleted": filename}


# ---------------------------------------------------------------------------
# B-roll Library endpoints (Phase 2)
# ---------------------------------------------------------------------------

broll_library_router = APIRouter(prefix="/api/broll/library", tags=["broll-library"])

@broll_library_router.get("")
async def api_list_library(
    page: int = 1,
    per_page: int = 24,
    game: Optional[str] = None,
    tag: Optional[str] = None,
    source: Optional[str] = None,
    permanent: Optional[bool] = None,
    expiring_soon: bool = False,
    search: Optional[str] = None,
    sort: str = "created_at_desc",
) -> dict:
    items, total = await asyncio.to_thread(
        list_library_clips,
        page=page, per_page=per_page, game=game, tag=tag,
        source=source, permanent=permanent, expiring_soon=expiring_soon,
        search=search, sort=sort,
    )
    return {"items": items, "total": total, "page": page, "per_page": per_page}


@broll_library_router.get("/tags")
async def api_library_tags() -> list[dict]:
    return await asyncio.to_thread(list_all_tags)


@broll_library_router.get("/games")
async def api_library_games() -> list[dict]:
    return await asyncio.to_thread(list_all_games)


@broll_library_router.get("/thumb/{clip_id}")
async def api_library_thumb(clip_id: str):
    from fastapi.responses import FileResponse
    clip = await asyncio.to_thread(get_clip, clip_id)
    if not clip or not clip.get("thumb_path"):
        raise HTTPException(404, "No thumbnail for this clip")
    thumb = Path(clip["thumb_path"])
    if not thumb.exists():
        raise HTTPException(404, "Thumbnail file missing")
    return FileResponse(str(thumb), media_type="image/webp", headers={"Cache-Control": "public, max-age=86400"})


@broll_library_router.get("/preview/{clip_id}")
async def api_library_preview(clip_id: str, request: Request):
    clip = await asyncio.to_thread(get_clip, clip_id)
    if not clip or not clip.get("preview_path"):
        raise HTTPException(404, "No preview for this clip")
    preview = Path(clip["preview_path"])
    if not preview.exists():
        raise HTTPException(404, "Preview file missing")
    from fastapi.responses import FileResponse
    return FileResponse(str(preview), media_type="video/webm", headers={"Cache-Control": "public, max-age=86400"})


@broll_library_router.get("/stream/{clip_id}")
async def api_library_stream(clip_id: str, request: Request):
    """Stream full clip for in-browser playback."""
    clip = await asyncio.to_thread(get_clip, clip_id)
    if not clip or not clip.get("filepath"):
        raise HTTPException(404, "Clip not found")
    fp = Path(clip["filepath"])
    if not fp.exists():
        raise HTTPException(404, "File not found on disk")
    return await serve_video(f"broll/{fp.name}", request)


# Bulk operations (put before {clip_id} to avoid path conflicts)
@broll_library_router.post("/bulk/tags")
async def api_bulk_tags(payload: dict) -> dict:
    clip_ids = payload.get("clip_ids", [])
    tags_list = payload.get("tags", [])
    if not clip_ids or not tags_list:
        raise HTTPException(400, "clip_ids and tags required")
    count = await asyncio.to_thread(bulk_add_tags, clip_ids, tags_list)
    return {"updated": count}


@broll_library_router.post("/bulk/permanent")
async def api_bulk_permanent(payload: dict) -> dict:
    clip_ids = payload.get("clip_ids", [])
    permanent = bool(payload.get("permanent", True))
    if not clip_ids:
        raise HTTPException(400, "clip_ids required")
    count = await asyncio.to_thread(bulk_set_permanent, clip_ids, permanent)
    return {"updated": count}


@broll_library_router.post("/bulk/delete")
async def api_bulk_delete(payload: dict) -> dict:
    clip_ids = payload.get("clip_ids", [])
    if not clip_ids:
        raise HTTPException(400, "clip_ids required")
    count = await asyncio.to_thread(bulk_soft_delete, clip_ids)
    return {"deleted": count}


@broll_library_router.get("/{clip_id}")
async def api_get_library_clip(clip_id: str) -> dict:
    clip = await asyncio.to_thread(get_clip, clip_id)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@broll_library_router.patch("/{clip_id}")
async def api_update_library_clip(clip_id: str, payload: dict) -> dict:
    allowed = {"game", "tags", "permanent", "source", "source_url"}
    fields = {k: v for k, v in payload.items() if k in allowed}
    if not fields:
        raise HTTPException(400, "No valid fields to update")
    clip = await asyncio.to_thread(update_clip, clip_id, **fields)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@broll_library_router.delete("/{clip_id}")
async def api_delete_library_clip(clip_id: str) -> dict:
    ok = await asyncio.to_thread(soft_delete_clip, clip_id)
    if not ok:
        raise HTTPException(404, "Clip not found")
    return {"deleted": clip_id}


@broll_library_router.post("/{clip_id}/tags")
async def api_add_clip_tags(clip_id: str, payload: dict) -> dict:
    tags_list = payload.get("tags", [])
    if not tags_list:
        raise HTTPException(400, "tags list required")
    clip = await asyncio.to_thread(add_tags, clip_id, tags_list)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@broll_library_router.delete("/{clip_id}/tags/{tag_name}")
async def api_remove_clip_tag(clip_id: str, tag_name: str) -> dict:
    clip = await asyncio.to_thread(remove_tag, clip_id, tag_name)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@broll_library_router.post("/{clip_id}/permanent")
async def api_toggle_permanent(clip_id: str, payload: dict) -> dict:
    permanent = bool(payload.get("permanent", True))
    clip = await asyncio.to_thread(update_clip, clip_id, permanent=permanent)
    if not clip:
        raise HTTPException(404, "Clip not found")
    return clip


@broll_library_router.post("/{clip_id}/bump")
async def api_bump_clip(clip_id: str) -> dict:
    await asyncio.to_thread(bump_last_used, clip_id)
    return {"bumped": clip_id}


app.include_router(broll_library_router)


@app.post("/api/upload")
async def api_upload_file(file: UploadFile = File(...)) -> dict:
    safe_name = Path(file.filename or "upload").name
    dest = UPLOADS_DIR / safe_name
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        n = 1
        while dest.exists():
            dest = UPLOADS_DIR / f"{stem}_{n}{suffix}"
            n += 1
        safe_name = dest.name
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(64 * 1024):
            await f.write(chunk)
    return {"filename": safe_name, "path": str(dest)}


# ---------------------------------------------------------------------------
# B-roll Wingman endpoints
# ---------------------------------------------------------------------------

@app.get("/api/broll-wingman/{job_id}")
async def api_get_broll_session(job_id: str) -> dict:
    session = await asyncio.to_thread(get_full_session, job_id)
    if not session:
        return {"session": None}
    return {"session": session}


@app.post("/api/broll-wingman/{job_id}/start")
async def api_start_broll_discovery(job_id: str) -> dict:
    job = await asyncio.to_thread(get_job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    script_text = job.get("script_text") or ""
    if not script_text:
        raise HTTPException(400, "Job has no script text")
    broll_count = int(job.get("broll_count", 4))
    asyncio.create_task(run_discovery(job_id, script_text, broll_count, ws_manager))
    return {"started": True, "job_id": job_id}


@app.post("/api/broll-wingman/slots/{slot_id}/approve")
async def api_approve_broll_slot(slot_id: str, payload: dict) -> dict:
    candidate_id = payload.get("candidate_id")
    if not candidate_id:
        raise HTTPException(400, "candidate_id required")

    slot = await asyncio.to_thread(get_slot, slot_id)
    if not slot:
        raise HTTPException(404, "Slot not found")

    cand = await asyncio.to_thread(get_candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")

    # Mark slot as approved
    await asyncio.to_thread(update_slot, slot_id, status="approved", approved_candidate_id=candidate_id)

    # Start download in background
    asyncio.create_task(_download_and_broadcast(slot_id, candidate_id, slot.get("session_id")))

    await ws_manager.broadcast("broll_slot_approved", {
        "slot_id": slot_id,
        "candidate_id": candidate_id,
    })
    return {"approved": True, "slot_id": slot_id, "candidate_id": candidate_id}


@app.post("/api/broll-wingman/slots/{slot_id}/skip")
async def api_skip_broll_slot(slot_id: str) -> dict:
    slot = await asyncio.to_thread(get_slot, slot_id)
    if not slot:
        raise HTTPException(404, "Slot not found")

    await asyncio.to_thread(update_slot, slot_id, status="skipped")

    await ws_manager.broadcast("broll_slot_skipped", {
        "slot_id": slot_id,
    })

    # Check if all slots resolved → mark session completed
    await _check_session_complete(slot["session_id"])

    return {"skipped": True, "slot_id": slot_id}


@app.post("/api/broll-wingman/slots/{slot_id}/assign-local")
async def api_assign_local_broll(slot_id: str, payload: dict) -> dict:
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(400, "filename required")

    local_path = BROLL_DIR / Path(filename).name
    if not local_path.exists():
        raise HTTPException(404, f"File not found in B-roll library: {filename}")

    slot = await asyncio.to_thread(get_slot, slot_id)
    if not slot:
        raise HTTPException(404, "Slot not found")

    file_size_mb = round(local_path.stat().st_size / 1_048_576, 1)

    # Create a local-source candidate already marked as ready
    cand = await asyncio.to_thread(
        create_candidate, slot_id, source="local", title=local_path.name,
    )
    await asyncio.to_thread(
        update_candidate, cand["id"],
        download_status="ready", local_path=str(local_path), file_size_mb=file_size_mb,
    )

    # Approve the slot with this candidate
    await asyncio.to_thread(update_slot, slot_id, status="approved", approved_candidate_id=cand["id"])

    await ws_manager.broadcast("broll_slot_approved", {
        "slot_id": slot_id,
        "candidate_id": cand["id"],
    })
    await ws_manager.broadcast("broll_candidate_ready", {
        "candidate_id": cand["id"],
        "slot_id": slot_id,
        "local_path": str(local_path),
    })

    await _check_session_complete(slot["session_id"])

    return {"approved": True, "slot_id": slot_id, "candidate": cand}


@app.get("/api/broll-wingman/preview/{candidate_id}")
async def api_broll_preview(candidate_id: str, request: Request):
    cand = await asyncio.to_thread(get_candidate, candidate_id)
    if not cand or not cand.get("local_path"):
        raise HTTPException(404, "No downloaded file for this candidate")
    local_path = Path(cand["local_path"])
    if not local_path.exists():
        raise HTTPException(404, "File not found on disk")
    # Resolve relative to broll dir (files live in ~/output/broll/)
    rel_name = f"broll/{local_path.name}"
    return await serve_video(rel_name, request)


async def _download_and_broadcast(slot_id: str, candidate_id: str, session_id: str) -> None:
    """Download clip, then check if session is complete."""
    try:
        local_path = await download_clip(candidate_id, ws_manager)
        if not local_path:
            # Revert slot to candidates_ready on failure
            await asyncio.to_thread(update_slot, slot_id, status="candidates_ready", approved_candidate_id=None)
            await ws_manager.broadcast("broll_download_failed", {
                "slot_id": slot_id,
                "candidate_id": candidate_id,
            })
    except Exception as e:
        print(f"[broll-wingman] Download task error: {e}")
        await asyncio.to_thread(update_slot, slot_id, status="candidates_ready", approved_candidate_id=None)

    await _check_session_complete(session_id)


async def _check_session_complete(session_id: str) -> None:
    """If all slots are approved or skipped, mark session completed."""
    from broll_db import get_slots_for_session, get_session
    slots = await asyncio.to_thread(get_slots_for_session, session_id)
    if all(s["status"] in ("approved", "skipped") for s in slots):
        session = await asyncio.to_thread(update_session, session_id, status="completed")
        if session:
            await ws_manager.broadcast("broll_session_completed", {
                "session_id": session_id,
                "job_id": session["job_id"],
            })


# ---------------------------------------------------------------------------
# Background task helpers
# ---------------------------------------------------------------------------

async def _enrich_broll_clip(
    filename: str, filepath: str, source: str = "upload", source_url: str | None = None,
) -> None:
    """Register a B-roll clip in the library and run metadata/preview/auto-tag enrichment."""
    try:
        # Extract video metadata
        meta = await extract_metadata(filepath)

        # Register in library
        clip = await asyncio.to_thread(
            register_clip,
            filename=filename,
            filepath=filepath,
            source=source,
            source_url=source_url,
            file_size_mb=meta.get("file_size_mb"),
            duration_sec=meta.get("duration_sec"),
            width=meta.get("width"),
            height=meta.get("height"),
            codec=meta.get("codec"),
        )
        clip_id = clip["id"]

        # Generate thumbnail + preview
        thumb_path, preview_path = await generate_clip_assets(filepath, clip_id)
        update_fields: dict = {}
        if thumb_path:
            update_fields["thumb_path"] = thumb_path
        if preview_path:
            update_fields["preview_path"] = preview_path

        # Auto-tag via Gemini Flash (or regex fallback)
        game, tags = await auto_tag_clip(filename, source_url)
        if game:
            update_fields["game"] = game
        if tags:
            update_fields["tags"] = tags

        if update_fields:
            await asyncio.to_thread(update_clip, clip_id, **update_fields)

    except Exception as e:
        print(f"[broll-library] Enrichment failed for {filename}: {e}")


async def _run_scriptgen(
    job_id: str,
    url: Optional[str],
    text: Optional[str],
    target_length_sec: int,
    dual_anchor: bool = False,
) -> None:
    try:
        if dual_anchor:
            from scriptgen import generate_dual_anchor_script
            script_text = await generate_dual_anchor_script(
                url=url, text=text, target_length_sec=target_length_sec,
            )
        else:
            script_text = await generate_script(
                url=url, text=text, target_length_sec=target_length_sec,
            )
        job = await asyncio.to_thread(
            transition, job_id, "script_ready", script_text=script_text,
        )
        await ws_manager.broadcast("job_updated", job)

        # B-roll Wingman discovery — only for solo format (dual-anchor doesn't use B-roll)
        if not dual_anchor:
            broll_count = int((await asyncio.to_thread(get_job, job_id) or {}).get("broll_count", 4))
            asyncio.create_task(run_discovery(job_id, script_text, broll_count, ws_manager))
    except Exception as exc:
        job = await asyncio.to_thread(
            update_job, job_id, status="error", error_msg=str(exc)[:800],
        )
        await ws_manager.broadcast("job_updated", job)


async def _run_pipeline_task(job_id: str, script_text: str) -> None:
    try:
        job_data = await asyncio.to_thread(get_job, job_id)
        is_dual = bool((job_data or {}).get("dual_anchor", False))

        if is_dual:
            # Dual-anchor pipeline — no B-roll, uses ninja_dual_anchor.py
            from pipeline import run_dual_anchor_pipeline
            output_path, error_msg = await run_dual_anchor_pipeline(script_text, job_id)
        else:
            # Standard solo pipeline
            broll_count = int((job_data or {}).get("broll_count") or 4)
            broll_duration = float((job_data or {}).get("broll_duration") or 10.0)

            # Query Wingman for approved clips — pass as explicit broll_map
            broll_map: list[str] = []
            try:
                session = await asyncio.to_thread(get_full_session, job_id)
                if session and session.get("slots"):
                    for slot in session["slots"]:
                        if slot.get("status") != "approved" or not slot.get("approved_candidate_id"):
                            continue
                        cand = next((c for c in slot.get("candidates", []) if c["id"] == slot["approved_candidate_id"]), None)
                        if cand and cand.get("local_path") and Path(cand["local_path"]).exists():
                            broll_map.append(f"{slot['keyword']}:{cand['local_path']}")
            except Exception:
                pass  # Wingman DB unavailable — fall back to directory scan

            output_path, error_msg = await run_pipeline(script_text, job_id, broll_count, broll_duration, broll_map=broll_map or None)
        if output_path:
            video_path = Path(output_path)
            thumb = get_thumbnail_for_video(video_path)
            thumb_path = str(thumb) if thumb else None
            job = await asyncio.to_thread(
                transition, job_id, "ready_for_review",
                output_path=output_path, thumb_path=thumb_path,
            )
        else:
            job = await asyncio.to_thread(
                transition, job_id, "error", error_msg=(error_msg or "Unknown error")[:800],
            )
        await ws_manager.broadcast("job_updated", job)
        if job and job.get("status") == "ready_for_review":
            asyncio.get_event_loop().run_in_executor(None, _rasengan_emit, "dojo.job_completed", {"job_id": job_id, "title": job.get("title", "")})
        elif job and job.get("status") == "error":
            asyncio.get_event_loop().run_in_executor(None, _rasengan_emit, "dojo.job_failed", {"job_id": job_id, "error": (job.get("error_msg") or "")[:200]})
    except Exception as exc:
        job = await asyncio.to_thread(
            update_job, job_id, status="error", error_msg=str(exc)[:800],
        )
        await ws_manager.broadcast("job_updated", job)
        asyncio.get_event_loop().run_in_executor(None, _rasengan_emit, "dojo.job_failed", {"job_id": job_id, "error": str(exc)[:200]})


# ---------------------------------------------------------------------------
# YouTube upload
# ---------------------------------------------------------------------------

@app.post("/api/jobs/{job_id}/upload")
async def api_upload_youtube(job_id: str, payload: dict) -> dict:
    job = await asyncio.to_thread(get_job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] not in ("approved", "error"):
        raise HTTPException(400, f"Cannot upload from status '{job['status']}'")
    if not job.get("output_path") or not Path(job["output_path"]).exists():
        raise HTTPException(400, "Video file not found on disk")

    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    tags = payload.get("tags") or []
    privacy = payload.get("privacy") or "private"
    if not title:
        raise HTTPException(400, "Title is required")

    job = await asyncio.to_thread(
        transition, job_id, "uploading",
        youtube_title=title, youtube_privacy=privacy,
    )
    await ws_manager.broadcast("job_updated", job)

    asyncio.create_task(_run_youtube_upload(
        job_id, job["output_path"], title, description, tags,
        job.get("thumb_path"), privacy,
    ))
    return job


async def _run_youtube_upload(
    job_id: str, video_path: str, title: str, description: str,
    tags: list[str], thumb_path: str | None, privacy: str,
) -> None:
    try:
        import sys as _sys

        # Scripts mounted at /data/scripts in Docker, fallback to ~/scripts locally
        scripts_dir = Path("/data/scripts") if Path("/data/scripts").exists() else Path.home() / "scripts"
        cmd = [
            _sys.executable, str(scripts_dir / "youtube/youtube_upload.py"),
            "--video", video_path,
            "--title", title,
            "--description", description,
            "--privacy", privacy,
        ]
        if tags:
            cmd += ["--tags", ",".join(tags)]
        if thumb_path and Path(thumb_path).exists():
            cmd += ["--thumbnail", thumb_path]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode()

        # Parse video_id from youtube_upload.py stdout
        video_id = None
        for line in output.splitlines():
            if "youtube.com/watch?v=" in line:
                video_id = line.split("watch?v=")[-1].strip()
                break

        if proc.returncode == 0 and video_id:
            job = await asyncio.to_thread(
                transition, job_id, "uploaded",
                youtube_video_id=video_id,
            )
            await ws_manager.broadcast("job_updated", job)
            asyncio.get_event_loop().run_in_executor(
                None, _rasengan_emit, "dojo.video_uploaded",
                {"job_id": job_id, "video_id": video_id, "title": title},
            )
        else:
            error = output[-500:] if output else "Upload returned no video ID"
            job = await asyncio.to_thread(
                transition, job_id, "error",
                error_msg=f"YouTube upload failed: {error}"[:800],
            )
            await ws_manager.broadcast("job_updated", job)
            asyncio.get_event_loop().run_in_executor(
                None, _rasengan_emit, "dojo.upload_failed",
                {"job_id": job_id, "error": error[:200]},
            )
    except Exception as exc:
        job = await asyncio.to_thread(
            update_job, job_id, status="error",
            error_msg=f"Upload exception: {str(exc)}"[:800],
        )
        await ws_manager.broadcast("job_updated", job)


# ---------------------------------------------------------------------------
# Preflight health check
# ---------------------------------------------------------------------------

def _get_celery():
    """Lazy Celery app import to avoid hard dependency when broker is down."""
    from celery import Celery
    broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    return Celery(broker=broker)


@app.get("/api/preflight")
async def api_preflight() -> dict:
    checks = {}

    # Content script exists
    from pipeline import CONTENT_SCRIPT
    checks["content_script"] = CONTENT_SCRIPT.exists()

    # Output dir writable
    try:
        test_file = OUTPUT_DIR / ".preflight_test"
        test_file.write_text("ok")
        test_file.unlink()
        checks["output_writable"] = True
    except Exception:
        checks["output_writable"] = False

    # Celery worker alive
    try:
        cel = _get_celery()
        result = cel.control.inspect(timeout=3.0).active_queues()
        checks["celery_worker"] = bool(result)
    except Exception:
        checks["celery_worker"] = False

    # B-roll clips count
    try:
        broll_clips = list(BROLL_DIR.glob("*.mp4"))
        checks["broll_clips"] = len(broll_clips)
    except Exception:
        checks["broll_clips"] = 0

    # Avatar check (soft — Dojo may not mount assets)
    avatar = Path("/app/assets/reference/ninja_helmet_v4_hires.jpg")
    checks["avatar"] = avatar.exists()

    # all_ok excludes avatar (soft check)
    all_ok = all([
        checks["content_script"],
        checks["output_writable"],
        checks["celery_worker"],
    ])

    return {"ok": all_ok, "checks": checks}


# ---------------------------------------------------------------------------
# Serve React SPA in production (must be last — catch-all)
# ---------------------------------------------------------------------------

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
