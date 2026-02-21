"""B-roll Wingman — Async discovery pipeline.

Extracts keywords from script, searches for candidate clips (Pexels + YouTube),
presents them for triage. Downloads happen lazily on approval.
"""

import asyncio
import json
import os
import re
import subprocess
import traceback
from pathlib import Path
from typing import Optional

from broll_db import (
    create_candidate,
    create_session,
    create_slot,
    get_candidate,
    get_full_session,
    get_slots_for_session,
    update_candidate,
    update_session,
    update_slot,
)

BROLL_DIR = Path(os.environ.get("BROLL_DIR", Path.home() / "output" / "broll"))
BROLL_DIR.mkdir(parents=True, exist_ok=True)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

async def _extract_keywords_gemini(script_text: str, count: int) -> list[dict]:
    """Use Gemini Flash via Vertex AI to extract visual keywords from script."""
    from google import genai
    from google.genai import types

    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0601509945")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    client = genai.Client(vertexai=True, project=project, location=location)

    prompt = f"""Analyze this video script and identify the {count} most visually exciting moments —
the sentences where game footage or action shots would have the most impact.

Script:
{script_text}

For each moment, return a JSON array of objects with:
- "keyword": a search-friendly keyword for finding stock footage or trailers (1-4 words, e.g. "Nioh 3 gameplay", "space combat")
- "sentence": the exact sentence or phrase from the script
- "position": what fraction through the script this sentence appears (0.0 to 1.0)

Rules:
- Pick moments that describe ACTION or VISUALS (trailers, gameplay, reveals)
- Avoid intro/outro lines
- Spread them out across the script
- Keywords should work well as YouTube or stock footage search queries
- Return ONLY valid JSON array, no other text

JSON:"""

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=500,
        ),
    )

    text = response.text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group())[:count]
    raise ValueError("No JSON array in Gemini response")


def _extract_keywords_regex(script_text: str, count: int) -> list[dict]:
    """Fallback: extract keywords using regex patterns from ninja_broll.py logic."""
    # Skip intro/outro
    lines = script_text.split("\n")
    content_lines = []
    for line in lines:
        lower = line.lower().strip()
        if any(p in lower for p in ["what's up", "hey ninja", "welcome back", "fellow ninja"]):
            continue
        if any(p in lower for p in ["thanks for watching", "subscribe", "peace out", "see you"]):
            continue
        if line.strip():
            content_lines.append(line.strip())

    body = " ".join(content_lines)

    # Proper nouns / game titles
    proper_nouns = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", body)
    # Tech terms with numbers
    tech_terms = re.findall(r"\b([A-Z][a-zA-Z]*(?:\s*[0-9]+)?(?:\s*(?:Pro|Max|Ultra|Plus|Air))?)\b", body)
    # Quoted terms
    quoted = re.findall(r'"([^"]+)"', body)

    # Score by specificity
    candidates = {}
    for term in proper_nouns + tech_terms + quoted:
        term = term.strip()
        if len(term) < 3:
            continue
        key = term.lower()
        candidates[key] = candidates.get(key, 0) + 1

    # Sort by frequency, take top N
    sorted_terms = sorted(candidates.items(), key=lambda x: -x[1])
    keywords = []
    total_len = len(body) or 1

    for term, _ in sorted_terms[:count]:
        # Find the sentence containing this keyword
        pos = body.lower().find(term)
        position = pos / total_len if pos >= 0 else 0.5

        # Find surrounding sentence
        sentence = ""
        for line in content_lines:
            if term in line.lower():
                sentence = line
                break

        keywords.append({
            "keyword": term,
            "sentence": sentence,
            "position": round(position, 2),
        })

    # Pad with generic terms if needed
    generics = ["gameplay trailer", "action footage", "game reveal", "combat scene", "cinematic"]
    while len(keywords) < count:
        idx = len(keywords)
        keywords.append({
            "keyword": generics[idx % len(generics)],
            "sentence": "",
            "position": round((idx + 1) / (count + 1), 2),
        })

    return keywords


async def _extract_keywords(script_text: str, count: int) -> list[dict]:
    """Extract keywords — try Gemini Flash, fall back to regex."""
    try:
        return await _extract_keywords_gemini(script_text, count)
    except Exception as e:
        print(f"[broll-wingman] Gemini extraction failed ({e}), using regex fallback")
        return await asyncio.to_thread(_extract_keywords_regex, script_text, count)


# ---------------------------------------------------------------------------
# Source search — Pexels
# ---------------------------------------------------------------------------

async def _search_pexels(keyword: str, slot_id: str) -> list[dict]:
    """Search Pexels for stock video clips. Returns created candidate dicts."""
    if not PEXELS_API_KEY:
        return []

    import urllib.request
    import urllib.parse

    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(keyword)}&per_page=3&size=small"
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY})

    try:
        def _fetch():
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())

        data = await asyncio.to_thread(_fetch)
        candidates = []
        for video in data.get("videos", [])[:3]:
            # Get smallest video file for preview
            files = video.get("video_files", [])
            preview_file = min(files, key=lambda f: f.get("width", 9999)) if files else None
            best_file = max(files, key=lambda f: f.get("width", 0)) if files else None

            cand = await asyncio.to_thread(
                create_candidate,
                slot_id=slot_id,
                source="pexels",
                source_url=best_file["link"] if best_file else None,
                title=video.get("url", "").split("/")[-1].replace("-", " ").title() if video.get("url") else keyword,
                preview_url=video.get("image", preview_file["link"] if preview_file else None),
                duration_sec=video.get("duration"),
            )
            candidates.append(cand)
        return candidates
    except Exception as e:
        print(f"[broll-wingman] Pexels search failed for '{keyword}': {e}")
        return []


# ---------------------------------------------------------------------------
# Source search — YouTube via yt-dlp
# ---------------------------------------------------------------------------

async def _search_youtube(keyword: str, slot_id: str) -> list[dict]:
    """Search YouTube for gameplay/trailer clips via yt-dlp flat playlist."""
    search_query = f"{keyword} gameplay trailer"
    cmd = [
        "yt-dlp",
        f"ytsearch5:{search_query}",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        "--quiet",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)

        candidates = []
        for line in stdout.decode().strip().split("\n"):
            if not line.strip():
                continue
            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                continue

            duration = info.get("duration")
            # Filter: 10-120 seconds
            if duration and (duration < 10 or duration > 120):
                continue

            video_id = info.get("id", "")
            title = info.get("title", keyword)
            thumbnail = info.get("thumbnail") or info.get("thumbnails", [{}])[0].get("url") if info.get("thumbnails") else None
            # Fallback thumbnail
            if not thumbnail and video_id:
                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            cand = await asyncio.to_thread(
                create_candidate,
                slot_id=slot_id,
                source="youtube",
                source_url=f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                title=title[:100],
                preview_url=thumbnail,
                duration_sec=duration,
            )
            candidates.append(cand)

            if len(candidates) >= 3:
                break

        return candidates
    except asyncio.TimeoutError:
        print(f"[broll-wingman] yt-dlp search timed out for '{keyword}'")
        return []
    except Exception as e:
        print(f"[broll-wingman] YouTube search failed for '{keyword}': {e}")
        return []


# ---------------------------------------------------------------------------
# Download — lazy, triggered on approval
# ---------------------------------------------------------------------------

async def download_clip(candidate_id: str, ws_manager=None) -> Optional[str]:
    """Download a candidate clip to ~/output/broll/. Returns local_path or None."""
    cand = await asyncio.to_thread(get_candidate, candidate_id)
    if not cand:
        return None

    source = cand["source"]
    source_url = cand["source_url"]
    slot_id = cand["slot_id"]

    if not source_url:
        await asyncio.to_thread(update_candidate, candidate_id, download_status="failed")
        return None

    # Build output filename from slot keyword
    from broll_db import get_slot
    slot = await asyncio.to_thread(get_slot, slot_id)
    keyword = slot["keyword"] if slot else "clip"
    slug = re.sub(r"[^a-z0-9]+", "_", keyword.lower()).strip("_")
    output_path = BROLL_DIR / f"{slug}.mp4"

    # Don't re-download if we already have it
    if output_path.exists() and output_path.stat().st_size > 10000:
        await asyncio.to_thread(
            update_candidate, candidate_id,
            download_status="ready",
            local_path=str(output_path),
            file_size_mb=round(output_path.stat().st_size / 1_048_576, 2),
        )
        return str(output_path)

    await asyncio.to_thread(update_candidate, candidate_id, download_status="downloading")

    try:
        if source == "pexels":
            local = await _download_pexels(source_url, output_path)
        elif source == "youtube":
            local = await _download_youtube(source_url, output_path)
        else:
            local = None

        if local and Path(local).exists():
            size_mb = round(Path(local).stat().st_size / 1_048_576, 2)
            await asyncio.to_thread(
                update_candidate, candidate_id,
                download_status="ready",
                local_path=str(local),
                file_size_mb=size_mb,
            )
            if ws_manager:
                await ws_manager.broadcast("broll_candidate_ready", {
                    "candidate_id": candidate_id,
                    "slot_id": slot_id,
                    "local_path": str(local),
                })
            return str(local)
        else:
            await asyncio.to_thread(update_candidate, candidate_id, download_status="failed")
            return None

    except Exception as e:
        print(f"[broll-wingman] Download failed for {candidate_id}: {e}")
        await asyncio.to_thread(update_candidate, candidate_id, download_status="failed")
        return None


async def _download_pexels(url: str, output_path: Path) -> Optional[str]:
    """Download a Pexels video file."""
    import urllib.request

    def _dl():
        urllib.request.urlretrieve(url, str(output_path))
        return str(output_path)

    return await asyncio.to_thread(_dl)


async def _download_youtube(url: str, output_path: Path) -> Optional[str]:
    """Download YouTube video via yt-dlp, trim to 15s max."""
    tmp_path = output_path.with_suffix(".tmp.mp4")
    cmd = [
        "yt-dlp",
        url,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--max-filesize", "50M",
        "--no-playlist",
        "--no-warnings",
        "--quiet",
        "-o", str(tmp_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

    if not tmp_path.exists():
        print(f"[broll-wingman] yt-dlp failed: {stderr.decode()[:200]}")
        return None

    # Trim to 15s max with ffmpeg
    trim_cmd = [
        "ffmpeg", "-y",
        "-i", str(tmp_path),
        "-t", "15",
        "-c", "copy",
        str(output_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *trim_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=30)

    # Clean up temp
    if tmp_path.exists():
        tmp_path.unlink()

    return str(output_path) if output_path.exists() else None


# ---------------------------------------------------------------------------
# Manual YouTube clip — paste URL + time range
# ---------------------------------------------------------------------------

async def clip_youtube(url: str, start: str, end: str, filename: Optional[str] = None) -> dict:
    """Download a YouTube video and trim to a specific time range.

    Args:
        url: YouTube video URL
        start: Start time (e.g. "0:11", "1:30")
        end: End time (e.g. "0:23", "2:00")
        filename: Optional output filename (without extension). Auto-generated from title if omitted.

    Returns:
        dict with filename, path, size_mb
    """
    # Get video info for auto-naming
    if not filename:
        info_cmd = [
            "yt-dlp", "--print", "%(title)s", "--no-warnings", "--quiet", url,
        ]
        proc = await asyncio.create_subprocess_exec(
            *info_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        title = stdout.decode().strip() or "clip"
        slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:60]
        # Include time range in filename
        t_start = start.replace(":", "m") + "s"
        t_end = end.replace(":", "m") + "s"
        filename = f"{slug}_{t_start}_{t_end}"

    output_path = BROLL_DIR / f"{filename}.mp4"
    tmp_path = BROLL_DIR / f"{filename}.tmp.mp4"

    # Download full video
    dl_cmd = [
        "yt-dlp", url,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--no-playlist",
        "--no-warnings",
        "--quiet",
        "-o", str(tmp_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *dl_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

    if not tmp_path.exists():
        raise RuntimeError(f"yt-dlp download failed: {stderr.decode()[:300]}")

    # Trim with ffmpeg
    trim_cmd = [
        "ffmpeg", "-y",
        "-ss", start,
        "-to", end,
        "-i", str(tmp_path),
        "-c", "copy",
        str(output_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *trim_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

    # Clean up temp
    if tmp_path.exists():
        tmp_path.unlink()

    if not output_path.exists():
        raise RuntimeError(f"ffmpeg trim failed: {stderr.decode()[:300]}")

    size_mb = round(output_path.stat().st_size / 1_048_576, 2)
    return {
        "filename": output_path.name,
        "path": str(output_path),
        "size_mb": size_mb,
    }


# ---------------------------------------------------------------------------
# Main discovery pipeline — runs as asyncio.create_task()
# ---------------------------------------------------------------------------

async def run_discovery(job_id: str, script_text: str, slot_count: int, ws_manager) -> None:
    """Full pipeline: extract keywords → search sources → present for triage."""
    print(f"[broll-wingman] Starting discovery for job {job_id[:8]} ({slot_count} slots)")

    try:
        # 1. Create session
        session = await asyncio.to_thread(create_session, job_id, script_text, slot_count)
        session_id = session["id"]
        await ws_manager.broadcast("broll_session_started", {
            "job_id": job_id,
            "session_id": session_id,
            "status": "extracting",
        })

        # 2. Extract keywords
        keywords = await _extract_keywords(script_text, slot_count)
        print(f"[broll-wingman] Extracted keywords: {[k.get('keyword') for k in keywords]}")

        # 3. Create slots
        slots = []
        for i, kw in enumerate(keywords):
            slot = await asyncio.to_thread(
                create_slot,
                session_id=session_id,
                slot_index=i,
                keyword=kw.get("keyword", f"clip_{i}"),
                sentence=kw.get("sentence"),
                position=float(kw.get("position", (i + 1) / (slot_count + 1))),
            )
            slots.append(slot)

        await asyncio.to_thread(update_session, session_id, status="searching")
        await ws_manager.broadcast("broll_slots_ready", {
            "job_id": job_id,
            "session_id": session_id,
            "slots": slots,
        })

        # 4. Search for candidates (parallel per slot)
        async def search_slot(slot: dict):
            slot_id = slot["id"]
            keyword = slot["keyword"]

            # Search both sources in parallel
            pexels_task = asyncio.create_task(_search_pexels(keyword, slot_id))
            youtube_task = asyncio.create_task(_search_youtube(keyword, slot_id))
            pexels_results, youtube_results = await asyncio.gather(pexels_task, youtube_task)

            all_candidates = pexels_results + youtube_results

            if all_candidates:
                await asyncio.to_thread(update_slot, slot_id, status="candidates_ready")
                await ws_manager.broadcast("broll_candidate_found", {
                    "job_id": job_id,
                    "slot_id": slot_id,
                    "candidates": all_candidates,
                })
            else:
                await asyncio.to_thread(update_slot, slot_id, status="candidates_ready")
                await ws_manager.broadcast("broll_candidate_found", {
                    "job_id": job_id,
                    "slot_id": slot_id,
                    "candidates": [],
                })

        await asyncio.gather(*(search_slot(s) for s in slots))

        # 5. All searches done — present for triage
        await asyncio.to_thread(update_session, session_id, status="presenting")
        full_session = await asyncio.to_thread(get_full_session, job_id)
        await ws_manager.broadcast("broll_session_updated", {
            "job_id": job_id,
            "session": full_session,
        })

        print(f"[broll-wingman] Discovery complete for job {job_id[:8]} — awaiting triage")

    except Exception as e:
        print(f"[broll-wingman] Discovery failed for job {job_id[:8]}: {e}")
        traceback.print_exc()
        try:
            session = await asyncio.to_thread(
                lambda: __import__("broll_db").get_session_by_job(job_id)
            )
            if session:
                await asyncio.to_thread(update_session, session["id"], status="failed")
            await ws_manager.broadcast("broll_session_updated", {
                "job_id": job_id,
                "error": str(e)[:200],
            })
        except Exception:
            pass
