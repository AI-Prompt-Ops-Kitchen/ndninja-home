"""Pipeline runner for ninja_content.py — Celery dispatch or local subprocess."""
import asyncio
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

LOG_DIR = Path("/tmp")

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", Path.home() / "output"))
BROLL_DIR = Path(os.environ.get("BROLL_DIR", Path.home() / "output" / "broll"))
CONTENT_SCRIPT = Path(os.environ.get("CONTENT_SCRIPT", Path.home() / "scripts" / "ninja_content.py"))

# Matches: DONE! Output: /path/to/file.mp4
_DONE_RE = re.compile(r"DONE!\s+Output:\s+(.+\.mp4)", re.IGNORECASE)

# Celery client — initialized lazily when CELERY_BROKER_URL is set
_celery_app = None
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")


def _get_celery():
    """Lazy-init Celery client for dispatching content tasks."""
    global _celery_app
    if _celery_app is None and CELERY_BROKER_URL:
        from celery import Celery
        _celery_app = Celery("content_dispatch", broker=CELERY_BROKER_URL)
        _celery_app.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
    return _celery_app


async def run_pipeline(
    script_text: str,
    job_id: str,
    broll_count: int = 3,
    broll_duration: float = 4.0,
    broll_map: Optional[list[str]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Run ninja_content.py via Celery worker (if configured) or local subprocess.
    Returns (output_path, error_msg). One will be None.
    """
    celery = _get_celery()
    if celery:
        return await _run_via_celery(celery, script_text, job_id, broll_count, broll_duration)
    return await _run_local(script_text, job_id, broll_count, broll_duration, broll_map=broll_map)


async def _run_via_celery(
    celery,
    script_text: str,
    job_id: str,
    broll_count: int,
    broll_duration: float,
) -> Tuple[Optional[str], Optional[str]]:
    """Dispatch to content worker via Celery and poll for result."""
    try:
        task = celery.send_task(
            "content.generate_video",
            args=[script_text, job_id, broll_count, broll_duration],
            queue="content",
        )
        result = await asyncio.to_thread(task.get, timeout=1800)
        if isinstance(result, dict):
            if "error" in result:
                return None, result["error"]
            return result.get("output_path"), None
        return None, f"Unexpected result type: {type(result)}"
    except Exception as exc:
        return None, f"Celery task failed: {exc}"


async def _run_local(
    script_text: str,
    job_id: str,
    broll_count: int,
    broll_duration: float,
    broll_map: Optional[list[str]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Fallback: run ninja_content.py as local async subprocess."""
    if not CONTENT_SCRIPT.exists():
        return None, f"Pipeline script not found: {CONTENT_SCRIPT}"

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        prefix=f"ninja_job_{job_id[:8]}_",
        delete=False,
    )
    tmp.write(script_text)
    tmp.close()
    script_file = tmp.name

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_prefix = f"ninja_dash_{job_id[:8]}_{timestamp}"

    cmd = [
        "python3", "-u",
        str(CONTENT_SCRIPT),
        "--script-file", script_file,
        "--output", output_prefix,
        "--broll-count", str(broll_count),
        "--broll-duration", str(broll_duration),
    ]

    if broll_map:
        # Use Wingman-approved clips — pass explicit keyword:path mappings
        cmd += ["--broll", "--broll-map"] + broll_map
        # Also pass broll-dir as fallback for any remaining moments
        if BROLL_DIR.exists() and any(BROLL_DIR.glob("*.mp4")):
            cmd += ["--broll-dir", str(BROLL_DIR)]
    elif BROLL_DIR.exists() and any(BROLL_DIR.glob("*.mp4")):
        cmd += ["--broll", "--broll-dir", str(BROLL_DIR)]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        output_path: Optional[str] = None
        stdout_lines: list[str] = []

        log_path = LOG_DIR / f"ninja_job_{job_id[:8]}.log"
        log_fh = open(log_path, "w", buffering=1)
        log_fh.write(f"=== Dojo Pipeline Log — job {job_id} ===\n")
        log_fh.write(f"=== CMD: {' '.join(cmd)} ===\n\n")

        assert proc.stdout is not None
        async for line_bytes in proc.stdout:
            line = line_bytes.decode("utf-8", errors="replace").rstrip()
            stdout_lines.append(line)
            log_fh.write(line + "\n")
            match = _DONE_RE.search(line)
            if match:
                output_path = match.group(1).strip()

        log_fh.write(f"\n=== Process exited with code {proc.returncode} ===\n")
        log_fh.close()

        await proc.wait()

        if proc.returncode != 0:
            snippet = "\n".join(stdout_lines[-15:])
            return None, f"Pipeline exited {proc.returncode}:\n{snippet[-800:]}"

        if not output_path:
            output_path = _find_newest_mp4(output_prefix)

        if output_path and Path(output_path).exists():
            return output_path, None

        return None, "Pipeline completed but output file not found"

    finally:
        try:
            os.unlink(script_file)
        except OSError:
            pass


def _find_newest_mp4(hint_prefix: str) -> Optional[str]:
    """Fallback: scan output dir for newest .mp4 matching the job prefix."""
    mp4s = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not mp4s:
        return None
    # Only consider files created in the last 30 minutes (prevent stale fallback)
    import time
    cutoff = time.time() - 1800
    for mp4 in mp4s[:5]:
        if mp4.stat().st_mtime < cutoff:
            continue
        if mp4.stem.startswith(hint_prefix.replace(".mp4", "")):
            return str(mp4)
    return None
