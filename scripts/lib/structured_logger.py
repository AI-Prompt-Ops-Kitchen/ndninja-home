"""
Structured JSON logging module with correlation IDs.

Usage:
    from lib.structured_logger import get_logger

    logger = get_logger("daily-review")
    logger.info("Starting review", extra={"conversations": 5})
    logger.error("DB connection failed", extra={"host": "100.77.248.9"})

Output (one JSON object per line):
    {"timestamp": "2026-02-08T23:00:00.000Z", "level": "INFO", "service": "daily-review",
     "correlation_id": "a1b2c3d4-...", "message": "Starting review", "conversations": 5}

Log files go to ~/.logs/<service>.log (logrotate-friendly, one file per service).
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path.home() / ".logs"

# Module-level correlation ID: set once per process invocation
_correlation_id = str(uuid.uuid4())


def get_correlation_id() -> str:
    """Return the current process correlation ID."""
    return _correlation_id


def set_correlation_id(cid: str) -> None:
    """Override the correlation ID (e.g., from an upstream caller)."""
    global _correlation_id
    _correlation_id = cid


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "service": self.service,
            "correlation_id": _correlation_id,
            "message": record.getMessage(),
        }

        # Merge any extra fields passed via logger.info("msg", extra={...})
        # Standard LogRecord attrs we don't want to duplicate
        _skip = {
            "name", "msg", "args", "created", "relativeCreated",
            "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "pathname", "filename", "module", "levelno", "levelname",
            "msecs", "thread", "threadName", "process", "processName",
            "taskName", "message",
        }
        for key, val in record.__dict__.items():
            if key not in _skip and not key.startswith("_"):
                entry[key] = val

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable format for stdout that includes correlation ID."""

    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        short_cid = _correlation_id[:8]
        return f"[{ts}] {record.levelname:7s} [{short_cid}] {record.getMessage()}"


def get_logger(
    service: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_stdout: bool = True,
) -> logging.Logger:
    """Create a structured logger for the given service.

    Args:
        service: Service name (used in log entries and filename).
        level: Logging level (default INFO).
        log_to_file: Write JSON logs to ~/.logs/<service>.log.
        log_to_stdout: Write human-readable logs to stdout.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(f"structured.{service}")

    # Avoid adding handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    if log_to_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / f"{service}.log"
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setFormatter(JSONFormatter(service))
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    if log_to_stdout:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(HumanFormatter(service))
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    return logger
