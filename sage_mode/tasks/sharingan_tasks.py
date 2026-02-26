"""Sharingan — Celery tasks for autonomous learning pipeline.

Replaces cron jobs with Beat-scheduled Celery tasks:
- daily_review: Daily 3AM observation log (no API cost)
- weekly_synthesis: Sunday 3AM chat history digest (Claude haiku)
- autolearn: Sunday 4AM autonomous scroll deepening
"""
import os
import subprocess
import logging

from sage_mode.celery_app import celery_app

logger = logging.getLogger(__name__)


def _rasengan_emit(event_type: str, payload: dict | None = None) -> None:
    try:
        import httpx
        url = os.environ.get("RASENGAN_URL", "http://rasengan:8050")
        httpx.post(f"{url}/events", json={"event_type": event_type, "source": "sharingan", "payload": payload or {}}, timeout=2.0)
    except Exception:
        pass

SHARINGAN_DIR = os.environ.get("SHARINGAN_SCRIPT_DIR", "/app/sharingan")
LOG_DIR = os.environ.get("SHARINGAN_LOG_DIR", "/data/logs")


def _run_script(script_name: str, args: list[str] | None = None) -> dict:
    """Run a Sharingan script as subprocess and capture output."""
    script_path = os.path.join(SHARINGAN_DIR, script_name)
    if not os.path.exists(script_path):
        return {"status": "error", "message": f"Script not found: {script_path}"}

    cmd = ["python3", script_path] + (args or [])
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max
        )
        log_file = os.path.join(LOG_DIR, f"sharingan-{script_name.replace('.py', '')}.log")
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(f"\n=== {script_name} run ===\n")
            f.write(result.stdout or "")
            if result.stderr:
                f.write(f"\nSTDERR:\n{result.stderr}")

        if result.returncode == 0:
            return {"status": "ok", "output": result.stdout[-500:] if result.stdout else ""}
        return {
            "status": "error",
            "returncode": result.returncode,
            "output": (result.stdout or "")[-500:],
            "stderr": (result.stderr or "")[-500:],
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": f"{script_name} timed out after 10 minutes"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@celery_app.task(name="sharingan.daily_review", queue="sharingan")
def daily_review() -> dict:
    """Daily 3AM — extract observations from chat history (no API cost)."""
    logger.info("Running Sharingan daily review")
    result = _run_script("extract_daily_review.py")
    if result.get("status") == "ok":
        _rasengan_emit("sharingan.daily_review", {"result": "ok"})
    return result


@celery_app.task(name="sharingan.weekly_synthesis", queue="sharingan")
def weekly_synthesis() -> dict:
    """Sunday 3AM — synthesize weekly chat history into workflow-insights scroll."""
    logger.info("Running Sharingan weekly synthesis")
    result = _run_script("extract_chat_history.py")
    if result.get("status") == "ok":
        _rasengan_emit("sharingan.weekly_synthesis", {"result": "ok"})
    return result


@celery_app.task(name="sharingan.autolearn", queue="sharingan")
def autolearn() -> dict:
    """Sunday 4AM — autonomous scroll deepening."""
    logger.info("Running Sharingan autolearn")
    result = _run_script("autolearn.py")
    if result.get("status") == "ok":
        _rasengan_emit("sharingan.autolearn", {"result": "ok"})
    return result
