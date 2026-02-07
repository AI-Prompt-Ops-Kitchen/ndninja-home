# Instagram Graph API Setup Guide

**Goal:** Enable automated Reel posting via the official Meta API (free, no risk of account ban)

**Time required:** ~2 hours (one-time setup)

**Prerequisites:**
- Instagram account (any type to start)
- Facebook account

---

## Phase 1: Instagram Account Setup (5 min)

1. **Open Instagram app** → Settings → Account → Switch to Professional Account
2. **Choose "Creator"** (or "Business" if you prefer)
3. **Pick a category** (doesn't really matter, can change later)
4. Done — account is now API-eligible

---

## Phase 2: Facebook Page Setup (5 min)

1. **Go to:** https://www.facebook.com/pages/create
2. **Create a Page** — name it anything (e.g., "NN Content" or your brand name)
3. **Set Page visibility to "Unpublished"** if you don't want it public:
   - Page Settings → General → Page Visibility → Unpublished
4. **Link Instagram to this Page:**
   - Page Settings → Linked Accounts → Instagram → Connect Account
   - Log in to Instagram when prompted
   - Authorize the connection

---

## Phase 3: Meta Developer App (30 min)

1. **Go to:** https://developers.facebook.com/
2. **Log in** with your Facebook account
3. **Click "My Apps"** → "Create App"
4. **Choose app type:** "Business" (or "Consumer" if Business isn't available)
5. **App name:** Whatever you want (e.g., "Ninja Content Automation")
6. **Create the app**

### Add Instagram Product:
7. In your app dashboard, find **"Add Products"**
8. Find **"Instagram Graph API"** → Click "Set Up"
9. Go to **"Instagram API with Instagram Login"** section

### Configure Permissions:
10. Go to **App Review → Permissions and Features**
11. Request these permissions:
    - `instagram_basic` — Read profile/media
    - `instagram_content_publish` — Post content (THIS IS THE KEY ONE)
    - `instagram_manage_comments` — Optional, for engagement
    - `instagram_manage_insights` — Optional, for analytics

### Generate Tokens:
12. Go to **Tools → Graph API Explorer**
13. Select your app from dropdown
14. Click **"Generate Access Token"**
15. Select the Instagram permissions
16. Authorize when prompted
17. **Copy the access token** — this is your short-lived token

### Get Long-Lived Token:
18. Exchange short-lived token for 60-day token:
```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
```
19. Save the long-lived token securely

### Get Instagram User ID:
20. With your token, call:
```bash
curl -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_TOKEN"
```
21. Find the Page ID, then:
```bash
curl -X GET "https://graph.facebook.com/v18.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
```
22. Save the `instagram_business_account.id` — this is your IG User ID

---

## Phase 4: Test the API (10 min)

### Post a test Reel:

**Step 1: Create media container**
```bash
curl -X POST "https://graph.facebook.com/v18.0/IG_USER_ID/media" \
  -d "media_type=REELS" \
  -d "video_url=https://YOUR_PUBLIC_VIDEO_URL.mp4" \
  -d "caption=Test post from API 🚀" \
  -d "access_token=YOUR_TOKEN"
```

**Step 2: Publish the container**
```bash
curl -X POST "https://graph.facebook.com/v18.0/IG_USER_ID/media_publish" \
  -d "creation_id=CONTAINER_ID_FROM_STEP_1" \
  -d "access_token=YOUR_TOKEN"
```

---

## Phase 5: Clawd Integration

Once you have:
- `IG_USER_ID` — Your Instagram Business Account ID
- `ACCESS_TOKEN` — Long-lived token (refresh every 60 days)
- `APP_ID` and `APP_SECRET` — For token refresh

I'll create `scripts/instagram_upload.py` similar to the YouTube uploader.

---

## Video Specs for Reels

- **Format:** MP4 or MOV
- **Max size:** 100MB
- **Max length:** 90 seconds (some accounts: 60s)
- **Aspect ratio:** 9:16 recommended
- **Resolution:** Max 1920px width
- **Frame rate:** 23-60 FPS
- **Video codec:** H.264 or HEVC
- **Audio:** AAC, 48kHz max, stereo

Our YouTube Shorts already meet these specs ✅

---

## Token Refresh (Every 60 Days)

Long-lived tokens expire after 60 days. Refresh before expiry:

```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=CURRENT_TOKEN"
```

I can set up a cron job to remind you (or auto-refresh if we store the app secret).

---

## Troubleshooting

**"Invalid OAuth access token"**
→ Token expired, regenerate it

**"Media posted but not visible"**
→ Check video specs, Instagram silently rejects invalid formats

**"Application does not have permission"**
→ Need to request `instagram_content_publish` in App Review

**Rate limited**
→ 200 requests/hour limit, wait for reset

---

## Notes

- The video must be publicly accessible via URL for the API to fetch it
- We can use a temp cloud storage (or serve locally via ngrok) for uploads
- Alternative: Use resumable upload endpoint for large files

---

*Guide created: 2026-02-01*
*Status: Ready for user to execute*
