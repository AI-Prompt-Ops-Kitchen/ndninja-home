# YouTube Auto-Upload Setup

## Overview
Automated YouTube uploads with custom thumbnails using OAuth 2.0.

## Setup Steps

### 1. Google Cloud Project
- Go to https://console.cloud.google.com/
- Create new project or use existing: `gen-lang-client-0601509945`
- Enable YouTube Data API v3

### 2. OAuth 2.0 Credentials
- Go to APIs & Services > Credentials
- Create OAuth 2.0 Client ID (Desktop App)
- Download JSON as `client_secrets.json`

### 3. First-time Auth
- Run `python youtube_auth.py` 
- Opens browser for consent
- Saves refresh token to `~/.config/youtube_uploader/token.json`

### 4. Usage
```bash
python youtube_upload.py --video output.mp4 --thumbnail output.thumb.png \
    --title "Video Title" --description "Description" --tags "tech,news"
```

## Integration
Add `--publish youtube` to ninja_content.py to auto-upload after generation.
