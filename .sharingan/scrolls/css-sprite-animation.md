---
name: css-sprite-animation
domain: Animation/Glitch
level: 2-tomoe
description: CSS animation system for 2.5D layered sprite overlays — breathing, state machines, sprite swaps, and Tauri overlay performance gotchas.
sources:
  - type: docs
    title: "MDN: Using CSS Animations"
    url: "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_animations/Using_CSS_animations"
    date: "2026-02-19"
    confidence: high
  - type: docs
    title: "MDN: Web Animations API"
    url: "https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API/Using_the_Web_Animations_API"
    date: "2026-02-19"
    confidence: high
  - type: web
    title: "CSS Sprites & Sprite Sheet Animation"
    url: "https://css-tricks.com/css-sprites/"
    date: "2026-02-19"
    confidence: high
  - type: web
    title: "GPU Animation Best Practices"
    url: "https://smashingmagazine.com/2016/12/gpu-animation-doing-it-right/"
    date: "2026-02-19"
    confidence: high
  - type: github
    title: "Tauri CSS Animation Performance Issue"
    url: "https://github.com/tauri-apps/wry/issues/617"
    date: "2026-02-19"
    confidence: medium
last_updated: 2026-02-19
can_do_from_cli: true
---

# CSS Sprite Animation for 2.5D Overlay

## Mental Model
Stack separate PNG layers (body, eyes, mouth) absolutely inside a container. CSS keyframes animate transforms/opacity for idle states. JavaScript swaps a `data-state` attribute — CSS rules respond to that state. No sprite sheets, no PixiJS — pure CSS is the right tool for a single character overlay.

## Prerequisites
- PNG assets with transparent backgrounds (rembg or hand-drawn)
- Basic HTML/CSS/JS knowledge
- Tauri v2 project (for overlay context)

## Core Workflows

### Workflow 1: Layered Sprite Setup
**When to use:** Building the base HTML/CSS structure for Glitch

```html
<div class="avatar" data-state="idle">
  <img class="layer body"  src="pose_nobg_neutral.png">
  <img class="layer eyes"  src="eyes_neutral.png">
  <img class="layer mouth" src="mouth_closed.png">
</div>
```

```css
.avatar {
  position: relative;
  width: var(--avatar-size, 250px);
  height: calc(var(--avatar-size, 250px) * 1.8);
  will-change: transform;
  contain: strict;
}

.layer {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  object-fit: contain;
}

.layer.eyes  { z-index: 3; top: 28%; left: 10%; width: 80%; height: 22%; }
.layer.mouth { z-index: 4; top: 55%; left: 25%; width: 50%; height: 14%; }
```

**Gotchas:**
- Parent MUST be `position: relative` — children anchor to it
- All PNGs need transparent backgrounds or layers bleed through
- Fine-tune `top/left/width/height` of eyes/mouth by eyeballing at actual display size

---

### Workflow 2: Idle Breathing Animation
**When to use:** Default always-running idle state

```css
@keyframes breathing {
  0%, 100% { transform: scale(1) translateY(0); }
  50%       { transform: scale(1.03) translateY(-2px); }
}

@keyframes blink {
  0%, 85%, 100% { transform: scaleY(1); }
  92%           { transform: scaleY(0.08); }
}

.avatar[data-state="idle"] .layer.body {
  animation: breathing 4s ease-in-out infinite;
}

.avatar[data-state="idle"] .layer.eyes {
  animation: blink 3.5s step-start infinite;
  transform-origin: center;
}
```

**Gotchas:**
- Human breathing = ~4s per cycle. Slower feels calmer, faster = anxious
- Blink: 90% open, close in 0.1s, reopen. `step-start` = no interpolation
- NEVER animate `left/top/width/height` — causes reflow. Use `transform` only

---

### Workflow 3: State Machine via Data Attributes
**When to use:** Switching between idle, talking, alert, hidden modes

```css
/* Each state drives different animations */
.avatar[data-state="idle"]    .layer.body { animation: breathing 4s ease-in-out infinite; }
.avatar[data-state="talking"] .layer.body { animation: breathing 2s ease-in-out infinite; }
.avatar[data-state="alert"]   .layer.body { animation: breathing 1.2s ease-in-out infinite; }
.avatar[data-state="hidden"]             { opacity: 0; pointer-events: none; }
```

```javascript
function setState(newState) {
  document.querySelector('.avatar').dataset.state = newState;
}

// Usage
setState('talking');  // Speed up breathing, enable mouth anim
setState('idle');     // Back to slow breathing
setState('hidden');   // Gone instantly (or fade — add transition)
```

**Gotchas:**
- Data attributes enforce mutual exclusivity (only one value at a time)
- Beats class-toggling — no risk of multiple conflicting states active
- Add `transition: opacity 0.3s` to `.avatar` for smooth show/hide

---

### Workflow 4: Sprite Swaps (Mouth Visemes, Eye States)
**When to use:** Changing eye/mouth image during talking or expressions

```javascript
const MOUTH_MAP = {
  closed: 'mouth_closed.png',
  open:   'mouth_open.png',
  wide:   'mouth_wide.png',
  oo:     'mouth_oo.png',
  ee:     'mouth_ee.png',
};

function setMouth(viseme) {
  document.querySelector('.layer.mouth').src =
    `sprite_layers/mouths/${MOUTH_MAP[viseme]}`;
}

function setEyes(state) {
  document.querySelector('.layer.eyes').src =
    `sprite_layers/eyes/eyes_crop_${state}.png`;
}
```

**Smooth crossfade version (no jarring swaps):**
```javascript
function swapSprite(el, newSrc, fadeDuration = 150) {
  el.style.transition = `opacity ${fadeDuration}ms`;
  el.style.opacity = '0';
  setTimeout(() => {
    el.src = newSrc;
    el.style.opacity = '1';
  }, fadeDuration);
}
```

**Gotchas:**
- Raw `img.src =` swap is instant and jarring — always fade
- 150ms fade is invisible to user but eliminates the pop
- Preload images on init to avoid flicker on first swap

---

### Workflow 5: Compact Mode Scaling
**When to use:** Switching Glitch from full (250px) to compact (100px) corner sprite

```css
:root { --avatar-size: 250px; --anim-speed: 1; }

.avatar.compact { --avatar-size: 100px; --anim-speed: 0.85; }

.avatar {
  width: var(--avatar-size);
  transition: width 0.3s ease-in-out, height 0.3s ease-in-out;
}

.avatar[data-state="idle"] .layer.body {
  animation: breathing calc(4s / var(--anim-speed)) ease-in-out infinite;
}
```

```javascript
function setCompact(isCompact) {
  document.querySelector('.avatar').classList.toggle('compact', isCompact);
}
```

**Gotchas:**
- Scale from 250→100 via CSS custom property, not `transform: scale()` — scale distorts click targets
- Slower breathing in compact mode (feels less frantic at small size)
- Pre-create 100px asset versions if quality matters — scaling down 250px renders fine though

---

## Command Reference

| Action | How | Notes |
|--------|-----|-------|
| Switch state | `avatar.dataset.state = 'talking'` | Data attribute enforces one state |
| Swap mouth | `el.src = newSrc` + opacity fade | 150ms fade hides seam |
| Pause animation | `animation-play-state: paused` | Via CSS or JS style |
| Compact mode | `.classList.toggle('compact')` | CSS var drives size |
| GPU promote | `will-change: transform` | On parent `.avatar` only |
| Isolate repaints | `contain: strict` | Prevents page-wide repaints |

## Integration Points — Glitch Overlay
- **AI brain → overlay:** WebSocket sends `{action: "setState", state: "talking"}` or `{action: "setMouth", viseme: "oo"}`
- **TTS viseme engine:** Maps ElevenLabs audio to mouth sprite sequence at ~10fps
- **Tauri commands:** Rust side calls `window.emit("avatar-state", payload)` → JS listener updates data-state
- **Sprite assets:** `/home/ndninja/projects/glitch/assets/sprite_layers/`

## Limitations & Gaps
- **Tauri/WebKit performance:** Known slower than Chromium — avoid `filter`, `box-shadow`, `backdrop-filter`
- **Linux is worst platform** for CSS animation smoothness — test early on actual machine
- **Audio sync precision:** CSS timers drift. For tight lip-sync, use Web Audio API timing, not setTimeout
- **`will-change` memory cost:** ~0.5-10MB per promoted layer — apply to `.avatar` parent only, not every child
- **`contain: strict`** hides overflow — if Glitch sprite overflows her container, switch to `contain: layout paint`
- Visual-only: I haven't built this yet — proportions of eye/mouth positioning need live calibration

## Tips & Best Practices
- **Only animate `transform` and `opacity`.** Everything else causes reflow.
- **One `will-change: transform` on the parent** — children inherit compositing, no extra VRAM.
- **`data-state` over class toggling** — impossible to accidentally have two conflicting states.
- **4s breathing cycle** = human resting rate. Feels alive without being distracting.
- **Always crossfade sprite swaps** — even 100ms opacity fade removes 100% of jarring pops.
- **Respect `prefers-reduced-motion`:** `@media (prefers-reduced-motion: reduce) { .avatar { animation: none; } }`
- **Preload all sprite images on init** — `new Image().src = url` in JS before first swap.
- **Test compact mode at actual 100px size** — eye/mouth pixel offsets that look fine at 250px go wrong at 100px.
