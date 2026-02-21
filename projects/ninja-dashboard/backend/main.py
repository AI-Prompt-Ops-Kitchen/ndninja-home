"""The Dojo — Content Pipeline Dashboard backend.
FastAPI app: all routes + WebSocket manager.
Run with: uvicorn main:app --host 0.0.0.0 --port 8090 --workers 1
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from jobs import create_job, delete_job, get_job, init_db, list_jobs, transition, update_job
from media import OUTPUT_DIR, get_thumbnail_for_video, safe_resolve, serve_thumb, serve_video
from pipeline import BROLL_DIR, run_pipeline
from scriptgen import generate_script

from broll_db import (
    get_candidate,
    get_full_session,
    get_slot,
    init_broll_db,
    update_candidate,
    update_session,
    update_slot,
)
from broll_discovery import clip_youtube, download_clip, run_discovery

UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", Path.home() / "uploads"))
UPLOADS_DIR.mkdir(exist_ok=True)
BROLL_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="The Dojo — Ninja Content Pipeline")

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
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup() -> None:
    init_db()
    try:
        init_broll_db()
    except Exception as e:
        print(f"⚠️ B-roll Wingman DB init failed (feature degraded): {e}")
    # Recover any jobs that were stuck in 'generating' when the server last died.
    # The subprocess keeps running but the asyncio listener is gone — find their output.
    stuck = [j for j in list_jobs() if j["status"] == "generating"]
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
        # Send full job list immediately on connect
        jobs = await asyncio.to_thread(list_jobs)
        await ws.send_text(json.dumps({"type": "job_list", "data": jobs}))

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

@app.get("/api/jobs")
async def api_list_jobs() -> list[dict]:
    return await asyncio.to_thread(list_jobs)


@app.post("/api/jobs/article")
async def api_submit_article(payload: dict) -> dict:
    url: Optional[str] = payload.get("url") or None
    text: Optional[str] = payload.get("text") or None
    target_length_sec: int = int(payload.get("target_length_sec", 60))
    broll_count: int = int(payload.get("broll_count", 3))
    broll_duration: float = float(payload.get("broll_duration", 10.0))

    if not url and not text:
        raise HTTPException(400, "Provide url or text")

    job = await asyncio.to_thread(create_job, url, text, target_length_sec, broll_count, broll_duration)
    await ws_manager.broadcast("job_created", job)

    # Scriptgen runs in the background — UI will receive WS update when done
    asyncio.create_task(_run_scriptgen(job["id"], url, text, target_length_sec))

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
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(64 * 1024):
            await f.write(chunk)
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


@app.post("/api/upload")
async def api_upload_file(file: UploadFile = File(...)) -> dict:
    safe_name = Path(file.filename or "upload").name
    dest = UPLOADS_DIR / safe_name
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
    broll_count = int(job.get("broll_count", 3))
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

async def _run_scriptgen(
    job_id: str,
    url: Optional[str],
    text: Optional[str],
    target_length_sec: int,
) -> None:
    try:
        script_text = await generate_script(
            url=url,
            text=text,
            target_length_sec=target_length_sec,
        )
        job = await asyncio.to_thread(
            transition, job_id, "script_ready", script_text=script_text,
        )
        await ws_manager.broadcast("job_updated", job)

        # Auto-trigger B-roll Wingman discovery
        broll_count = int((await asyncio.to_thread(get_job, job_id) or {}).get("broll_count", 3))
        asyncio.create_task(run_discovery(job_id, script_text, broll_count, ws_manager))
    except Exception as exc:
        job = await asyncio.to_thread(
            update_job, job_id, status="error", error_msg=str(exc)[:800],
        )
        await ws_manager.broadcast("job_updated", job)


async def _run_pipeline_task(job_id: str, script_text: str) -> None:
    try:
        job_data = await asyncio.to_thread(get_job, job_id)
        broll_count = int((job_data or {}).get("broll_count") or 3)
        broll_duration = float((job_data or {}).get("broll_duration") or 10.0)
        output_path, error_msg = await run_pipeline(script_text, job_id, broll_count, broll_duration)
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
    except Exception as exc:
        job = await asyncio.to_thread(
            update_job, job_id, status="error", error_msg=str(exc)[:800],
        )
        await ws_manager.broadcast("job_updated", job)


# ---------------------------------------------------------------------------
# Serve React SPA in production (must be last — catch-all)
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
