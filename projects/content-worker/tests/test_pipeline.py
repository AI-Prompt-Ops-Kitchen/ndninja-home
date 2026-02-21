"""Pipeline test harness — dry-run checks ($0, <10s) + optional integration test.

Dry-run tests validate that the container environment is correctly configured
before accepting any work. Integration test runs a real (short) pipeline.

Usage:
    pytest tests/ -v --tb=short          # dry-run only
    pytest tests/ -v --integration       # dry-run + real pipeline run
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import requests


# ---------------------------------------------------------------------------
# Dry-run tests — $0, <10 seconds
# ---------------------------------------------------------------------------


class TestPythonEnvironment:
    """Validate Python version and critical imports."""

    def test_python_version(self):
        assert sys.version_info >= (3, 13), (
            f"Python >= 3.13 required, got {sys.version}"
        )

    @pytest.mark.parametrize("module", [
        "celery",
        "requests",
        "fal_client",
        "keyring",
        "google.genai",
    ])
    def test_critical_import(self, module):
        __import__(module)


class TestSystemDependencies:
    """Validate system binaries are available."""

    def test_ffmpeg_in_path(self):
        assert shutil.which("ffmpeg"), "ffmpeg not found in PATH"

    def test_ffprobe_in_path(self):
        assert shutil.which("ffprobe"), "ffprobe not found in PATH"


class TestEnvVars:
    """Validate required environment variables are set and non-empty."""

    @pytest.mark.parametrize("var", [
        "ELEVENLABS_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
    ])
    def test_required_env_var(self, var):
        val = os.environ.get(var, "")
        assert val, f"Required env var {var} is empty or unset"

    def test_fal_key_present(self):
        fal_key = os.environ.get("FAL_KEY", "")
        fal_ai = os.environ.get("FAL_AI_API_KEY", "")
        assert fal_key or fal_ai, (
            "Neither FAL_KEY nor FAL_AI_API_KEY is set"
        )

    def test_fal_key_normalization(self):
        """Both FAL_KEY and FAL_AI_API_KEY should resolve to the same value."""
        fal_key = os.environ.get("FAL_KEY", "")
        fal_ai = os.environ.get("FAL_AI_API_KEY", "")
        if fal_key and fal_ai:
            assert fal_key == fal_ai, (
                "FAL_KEY and FAL_AI_API_KEY are both set but differ — "
                "this causes subtle bugs"
            )


class TestFilesystem:
    """Validate output dirs, content script, and symlinks."""

    def test_output_dir_writable(self):
        output_dir = Path(os.environ.get("OUTPUT_DIR", "/data/output"))
        assert output_dir.exists(), f"Output dir {output_dir} does not exist"
        test_file = output_dir / ".pytest_write_test"
        try:
            test_file.write_text("ok")
        finally:
            test_file.unlink(missing_ok=True)

    def test_content_script_exists(self):
        script = Path(os.environ.get(
            "CONTENT_SCRIPT", "/app/scripts/ninja_content.py"
        ))
        assert script.exists(), f"Content script not found: {script}"

    def test_content_script_parses(self):
        script = Path(os.environ.get(
            "CONTENT_SCRIPT", "/app/scripts/ninja_content.py"
        ))
        if not script.exists():
            pytest.skip("Content script not found")
        source = script.read_text()
        ast.parse(source)  # raises SyntaxError if broken

    def test_output_symlink_resolves(self):
        symlink = Path("/app/output")
        if not symlink.exists() and not symlink.is_symlink():
            pytest.skip("/app/output symlink not present (non-Docker env)")
        target = symlink.resolve()
        assert target.exists(), (
            f"/app/output -> {target} does not resolve to an existing dir"
        )

    def test_broll_dir_accessible(self):
        broll = Path(os.environ.get("BROLL_DIR", "/data/output/broll"))
        if not broll.exists():
            pytest.skip(f"B-roll dir {broll} does not exist (optional)")
        assert os.access(broll, os.R_OK), f"B-roll dir {broll} not readable"


class TestRedis:
    """Validate Redis broker connectivity."""

    def test_redis_reachable(self):
        broker_url = os.environ.get("CELERY_BROKER_URL", "")
        if not broker_url:
            pytest.skip("CELERY_BROKER_URL not set")
        try:
            import redis
            r = redis.Redis.from_url(broker_url, socket_timeout=3)
            r.ping()
        except ImportError:
            # Fall back to raw socket check if redis-py not available
            import socket
            # Parse redis://host:port/db
            stripped = broker_url.replace("redis://", "")
            host_port = stripped.split("/")[0]
            parts = host_port.rsplit(":", 1)
            host = parts[0] or "localhost"
            port = int(parts[1]) if len(parts) > 1 else 6379
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            try:
                sock.connect((host, port))
                sock.sendall(b"PING\r\n")
                resp = sock.recv(64)
                assert b"PONG" in resp, f"Redis did not PONG: {resp!r}"
            finally:
                sock.close()


class TestAPIAuth:
    """Validate API keys actually authenticate (lightweight GET requests)."""

    def test_elevenlabs_auth(self):
        key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not key:
            pytest.skip("ELEVENLABS_API_KEY not set")
        resp = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": key},
            timeout=10,
        )
        assert resp.status_code == 200, (
            f"ElevenLabs auth failed: HTTP {resp.status_code}"
        )

    def test_fal_auth(self):
        key = os.environ.get("FAL_KEY", "") or os.environ.get("FAL_AI_API_KEY", "")
        if not key:
            pytest.skip("No fal.ai key set")
        resp = requests.get(
            "https://rest.alpha.fal.ai/tokens/",
            headers={"Authorization": f"Key {key}"},
            timeout=10,
        )
        # fal returns 200/404/405 on valid key; 401/403 on invalid
        assert resp.status_code not in (401, 403), (
            f"fal.ai auth failed: HTTP {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# Integration test — ~$0.50, ~3 min (opt-in via --integration)
# ---------------------------------------------------------------------------


class TestIntegration:
    """End-to-end pipeline test with a short script."""

    @pytest.fixture(autouse=True)
    def _require_integration(self, request):
        if not request.config.getoption("--integration"):
            pytest.skip("Integration tests skipped (use --integration)")

    def test_short_pipeline_run(self, tmp_path):
        """Run ninja_content.py with a minimal test script, validate output."""
        script_path = Path(os.environ.get(
            "CONTENT_SCRIPT", "/app/scripts/ninja_content.py"
        ))
        if not script_path.exists():
            pytest.fail(f"Content script not found: {script_path}")

        test_script = (
            "What's up my fellow Ninjas, this is Neurodivergent Ninja here "
            "back with another video. This is a test. Peace out ninjas."
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        env = os.environ.copy()
        env["OUTPUT_DIR"] = str(output_dir)

        result = subprocess.run(
            [
                sys.executable, str(script_path),
                "--script", test_script,
                "--broll-count", "0",
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min hard limit
            env=env,
        )

        assert result.returncode == 0, (
            f"Pipeline failed (rc={result.returncode}):\n"
            f"STDOUT: {result.stdout[-500:]}\n"
            f"STDERR: {result.stderr[-500:]}"
        )

        # Find output video
        mp4s = list(output_dir.glob("*.mp4"))
        assert mp4s, f"No .mp4 output in {output_dir}"

        video = mp4s[0]

        # Validate with ffprobe
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_type",
                "-show_entries", "format=duration",
                "-of", "json",
                str(video),
            ],
            capture_output=True,
            text=True,
        )
        assert probe.returncode == 0, f"ffprobe failed: {probe.stderr}"

        import json
        info = json.loads(probe.stdout)

        # Check for video + audio streams
        stream_types = {s["codec_type"] for s in info.get("streams", [])}
        assert "video" in stream_types, "Output missing video stream"
        assert "audio" in stream_types, "Output missing audio stream"

        # Check duration > 3 seconds
        duration = float(info.get("format", {}).get("duration", 0))
        assert duration > 3.0, f"Output too short: {duration:.1f}s"
