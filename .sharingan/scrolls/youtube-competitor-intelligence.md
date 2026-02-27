---
name: youtube-competitor-intelligence
domain: Content/Strategy
level: 3-tomoe
description: Continuous competitor research system for gaming/tech YouTube channels — extract content patterns, engagement formulas, title/tag optimization, and content archetype taxonomy to sharpen the Neurodivergent Ninja channel strategy.
sources:
  - type: methodology
    title: "yt-dlp metadata extraction + engagement ratio analysis"
    url: "https://github.com/yt-dlp/yt-dlp"
    date: "2026-02-26"
    confidence: high
  - type: field-tested
    title: "RaumMkII channel analysis — Shorts engagement benchmarking"
    url: "https://www.youtube.com/@RaumMkII"
    date: "2026-02-26"
    confidence: medium
last_updated: 2026-02-26
can_do_from_cli: true
---

# YouTube Competitor Intelligence

## Mental Model
Study what works on gaming YouTube by reverse-engineering successful channels. Instead of guessing what titles, thumbnails, or formats perform well, extract hard data from competitors and identify repeatable patterns. The goal is not to copy — it is to understand the underlying mechanics of engagement and apply them to the Ninja brand identity. Think of it as Sharingan in its purest form: watch, learn, adapt.

## The Secret Sauce Formula

Working theory for viral Shorts performance:

```
VIRAL SHORT = (Trending Game Moment x Emotional Hook x Meme Layer) / Duration
              + Community Energy + SEO Tags
```

**Breakdown:**
- **Trending Game Moment** — ride the wave, don't create it. New banner, patch notes, controversy, leak.
- **Emotional Hook** — the first 1-2 seconds must trigger a feeling: hype, outrage, FOMO, disbelief.
- **Meme Layer** — community in-jokes, shared vocabulary ("eating good", "went Nuclear"), reaction culture.
- **Duration** — shorter is better for completion rate. 30-45s beats 90s for algorithm favor. Longer only if retention holds.
- **Community Energy** — comments, shares, saves. A video with 100 comments and 500 views outranks one with 10 comments and 5000 views in the algorithm's eyes.
- **SEO Tags** — game name + event + emotional keyword. "Genshin Impact 5.4 INSANE new character" not "New character announcement."

## Key Metrics

| Metric | Formula | What It Tells You |
|--------|---------|-------------------|
| Like:View Ratio | `likes / views` | Content resonance. >4% is strong, >7% is exceptional |
| Comment:View Ratio | `comments / views` | Community engagement. >1% means people care enough to talk |
| Views Per Second | `views / duration_seconds` | Efficiency — are people watching per second of content invested? |
| Engagement Score | `(likes + comments * 5) / views` | Weighted engagement — comments are 5x more valuable than likes |
| Upload Velocity | `videos_per_week` | How aggressively the channel publishes |
| Avg Duration | `mean(duration_seconds)` | Sweet spot for the niche |
| Tag Count | `len(tags)` | SEO saturation level |
| Title Length | `len(title)` | Optimal character count for CTR |
| Emoji Density | `count(emojis_in_title) / len(title)` | Title formatting patterns |

## Content Archetype Taxonomy

Every gaming YouTube Short falls into one of these archetypes. Tag each competitor video during analysis:

| Archetype | Description | Example Title Pattern |
|-----------|-------------|----------------------|
| **Waifu Reveal** | New character showcase, design reaction, banner hype | "NEW 5-STAR IS INSANE", "She's GORGEOUS" |
| **Meme Reaction** | Community memes, cursed builds, funny moments | "When the gacha hits different", "POV: you lost 50/50" |
| **Lore Clip** | Story moments, lore theory, cinematic reaction | "This changes EVERYTHING", "The truth about X" |
| **Engagement Bait** | Controversial take, ranking, tier list snippet | "WORST character in the game??", "Top 5 BROKEN units" |
| **Community Shitpost** | Low-effort high-engagement meme content, inside jokes | "Day 47 of waiting for X", absurdist humor |
| **Hot Take** | Opinionated stance designed to provoke discussion | "Nobody talks about THIS problem", "Unpopular opinion:" |
| **News Roundup** | Multi-story news digest, patch notes, event calendar | "EVERYTHING new in 5.4", "This week in gaming" |
| **Gameplay Clip** | Raw gameplay highlight, boss kill, clutch moment | "0.1% chance and it HAPPENED", "Fastest clear EVER" |

**Tracking insight:** The best-performing channels mix archetypes. Pure news = boring. Pure memes = no authority. The sweet spot is News Roundup with Meme Layer or Hot Take with Engagement Bait energy.

## Methodology: How to Analyze a Channel

### Step 1: Download Channel Metadata

```bash
# Download metadata for all videos (no actual video download)
yt-dlp --flat-playlist --print-to-file "%(id)s|%(title)s|%(view_count)s|%(like_count)s|%(duration)s|%(upload_date)s|%(tags)s" \
  metadata.txt "https://www.youtube.com/@RaumMkII/shorts"

# Or get full JSON metadata for deeper analysis
yt-dlp --flat-playlist --dump-json --no-download \
  "https://www.youtube.com/@RaumMkII/shorts" > channel_shorts.jsonl
```

### Step 2: Extract Top Performers

```python
import json

videos = []
with open("channel_shorts.jsonl") as f:
    for line in f:
        v = json.loads(line)
        videos.append({
            "id": v["id"],
            "title": v["title"],
            "views": v.get("view_count", 0),
            "likes": v.get("like_count", 0),
            "comments": v.get("comment_count", 0),
            "duration": v.get("duration", 0),
            "upload_date": v.get("upload_date", ""),
            "tags": v.get("tags", []),
            "description": v.get("description", ""),
        })

# Sort by views, get top 20
top = sorted(videos, key=lambda x: x["views"], reverse=True)[:20]

# Compute engagement ratios
for v in top:
    if v["views"] > 0:
        v["like_ratio"] = round(v["likes"] / v["views"] * 100, 2)
        v["comment_ratio"] = round(v["comments"] / v["views"] * 100, 2)
        v["views_per_sec"] = round(v["views"] / max(v["duration"], 1), 1)
```

### Step 3: Analyze Title Patterns

```python
import re
from collections import Counter

# Extract common words/phrases from top video titles
all_words = []
for v in top:
    words = re.findall(r'[A-Z]{2,}', v["title"])  # ALL-CAPS words (emotional hooks)
    all_words.extend(words)

caps_freq = Counter(all_words).most_common(20)
# Common results: "NEW", "INSANE", "FREE", "BROKEN", "BEST", "THIS"

# Average title length
avg_title_len = sum(len(v["title"]) for v in top) / len(top)

# Tag frequency across top performers
all_tags = []
for v in top:
    all_tags.extend(v["tags"])
tag_freq = Counter(all_tags).most_common(30)
```

### Step 4: Extract Thumbnail Frames

```bash
# Download top video thumbnails for visual analysis
for vid_id in $(head -20 top_ids.txt); do
    curl -o "thumbs/${vid_id}.jpg" \
      "https://img.youtube.com/vi/${vid_id}/maxresdefault.jpg"
done
```

### Step 5: Classify Content Archetypes

Manually tag (or use LLM-assisted classification) each top video with its archetype from the taxonomy above. Build a distribution:

```python
archetype_counts = Counter(v["archetype"] for v in top)
# Example output:
# {"news_roundup": 6, "waifu_reveal": 5, "hot_take": 4, "engagement_bait": 3, "meme_reaction": 2}
```

### Step 6: Compute Channel Benchmarks

```python
benchmarks = {
    "avg_views": sum(v["views"] for v in videos) / len(videos),
    "median_views": sorted(v["views"] for v in videos)[len(videos)//2],
    "avg_like_ratio": sum(v.get("like_ratio", 0) for v in top) / len(top),
    "avg_duration": sum(v["duration"] for v in videos) / len(videos),
    "upload_frequency": len(videos) / weeks_active,
    "top_archetype": archetype_counts.most_common(1)[0],
    "avg_tags_per_video": sum(len(v["tags"]) for v in videos) / len(videos),
}
```

## Channels to Track

### Tier 1: Direct Competitors (Gaming Shorts, Avatar-based)
| Channel | Why Track | Focus |
|---------|-----------|-------|
| **RaumMkII** | Similar niche (gacha gaming Shorts), fast growth | Title patterns, upload cadence, engagement bait style |
| **Bloo** | 2.5M subs, single avatar format | How far the avatar format scales, content mix |

### Tier 2: Aspirational (Large Gaming Channels)
| Channel | Why Track | Focus |
|---------|-----------|-------|
| **Vars II** | Gaming analysis Shorts, high engagement | How to make analytical content work in Short format |
| **SomeCallMeJohnny** | Consistent gaming commentary | Tone, pacing, how personality drives retention |

### Adding New Channels
The methodology works for any channel. To add one:
1. Get the channel URL or `@handle`
2. Run the metadata extraction (Step 1)
3. Compute benchmarks (Steps 2-6)
4. Compare against existing channel benchmarks
5. Add to the tracking table above with rationale

## Automation Ideas

### Periodic New Upload Detection

```bash
#!/bin/bash
# cron: 0 */6 * * * (every 6 hours)
# Check tracked channels for new uploads since last check

CHANNELS=("@RaumMkII" "@Bloo")
LAST_CHECK_FILE="$HOME/.sharingan/training/competitor_last_check.txt"
LAST_CHECK=$(cat "$LAST_CHECK_FILE" 2>/dev/null || echo "20260201")

for channel in "${CHANNELS[@]}"; do
    yt-dlp --flat-playlist --print "%(id)s|%(title)s|%(view_count)s|%(upload_date)s" \
      --dateafter "$LAST_CHECK" \
      "https://www.youtube.com/${channel}/shorts" >> new_uploads.txt
done

date +%Y%m%d > "$LAST_CHECK_FILE"

# Count new uploads
NEW_COUNT=$(wc -l < new_uploads.txt)
if [ "$NEW_COUNT" -gt 0 ]; then
    # Emit Rasengan event
    python3 -c "
import httpx
httpx.post('http://localhost:8050/events', json={
    'event_type': 'competitor.new_uploads',
    'source': 'competitor-intel-cron',
    'payload': {'count': $NEW_COUNT, 'channels': '${CHANNELS[*]}'}
})
"
fi
```

### View Threshold Alert

When a competitor video crosses a view threshold (e.g., 50K views in 24 hours), flag it for deep analysis:

```python
# In the periodic check script
for video in new_uploads:
    if video["views"] > 50000 and video["age_hours"] < 24:
        # This video is popping off — analyze it NOW
        emit_rasengan_event("competitor.viral_detected", {
            "video_id": video["id"],
            "title": video["title"],
            "views": video["views"],
            "channel": video["channel"],
            "url": f"https://youtube.com/shorts/{video['id']}"
        })
```

### Rasengan Rules for Competitor Events

```json
{
    "name": "competitor_viral_alert",
    "event_pattern": "competitor.viral_detected",
    "conditions": {"payload.views": {"$gt": 50000}},
    "actions": [
        {"type": "log", "message": "VIRAL COMPETITOR: {payload.title} ({payload.views} views)"},
        {"type": "emit", "event_type": "analysis.requested", "payload": {"source": "competitor_intel"}}
    ],
    "cooldown_seconds": 3600
}
```

## Integration Points

### Rasengan Event Hub
- `competitor.new_uploads` — emitted when tracked channels post new content
- `competitor.viral_detected` — emitted when a video crosses the view threshold
- `analysis.requested` — triggers deeper analysis workflow

### Sharingan Scroll: youtube-competitor-playbook.md (Future)
Findings from this intelligence system feed into a separate playbook scroll that documents proven formulas. This scroll is the HOW (methodology), the playbook is the WHAT (actionable recipes).

### Shadow Council
Feed competitor analysis data to council agents for strategic interpretation. "Channel X is posting 3x/day with 40s average duration and getting 5% like ratios — what should we adjust?"

### Dojo Script Workshop
Tag competitor video archetypes can inform the Script Workshop's tone and structure suggestions. If "hot take + engagement bait" is performing well this week, the scriptgen pipeline can bias toward that archetype.

### Content Calendar
Weekly competitor digest can highlight trending games and topics to prioritize. If every competitor is covering the same patch notes, either join the wave early or deliberately counter-program.

## Command Reference

| Action | How | Notes |
|--------|-----|-------|
| Download channel metadata | `yt-dlp --flat-playlist --dump-json --no-download "URL"` | Outputs JSONL |
| Get video thumbnails | `curl "https://img.youtube.com/vi/ID/maxresdefault.jpg"` | Max quality |
| Get video details | `yt-dlp --dump-json --no-download "https://youtube.com/shorts/ID"` | Single video |
| Check new uploads | `yt-dlp --flat-playlist --dateafter YYYYMMDD` | Since date filter |
| Download video for frame analysis | `yt-dlp -f "bestvideo[height<=720]" --no-audio` | 720p is enough for analysis |

## Limitations & Gaps

- **No comment sentiment analysis** — we track comment COUNT but not what people are saying. Future: sample top comments for sentiment/themes.
- **No thumbnail visual analysis at scale** — downloading and manually reviewing thumbnails does not scale. Future: use Gemini multimodal to classify thumbnail styles (face closeup, text-heavy, gameplay screenshot, etc.)
- **Private metrics invisible** — we cannot see CTR, average view duration, or impressions. Only public metrics (views, likes, comments) are available.
- **Historical data limited** — yt-dlp gets current view counts, not growth curves. We see the final state, not velocity over time. Future: periodic snapshots to compute growth rate.
- **Manual archetype tagging** — classification is currently human judgment. Future: few-shot LLM classifier using the taxonomy.
- **No A/B title testing** — we can see what titles competitors use but cannot test alternatives. We can only learn from their experiments.

## Tips & Best Practices

1. **Analyze weekly, not daily** — daily checking leads to reactive strategy. Weekly batches reveal trends.
2. **Focus on outliers, not averages** — a channel's top 10% of videos reveal their formula. The bottom 90% is noise.
3. **Track the DELTA, not the absolute** — a 10K-sub channel getting 500K views on a video is more interesting than a 5M-sub channel getting 500K views.
4. **Study failures too** — when a competitor's video flops (way below their average), ask why. It reveals what NOT to do.
5. **Cross-reference with trending topics** — a video's success is often 80% timing and 20% execution. Same content a week later might flop.
6. **Save metadata snapshots** — store the JSONL files with dates so you can track how a channel's strategy evolves over months.
7. **Don't chase metrics blindly** — high view count with low like ratio means clickbait that disappoints. Aim for both.
8. **The 48-hour window matters most** — check competitor videos at 48 hours post-upload. That is when YouTube's algorithm decides if a video gets pushed or buried.
