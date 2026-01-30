#!/usr/bin/env python3
"""
ninja_pipeline.py — Ninja avatar talking head video generator (Python wrapper)

Provides a Python API and CLI for the ninja avatar content pipeline:
  Text → ElevenLabs TTS → Ditto lip-sync → finished MP4

Usage:
    # CLI
    python ninja_pipeline.py "Shadow Operators reporting in."
    python ninja_pipeline.py --output intro.mp4 "Welcome to the channel"
    python ninja_pipeline.py --file script.txt --output episode1.mp4

    # Python API
    from ninja_pipeline import NinjaPipeline
    pipeline = NinjaPipeline()
    result = pipeline.run("Shadow Operators reporting in.")
    print(result.output_path)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


###############################################################################
# Configuration
###############################################################################
DEFAULT_VOICE_ID = "pDrEFcc78kuc76ECGkU8"
ELEVENLABS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
ENV_FILE = Path("/home/ndninja/projects/content-automation/.env")
LOCAL_OUTPUT_DIR = Path("/home/ndninja/clawd/output")

STEAM_HOST = "Steam@100.98.226.75"
AVATAR_PATH = "/home/steam/musetalk/data/video/ninja_avatar.jpg"
DITTO_CHECKPOINTS = "/home/steam/ditto/checkpoints"
DITTO_OUTPUT = "/home/steam/ditto/output"


###############################################################################
# Data classes
###############################################################################
@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    output_path: Path
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    steps_completed: list = field(default_factory=list)
    elapsed_seconds: float = 0.0


@dataclass
class VoiceSettings:
    """ElevenLabs voice settings."""
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True


###############################################################################
# Pipeline
###############################################################################
class NinjaPipeline:
    """Automated ninja avatar video generation pipeline."""

    def __init__(
        self,
        voice_id: str = DEFAULT_VOICE_ID,
        voice_settings: Optional[VoiceSettings] = None,
        output_dir: Optional[Path] = None,
        steam_host: str = STEAM_HOST,
        avatar_path: str = AVATAR_PATH,
        keep_intermediates: bool = False,
        api_key: Optional[str] = None,
        verbose: bool = True,
    ):
        self.voice_id = voice_id
        self.voice_settings = voice_settings or VoiceSettings()
        self.output_dir = output_dir or LOCAL_OUTPUT_DIR
        self.steam_host = steam_host
        self.avatar_path = avatar_path
        self.keep_intermediates = keep_intermediates
        self.verbose = verbose
        self.api_key = api_key or self._load_api_key()

    def _load_api_key(self) -> str:
        """Load ElevenLabs API key from env file."""
        if not ENV_FILE.exists():
            raise FileNotFoundError(f"Env file not found: {ENV_FILE}")
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                return line.split("=", 1)[1].strip()
        raise ValueError(f"ELEVENLABS_API_KEY not found in {ENV_FILE}")

    def log(self, msg: str):
        """Log with timestamp."""
        if self.verbose:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] {msg}", flush=True)

    def run(
        self,
        text: str,
        output_name: Optional[str] = None,
    ) -> PipelineResult:
        """Run the full pipeline: text → speech → video.

        Args:
            text: The script text to speak.
            output_name: Optional output filename (default: auto-generated).

        Returns:
            PipelineResult with output path and metadata.
        """
        t0 = time.time()
        steps = []

        if not text.strip():
            raise ValueError("Text cannot be empty")

        # Generate output name
        if not output_name:
            slug = "".join(c if c.isalnum() else "_" for c in text[:30].lower()).strip("_")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"ninja_{slug}_{ts}.mp4"
        if not output_name.endswith(".mp4"):
            output_name += ".mp4"

        self.output_dir.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(prefix="ninja-pipeline-"))

        try:
            self.log("━" * 48)
            self.log("🥷 Ninja Avatar Pipeline")
            self.log("━" * 48)
            self.log(f"Text:     {text[:80]}{'...' if len(text) > 80 else ''}")
            self.log(f"Voice:    {self.voice_id}")
            self.log(f"Output:   {output_name}")
            self.log("")

            # Step 1: TTS
            mp3_path = work_dir / "tts_output.mp3"
            wav_path = work_dir / "audio.wav"
            self._step_tts(text, mp3_path)
            steps.append("tts")

            # Step 2: Convert to WAV
            self._step_convert_audio(mp3_path, wav_path)
            steps.append("audio_convert")

            # Step 3: Ditto lip-sync
            self._step_ditto(wav_path, output_name, work_dir)
            steps.append("ditto")

            # Step 4: Retrieve
            final_path = self._step_retrieve(output_name)
            steps.append("retrieve")

            # Get video info
            duration = self._get_duration(final_path)
            file_size = final_path.stat().st_size

            elapsed = time.time() - t0
            self.log("")
            self.log("━" * 48)
            self.log("🥷 Pipeline complete!")
            self.log("━" * 48)
            self.log(f"   Output:   {final_path}")
            self.log(f"   Size:     {file_size / 1024 / 1024:.1f} MB")
            self.log(f"   Duration: {duration:.1f}s")
            self.log(f"   Elapsed:  {elapsed:.1f}s")
            self.log("")

            return PipelineResult(
                output_path=final_path,
                duration_seconds=duration,
                file_size_bytes=file_size,
                steps_completed=steps,
                elapsed_seconds=elapsed,
            )

        finally:
            if not self.keep_intermediates:
                shutil.rmtree(work_dir, ignore_errors=True)
            else:
                self.log(f"   Intermediates kept in: {work_dir}")

    def _step_tts(self, text: str, output_path: Path):
        """Step 1: Generate speech via ElevenLabs."""
        self.log("📢 Step 1/4: Generating speech via ElevenLabs...")

        payload = json.dumps({
            "text": text,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": self.voice_settings.stability,
                "similarity_boost": self.voice_settings.similarity_boost,
                "style": self.voice_settings.style,
                "use_speaker_boost": self.voice_settings.use_speaker_boost,
            },
        }).encode("utf-8")

        url = f"{ELEVENLABS_API_URL}/{self.voice_id}"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                output_path.write_bytes(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"ElevenLabs API error (HTTP {e.code}): {body}") from e

        size = output_path.stat().st_size
        self.log(f"   ✅ TTS audio generated ({size:,} bytes)")

    def _step_convert_audio(self, mp3_path: Path, wav_path: Path):
        """Step 2: Convert MP3 to WAV 16kHz mono with silence padding."""
        self.log("🔊 Step 2/4: Converting audio to WAV 16kHz mono (with silence padding)...")

        work_dir = mp3_path.parent
        raw_wav = work_dir / "audio_raw.wav"
        silence_wav = work_dir / "silence_pad.wav"

        # Convert TTS to WAV
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", "16000", "-ac", "1",
             "-acodec", "pcm_s16le", str(raw_wav)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

        # Generate 500ms silence
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
             "-t", "0.5", "-acodec", "pcm_s16le", str(silence_wav)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg silence generation failed: {result.stderr}")

        # Prepend silence to prevent AAC encoder from clipping the first word
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(silence_wav), "-i", str(raw_wav),
             "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]", "-map", "[out]",
             "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le", str(wav_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {result.stderr}")

        size = wav_path.stat().st_size
        duration = self._get_duration(wav_path)
        self.log(f"   ✅ WAV converted ({size:,} bytes, ~{duration:.0f}s, includes 0.5s padding)")

    def _ssh(self, cmd: str, check: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
        """Run an SSH command on the Steam PC."""
        return subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", self.steam_host, cmd],
            capture_output=True, text=True, timeout=timeout,
        )

    def _step_ditto(self, wav_path: Path, output_name: str, work_dir: Path):
        """Step 3: Run Ditto lip-sync on Steam PC."""
        self.log("🎬 Step 3/4: Running Ditto lip-sync on Steam PC (RTX 4090)...")

        # Create Docker run script
        run_script = work_dir / "run.sh"
        run_script.write_text(
            "#!/bin/bash\n"
            "set -e\n"
            "echo '[Ditto] Installing runtime dependencies...'\n"
            "pip install -q einops pillow\n"
            "echo '[Ditto] Running inference...'\n"
            "python inference.py \\\n"
            "    --data_root ./checkpoints/ditto_pytorch \\\n"
            "    --cfg_pkl ./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl \\\n"
            "    --audio_path /data/input/audio.wav \\\n"
            "    --source_path /data/input/source.jpg \\\n"
            f"    --output_path /data/output/{output_name}\n"
            "echo '[Ditto] Inference complete'\n"
        )
        run_script.chmod(0o755)

        # Upload files to Steam PC (via Windows then WSL)
        self.log("   Uploading audio to Steam PC...")
        for local, remote_win in [(wav_path, "audio.wav"), (run_script, "run.sh")]:
            r = subprocess.run(
                ["scp", "-q", str(local), f"{self.steam_host}:C:/Users/Steam/{remote_win}"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                raise RuntimeError(f"SCP upload failed for {remote_win}: {r.stderr}")

        # Move into WSL filesystem
        self._ssh("wsl mkdir -p /tmp/ninja-pipeline")
        self._ssh("wsl cp /mnt/c/Users/Steam/audio.wav /tmp/ninja-pipeline/audio.wav")
        self._ssh("wsl cp /mnt/c/Users/Steam/run.sh /tmp/ninja-pipeline/run.sh")
        self._ssh("wsl chmod +x /tmp/ninja-pipeline/run.sh")

        # Run Ditto Docker
        self.log("   Running Ditto Docker container...")
        docker_cmd = (
            f"wsl docker run --rm --gpus all --entrypoint bash "
            f"-v {DITTO_CHECKPOINTS}:/app/ditto/checkpoints "
            f"-v {self.avatar_path}:/data/input/source.jpg "
            f"-v /tmp/ninja-pipeline/audio.wav:/data/input/audio.wav "
            f"-v {DITTO_OUTPUT}:/data/output "
            f"-v /tmp/ninja-pipeline/run.sh:/tmp/run.sh "
            f"ditto:latest /tmp/run.sh"
        )

        result = self._ssh(docker_cmd, timeout=600)
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                self.log(f"   [Ditto] {line}")
        if result.returncode != 0:
            stderr_tail = (result.stderr or "")[-500:]
            raise RuntimeError(f"Ditto inference failed (exit {result.returncode}): {stderr_tail}")

        # Verify output
        check = self._ssh(f"wsl test -f {DITTO_OUTPUT}/{output_name}")
        if check.returncode != 0:
            raise RuntimeError(f"Ditto output not found: {DITTO_OUTPUT}/{output_name}")

        self.log("   ✅ Ditto video generated")

    def _step_retrieve(self, output_name: str) -> Path:
        """Step 4: Retrieve video from Steam PC."""
        self.log("📦 Step 4/4: Retrieving video...")

        # WSL → Windows
        self._ssh(f"wsl cp {DITTO_OUTPUT}/{output_name} /mnt/c/Users/Steam/{output_name}")

        # Windows → local
        final_path = self.output_dir / output_name
        r = subprocess.run(
            ["scp", "-q", f"{self.steam_host}:C:/Users/Steam/{output_name}", str(final_path)],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            raise RuntimeError(f"SCP download failed: {r.stderr}")

        if not final_path.exists():
            raise RuntimeError(f"Output not found at {final_path}")

        # Cleanup remote
        self._ssh(f"wsl rm -rf /tmp/ninja-pipeline", check=False)
        self._ssh(f'del C:\\Users\\Steam\\audio.wav C:\\Users\\Steam\\run.sh C:\\Users\\Steam\\{output_name}', check=False)

        return final_path

    def _get_duration(self, path: Path) -> float:
        """Get media duration in seconds."""
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(path)],
                capture_output=True, text=True,
            )
            return float(r.stdout.strip())
        except (ValueError, Exception):
            return 0.0

    # Convenience method for quick generation
    @staticmethod
    def quick(text: str, output_name: Optional[str] = None, **kwargs) -> PipelineResult:
        """One-liner pipeline run.

        Usage:
            result = NinjaPipeline.quick("Hello world!")
        """
        pipeline = NinjaPipeline(**kwargs)
        return pipeline.run(text, output_name)


###############################################################################
# CLI
###############################################################################
def main():
    parser = argparse.ArgumentParser(
        description="🥷 Ninja Avatar Talking Head Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Shadow Operators reporting in."
  %(prog)s -o intro.mp4 "Welcome to the channel"
  %(prog)s --file script.txt --output episode1.mp4
  %(prog)s --voice VOICE_ID "Custom voice test"
        """,
    )
    parser.add_argument("text", nargs="?", help="Text to speak")
    parser.add_argument("-o", "--output", help="Output filename (default: auto-generated)")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE_ID, help="ElevenLabs voice ID")
    parser.add_argument("-f", "--file", help="Read text from file")
    parser.add_argument("-k", "--keep", action="store_true", help="Keep intermediate files")
    parser.add_argument("--stability", type=float, default=0.5, help="Voice stability (0-1)")
    parser.add_argument("--similarity", type=float, default=0.75, help="Similarity boost (0-1)")
    parser.add_argument("--style", type=float, default=0.0, help="Style exaggeration (0-1)")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    # Get text
    text = args.text
    if args.file:
        text = Path(args.file).read_text().strip()
    if not text:
        parser.error("No text provided. Use positional arg or --file")

    # Build pipeline
    voice_settings = VoiceSettings(
        stability=args.stability,
        similarity_boost=args.similarity,
        style=args.style,
    )

    pipeline = NinjaPipeline(
        voice_id=args.voice,
        voice_settings=voice_settings,
        keep_intermediates=args.keep,
        verbose=not args.quiet,
    )

    try:
        result = pipeline.run(text, args.output)

        if args.json:
            print(json.dumps({
                "output_path": str(result.output_path),
                "duration_seconds": result.duration_seconds,
                "file_size_bytes": result.file_size_bytes,
                "steps_completed": result.steps_completed,
                "elapsed_seconds": result.elapsed_seconds,
            }, indent=2))
        elif args.quiet:
            print(result.output_path)

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        else:
            print(f"❌ Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
