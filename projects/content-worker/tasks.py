"""Content pipeline tasks — wraps ninja_content.py as subprocess."""
import os
import re
import subprocess
import tempfile
from pathlib import Path

from celery_app import app

CONTENT_SCRIPT = Path(os.environ.get("CONTENT_SCRIPT", "/app/scripts/ninja_content.py"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/data/output"))
BROLL_DIR = Path(os.environ.get("BROLL_DIR", "/data/output/broll"))

# Matches: DONE! Output: /path/to/file.mp4
_DONE_RE = re.compile(r"DONE!\s+Output:\s+(.+\.mp4)", re.IGNORECASE)


@app.task(name="content.generate_video", bind=True, queue="content")
def generate_video(self, script_text: str, job_id: str, broll_count: int = 3, broll_duration: float = 10.0) -> dict:
    """Run ninja_content.py and return the output path or error."""
    if not CONTENT_SCRIPT.exists():
        return {"error": f"Pipeline script not found: {CONTENT_SCRIPT}"}

    # Write script to temp file
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", prefix=f"ninja_job_{job_id[:8]}_", delete=False
    )
    tmp.write(script_text)
    tmp.close()
    script_file = tmp.name

    from datetime import datetime
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

    if BROLL_DIR.exists() and any(BROLL_DIR.glob("*.mp4")):
        cmd += ["--broll", "--broll-dir", str(BROLL_DIR)]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,
        )

        stdout = proc.stdout or ""
        output_path = None

        for line in stdout.splitlines():
            match = _DONE_RE.search(line)
            if match:
                output_path = match.group(1).strip()

        if proc.returncode != 0:
            snippet = "\n".join(stdout.splitlines()[-15:])
            return {"error": f"Pipeline exited {proc.returncode}:\n{snippet[-800:]}"}

        # Fallback: find newest matching mp4
        if not output_path:
            output_path = _find_newest_mp4(output_prefix)

        if output_path and Path(output_path).exists():
            return {"output_path": output_path}

        return {"error": "Pipeline completed but output file not found"}

    except subprocess.TimeoutExpired:
        return {"error": "Pipeline timed out after 30 minutes"}
    finally:
        try:
            os.unlink(script_file)
        except OSError:
            pass


def _find_newest_mp4(hint_prefix: str) -> str | None:
    mp4s = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not mp4s:
        return None
    for mp4 in mp4s[:5]:
        if mp4.stem.startswith(hint_prefix.replace(".mp4", "")):
            return str(mp4)
    return None
