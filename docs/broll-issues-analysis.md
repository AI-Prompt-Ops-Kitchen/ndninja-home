# B-Roll Issues Analysis — 2026-01-30

## Problems Identified

### 1. Only 1 of 4 B-roll clips inserted

**Root cause:** The `find_broll_insert_points()` function has broken timing logic.

```python
current = 4.5  # First insert point
# Next: 4.5 + 8 = 12.5
# But video is only 14.7s, and we require 5s padding at end
# 12.5 > (14.7 - 5.0 = 9.7), so loop exits!
```

For a 14.7s video, the function only generates 1 insert point because:
- It uses `loop_duration + 3.0 = 8s` between B-roll clips
- It requires `main_duration - 5.0` minimum space at end
- Math: Only room for 1 insert at 4.5s before hitting the 9.7s cutoff

**Fix needed:** Better distribution logic that actually uses all B-roll clips.

### 2. Freeze detection fails

**Root cause:** Hash-based comparison expects IDENTICAL frames.

Veo videos don't have perfectly identical frames at loop points — they have subtle variations. The MD5 hash comparison is too strict.

**Fix options:**
- Use perceptual hashing (pHash) instead of MD5
- Use SSIM (structural similarity) metric
- Skip detection entirely and use even distribution

### 3. Face freeze/glitch before B-roll

**Root cause:** Veo generation artifact.

This is NOT a post-processing issue. Veo sometimes generates:
- Facial glitches
- Mouth disappearing
- Brief freezes mid-clip

**Fix options:**
- Regenerate video (hit or miss)
- Use better prompts (ask for smooth continuous motion)
- Accept imperfection and hide with more frequent B-roll
- Use a different video model

## Proposed Solutions

### Option A: Fix B-roll timing (quick fix)
Modify compositor to evenly distribute B-roll based on clip count, not freeze detection.

```python
# Even distribution: insert B-roll at regular intervals
interval = main_duration / (num_broll + 1)
insert_points = [interval * (i + 1) for i in range(num_broll)]
```

### Option B: Use B-roll to hide ALL loop points
If Veo creates an 8s clip and we need 15s, we loop ~2x. 
Insert B-roll at EVERY loop transition (~8s mark).

### Option C: Generate longer unique content
Use multiclip mode to generate 3-4 different Veo clips and concatenate them, reducing repetition and avoiding single-clip artifacts.

### Option D: Different video approach
- Pre-made avatar video loops (reliable, no generation artifacts)
- MuseTalk/SadTalker lip sync on static image
- Accept simpler animations

## Recommended Path Forward

1. **Immediate fix:** Even B-roll distribution (Option A)
2. **Short term:** Hide loop points with B-roll (Option B)  
3. **Medium term:** Multiclip mode for variety (Option C)
4. **Long term:** Evaluate avatar alternatives for reliability

## Key Insight

The face freeze is a **generation problem**, not a composition problem.
We can hide it with B-roll, but we can't fix it in post.
