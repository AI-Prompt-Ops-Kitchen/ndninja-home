# CapCut API Reference

Server: `http://127.0.0.1:9000`

## Endpoints

### POST /create_draft
Create a new draft project.
```json
{"width": 1080, "height": 1920}
```
Returns: `{"success": true, "draft_id": "dfd_xxx"}`

### POST /add_video
Add video to timeline.
```json
{
  "draft_id": "dfd_xxx",
  "video_url": "file:///path/to/video.mp4",
  "start": 0,
  "end": 10,
  "target_start": 0,
  "volume": 1.0,
  "transition": "fade_in",
  "transition_duration": 0.5,
  "track_name": "main_video"
}
```

### POST /add_audio
Add audio track.
```json
{
  "draft_id": "dfd_xxx",
  "audio_url": "file:///path/to/audio.mp3",
  "start": 0,
  "end": 30,
  "target_start": 0,
  "volume": 1.0,
  "track_name": "voice"
}
```

### POST /add_text
Add text overlay.
```json
{
  "draft_id": "dfd_xxx",
  "text": "Hello World",
  "start": 0,
  "end": 5,
  "font": "Source Han Sans",
  "font_color": "#FFFFFF",
  "font_size": 48,
  "transform_y": -0.8
}
```

### POST /add_subtitle
Add SRT subtitles.
```json
{
  "draft_id": "dfd_xxx",
  "subtitle_url": "file:///path/to/subs.srt",
  "font_size": 36,
  "font_color": "#FFFFFF"
}
```

### POST /add_image
Add image overlay.
```json
{
  "draft_id": "dfd_xxx",
  "image_url": "file:///path/to/image.png",
  "width": 1080,
  "height": 1920,
  "start": 0,
  "end": 5,
  "transform_x": 0,
  "transform_y": 0
}
```

### POST /save_draft
Save draft to disk.
```json
{"draft_id": "dfd_xxx"}
```
Returns: `{"success": true, "draft_path": "/path/to/draft"}`

## Transitions

Available values for `transition`:
- `fade_in`, `fade_out`
- `slide_left`, `slide_right`, `slide_up`, `slide_down`
- `zoom_in`, `zoom_out`
- `dissolve`
- `wipe_left`, `wipe_right`
- `blur`

## URL Formats

- Local files: `file:///absolute/path/to/file.mp4`
- HTTP(S): `https://example.com/video.mp4`

## Response Format

All endpoints return:
```json
{
  "success": true|false,
  "output": "...",
  "error": "..."
}
```

## Draft Output

Drafts are saved as `dfd_xxx` folders. Copy to CapCut drafts folder:
- **Mac**: `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/`
- **Windows**: `%APPDATA%\CapCut\User Data\Projects\com.lveditor.draft\`
