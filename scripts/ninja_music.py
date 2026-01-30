#!/usr/bin/env python3
"""
ninja_music.py — Add background music to ninja avatar videos.

Mixes background music into a video at low volume so the voice stays clear.
Auto-loops or trims the music to match video duration, with a fade-out at the end.

Part of the Neurodivergent Ninja content pipeline.

Usage:
    python3 ninja_music.py --input video.mp4 --output video_with_music.mp4
    python3 ninja_music.py --input video.mp4 --music track.mp3 --output out.mp4
    python3 ninja_music.py --input video.mp4 --music-dir /path/to/music/ --output out.mp4

If --music is not specified, picks a random track from the default music directory.
"""

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

# Defaults
DEFAULT_MUSIC_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"
DEFAULT_MUSIC_VOLUME = 0.15  # 15% volume for background music
DEFAULT_VOICE_VOLUME = 1.0   # 100% voice volume
FADE_OUT_DURATION = 1.5      # seconds of fade-out at the end


def get_duration(filepath: str) -> float:
    """Get duration of a media file in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            filepath,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {filepath}: {result.stderr}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def has_audio_stream(filepath: str) -> bool:
    """Check if a media file has an audio stream."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "json",
            filepath,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return False
    data = json.loads(result.stdout)
    return len(data.get("streams", [])) > 0


def find_music_track(music_dir: Path, music_file: str | None = None) -> str:
    """Find a music track to use. If music_file is given, use that. Otherwise pick random."""
    if music_file:
        if not os.path.isfile(music_file):
            raise FileNotFoundError(f"Music file not found: {music_file}")
        return music_file

    # Look for audio files in the music directory
    extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".opus"}
    tracks = [
        f for f in music_dir.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ]

    if not tracks:
        raise FileNotFoundError(
            f"No music tracks found in {music_dir}. "
            f"Add .mp3/.wav/.ogg files to {music_dir} or use --music to specify a file."
        )

    chosen = random.choice(tracks)
    print(f"🎵 Selected track: {chosen.name}")
    return str(chosen)


def add_background_music(
    input_video: str,
    output_video: str,
    music_file: str,
    music_volume: float = DEFAULT_MUSIC_VOLUME,
    voice_volume: float = DEFAULT_VOICE_VOLUME,
    fade_out: float = FADE_OUT_DURATION,
) -> None:
    """
    Mix background music into a video.

    - Loops/trims music to match video duration
    - Applies volume adjustment (music low, voice full)
    - Fades out music in the last N seconds
    - Preserves original video stream (no re-encoding video)
    """
    video_duration = get_duration(input_video)
    video_has_audio = has_audio_stream(input_video)

    print(f"📹 Video duration: {video_duration:.1f}s")
    print(f"🔊 Voice volume: {voice_volume:.0%} | Music volume: {music_volume:.0%}")
    print(f"🎵 Fade out: last {fade_out:.1f}s")

    # Calculate fade start time
    fade_start = max(0, video_duration - fade_out)

    # Build the ffmpeg filter complex
    # Music: loop if needed, trim to video duration, apply volume + fade out
    # aloop: loop enough times to cover the video (loop=-1 for infinite isn't reliable,
    # so we calculate how many loops we need)
    music_duration = get_duration(music_file)
    loops_needed = max(0, int(video_duration / music_duration))  # extra loops needed (0 = no loop)

    print(f"🎵 Music track duration: {music_duration:.1f}s → {'looping' if loops_needed > 0 else 'trimming'}")

    # Build filter graph
    #
    # Input layout:
    #   0 = video file (may have video + audio streams)
    #   1 = music file (we select audio only with 1:a)
    #
    # When the music file has embedded album art (e.g. MP3 with cover),
    # ffmpeg sees multiple streams, but we only want the audio stream.
    filters = []

    if video_has_audio:
        # Voice: apply volume
        filters.append(f"[0:a]volume={voice_volume}[voice]")

    # Music: loop → trim → volume → fade out
    if loops_needed > 0:
        # stream_loop on the input for full-file looping
        music_input_args = ["-stream_loop", str(loops_needed), "-i", music_file]
    else:
        music_input_args = ["-i", music_file]

    # Music is always input #1, select its audio stream
    music_filter = (
        f"[1:a]"
        f"atrim=0:{video_duration},"
        f"asetpts=PTS-STARTPTS,"
        f"volume={music_volume},"
        f"afade=t=out:st={fade_start}:d={fade_out}"
        f"[music]"
    )
    filters.append(music_filter)

    if video_has_audio:
        # Mix voice and music together, then upsample to 44.1kHz stereo
        # (original voice is often 16kHz mono from TTS; music is 44.1kHz stereo)
        filters.append(
            "[voice][music]amix=inputs=2:duration=first:dropout_transition=0,"
            "aresample=44100,aformat=channel_layouts=stereo[mixed]"
        )
        output_map = ["-map", "0:v", "-map", "[mixed]"]
    else:
        # No voice, just use music
        output_map = ["-map", "0:v", "-map", "[music]"]

    filter_complex = ";".join(filters)

    # Build the full ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        *music_input_args,
        "-filter_complex", filter_complex,
        *output_map,
        "-c:v", "copy",       # Don't re-encode video
        "-c:a", "aac",        # Encode mixed audio as AAC
        "-b:a", "192k",       # Good audio quality
        "-shortest",          # End when the shortest stream ends
        output_video,
    ]

    print(f"🔧 Running ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ ffmpeg stderr:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"ffmpeg failed with return code {result.returncode}")

    # Verify output
    output_duration = get_duration(output_video)
    output_size = os.path.getsize(output_video)
    print(f"✅ Output: {output_video}")
    print(f"   Duration: {output_duration:.1f}s | Size: {output_size / 1024:.0f} KB")


def main():
    parser = argparse.ArgumentParser(
        description="Add background music to ninja avatar videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Input video file",
    )
    parser.add_argument(
        "--output", "-o", required=True,
        help="Output video file",
    )
    parser.add_argument(
        "--music", "-m", default=None,
        help="Specific music file to use (default: random from music dir)",
    )
    parser.add_argument(
        "--music-dir", default=str(DEFAULT_MUSIC_DIR),
        help=f"Directory containing music tracks (default: {DEFAULT_MUSIC_DIR})",
    )
    parser.add_argument(
        "--music-volume", type=float, default=DEFAULT_MUSIC_VOLUME,
        help=f"Music volume 0.0-1.0 (default: {DEFAULT_MUSIC_VOLUME})",
    )
    parser.add_argument(
        "--voice-volume", type=float, default=DEFAULT_VOICE_VOLUME,
        help=f"Voice volume 0.0-1.0 (default: {DEFAULT_VOICE_VOLUME})",
    )
    parser.add_argument(
        "--fade-out", type=float, default=FADE_OUT_DURATION,
        help=f"Fade out duration in seconds (default: {FADE_OUT_DURATION})",
    )
    parser.add_argument(
        "--no-fade", action="store_true",
        help="Disable fade out",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"❌ Input video not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Find a music track
    try:
        music_track = find_music_track(
            Path(args.music_dir),
            args.music,
        )
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    fade = 0.0 if args.no_fade else args.fade_out

    add_background_music(
        input_video=args.input,
        output_video=args.output,
        music_file=music_track,
        music_volume=args.music_volume,
        voice_volume=args.voice_volume,
        fade_out=fade,
    )


if __name__ == "__main__":
    main()
