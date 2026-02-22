"""Context engine — aggregates state for the /resume endpoint."""

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.config import GIT_DIR, SHARINGAN_INDEX
from app.database import query_events, recent_events

logger = logging.getLogger("rasengan.context")


def _git_context() -> dict:
    """Current git state: branch, last commit, dirty files."""
    try:
        git_dir = str(Path(GIT_DIR) / ".git")
        git_base = ["git", "--git-dir", git_dir, "--work-tree", GIT_DIR]
        branch = subprocess.run(
            git_base + ["rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        last_commit = subprocess.run(
            git_base + ["log", "-1", "--format=%h %s (%ar)"],
            capture_output=True, text=True, timeout=5,
        )
        dirty = subprocess.run(
            git_base + ["status", "--porcelain", "-u"],
            capture_output=True, text=True, timeout=5,
        )
        dirty_lines = [l for l in dirty.stdout.strip().split("\n") if l][:20]
        return {
            "branch": branch.stdout.strip(),
            "last_commit": last_commit.stdout.strip(),
            "dirty_files": len(dirty_lines),
            "dirty_sample": dirty_lines[:5],
        }
    except Exception as e:
        return {"error": str(e)}


def _sharingan_context() -> dict:
    """Recently updated scrolls from Sharingan index."""
    try:
        idx_path = Path(SHARINGAN_INDEX)
        if not idx_path.exists():
            return {"scrolls": [], "note": "index not found"}
        data = json.loads(idx_path.read_text())
        scrolls = data if isinstance(data, list) else data.get("scrolls", [])
        # Sort by last_updated descending, take top 5
        scrolls_sorted = sorted(
            scrolls,
            key=lambda s: s.get("last_updated", ""),
            reverse=True,
        )[:5]
        return {
            "total_scrolls": len(scrolls),
            "recent": [
                {
                    "name": s.get("name", "unknown"),
                    "level": s.get("level", "unknown"),
                    "domain": s.get("domain", ""),
                    "updated": s.get("last_updated", "unknown"),
                }
                for s in scrolls_sorted
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def _deploy_context() -> dict:
    """Recent deploy status per service."""
    try:
        events = query_events(event_type_prefix="deploy.", limit=50)
        services: dict[str, dict] = {}
        for ev in events:
            payload = ev.get("payload", {})
            service = payload.get("service", "unknown")
            if service not in services:
                ts = ev.get("created_at")
                if isinstance(ts, datetime):
                    ts = ts.isoformat()
                services[service] = {
                    "last_event": ev.get("event_type", "?"),
                    "last_at": ts or "?",
                    "exit_code": payload.get("exit_code"),
                    "duration_seconds": payload.get("duration_seconds"),
                }
        return {"services": services, "total_recent": len(events)}
    except Exception as e:
        return {"error": str(e)}


def build_resume() -> dict:
    """Build a context resume brief."""
    events = recent_events(10)
    # Serialize datetimes for JSON
    for e in events:
        if isinstance(e.get("created_at"), datetime):
            e["created_at"] = e["created_at"].isoformat()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git": _git_context(),
        "sharingan": _sharingan_context(),
        "deploys": _deploy_context(),
        "recent_events": events,
    }
