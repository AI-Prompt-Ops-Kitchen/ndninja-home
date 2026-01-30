---
name: capcut
description: Compose and edit videos using CapCut via the CapCutAPI. Use for video editing tasks that need smooth transitions, effects, looping, and professional output. Triggers when user needs to create/edit videos, add transitions, composite B-roll footage, or generate CapCut drafts for review.
---

# CapCut Video Editing Skill

Automate video editing with CapCut via the CapCutAPI Python library.

## Setup

CapCutAPI is installed at: `/home/ndninja/projects/capcut-api`

**Start the server:**
```bash
cd /home/ndninja/projects/capcut-api
source venv/bin/activate
nohup python capcut_server.py > /tmp/capcut_server.log 2>&1 &
```

Server runs on port 9000. Check with: `curl http://127.0.0.1:9000/`

## Core Capabilities

### 1. Create Draft
```python
from create_draft import create_draft
draft = create_draft(width=1080, height=1920)  # 9:16 vertical
draft_id = draft["draft_id"]
```

### 2. Add Video Track
```python
from add_video_track import add_video_track
add_video_track(
    draft_id=draft_id,
    video_path="/path/to/video.mp4",
    start_time=0,      # seconds
    duration=10,       # seconds (None = full duration)
    volume=1.0,
    transition="fade"  # fade, dissolve, slide, etc.
)
```

### 3. Add Audio Track
```python
from add_audio_track import add_audio_track
add_audio_track(
    draft_id=draft_id,
    audio_path="/path/to/audio.mp3",
    start_time=0,
    volume=1.0
)
```

### 4. Add Text/Captions
```python
from add_text_impl import add_text
add_text(
    draft_id=draft_id,
    text="Your text here",
    start_time=0,
    duration=5,
    font_size=48,
    font_color="#FFFFFF",
    position="bottom"  # top, center, bottom
)
```

### 5. Add Subtitles (SRT)
```python
from add_subtitle_impl import add_subtitle
add_subtitle(
    draft_id=draft_id,
    srt_path="/path/to/subtitles.srt",
    font_size=36,
    font_color="#FFFFFF"
)
```

### 6. Save Draft
```python
from save_draft_impl import save_draft
result = save_draft(draft_id)
# Creates dfd_XXXX folder - copy to CapCut drafts directory
```

## Transitions

Available transitions for video segments:
- `fade` - Fade in/out
- `dissolve` - Cross dissolve
- `slide_left`, `slide_right` - Slide transitions
- `zoom_in`, `zoom_out` - Zoom effects
- `wipe` - Wipe transition

## Workflow: Ninja Content Pipeline Integration

For composing ninja news videos with B-roll:

1. Create draft at 1080x1920 (9:16)
2. Add main ninja video as base track
3. Add B-roll clips at insert points with transitions
4. Add audio track (ElevenLabs TTS)
5. Add synced captions (from SRT or word timestamps)
6. Save draft → opens in CapCut for final review

Use `scripts/capcut_compose.py` for the full workflow.

## Draft Output

Drafts are saved as `dfd_XXXX` folders. To use in CapCut:

**Mac:** `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`
**Windows:** `%APPDATA%\CapCut\User Data\Projects\com.lveditor.draft\`
**Linux:** Via CapCut web or copy to accessible location

## HTTP API (Alternative)

If the server is running on port 9001:
```bash
curl -X POST http://localhost:9001/create_draft \
  -H "Content-Type: application/json" \
  -d '{"width": 1080, "height": 1920}'
```

## References

- Full API docs: `references/api.md`
- CapCutAPI repo: `/home/ndninja/projects/capcut-api`
