---
name: css-sprite-animation
domain: Animation/Glitch
level: 3-tomoe
description: CSS animation system for 2.5D layered sprite overlays — breathing, state machines, sprite sheets, WAAPI, View Transitions, and performance benchmarks.
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
    title: "GPU Animation Best Practices"
    url: "https://smashingmagazine.com/2016/12/gpu-animation-doing-it-right/"
    date: "2026-02-19"
    confidence: high
  - type: github
    title: "Tauri CSS Animation Performance Issue"
    url: "https://github.com/tauri-apps/wry/issues/617"
    date: "2026-02-19"
    confidence: medium
  - type: web
    title: "CSS Sprite Sheets with steps() — Lean Rada"
    url: "https://leanrada.com/notes/css-sprite-sheets/"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "SVG vs Canvas vs WebGL Performance Benchmarks 2025"
    url: "https://www.svggenie.com/blog/svg-vs-canvas-vs-webgl-performance-2025"
    date: "2026-02-23"
    confidence: high
  - type: docs
    title: "MDN: Animation.commitStyles()"
    url: "https://developer.mozilla.org/en-US/docs/Web/API/Animation/commitStyles"
    date: "2026-02-23"
    confidence: high
  - type: docs
    title: "View Transitions API — Chrome for Developers"
    url: "https://developer.chrome.com/docs/web-platform/view-transitions"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "content-visibility Baseline — web.dev"
    url: "https://web.dev/blog/css-content-visibility-baseline"
    date: "2026-02-23"
    confidence: high
sources_count: 9
last_updated: 2026-02-23
can_do_from_cli: true
---

# CSS Sprite Animation for 2.5D Overlay

## Mental Model
Stack PNG layers (body, eyes, mouth) absolutely positioned. CSS keyframes for idle loops. `data-state` attribute drives state machine. `steps()` for sprite sheets. WAAPI (`element.animate()`) for programmatic one-shots. No PixiJS — CSS handles a single character overlay.

## Workflow 1: Layered Sprite Setup

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
.layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; }
.layer.eyes  { z-index: 3; top: 28%; left: 10%; width: 80%; height: 22%; }
.layer.mouth { z-index: 4; top: 55%; left: 25%; width: 50%; height: 14%; }
```

## Workflow 2: Idle Breathing + Blink

```css
@keyframes breathing {
  0%, 100% { transform: scale(1) translateY(0); }
  50%       { transform: scale(1.03) translateY(-2px); }
}
@keyframes blink {
  0%, 85%, 100% { transform: scaleY(1); }
  92%           { transform: scaleY(0.08); }
}
.avatar[data-state="idle"] .layer.body { animation: breathing 4s ease-in-out infinite; }
.avatar[data-state="idle"] .layer.eyes { animation: blink 3.5s step-start infinite; transform-origin: center; }
```
- 4s = human resting rate. `step-start` on blink = instant snap, no interpolation
- NEVER animate `left/top/width/height` — reflow. `transform` and `opacity` only

## Workflow 3: State Machine (data-state)

```css
.avatar[data-state="idle"]    .layer.body { animation: breathing 4s ease-in-out infinite; }
.avatar[data-state="talking"] .layer.body { animation: breathing 2s ease-in-out infinite; }
.avatar[data-state="alert"]   .layer.body { animation: breathing 1.2s ease-in-out infinite; }
.avatar[data-state="hidden"]             { opacity: 0; pointer-events: none; }
```
```javascript
const setState = (s) => document.querySelector('.avatar').dataset.state = s;
```
- `data-state` enforces mutual exclusivity — one value at a time, no conflicting classes

## Workflow 4: Sprite Sheet with steps()

```css
.sprite-anim {
  width: 100px; height: 100px;
  background: url('walk_cycle.png') 0 0 no-repeat;
  background-size: 800px 100px;              /* 8 frames x 100px */
  animation: walk 0.8s steps(8, jump-none) infinite;
}
@keyframes walk {
  from { background-position: 0 0; }
  to   { background-position: -800px 0; }
}
.sprite-anim.pixel-art {
  image-rendering: pixelated;   /* Chrome/Edge */
  image-rendering: crisp-edges; /* Firefox */
}
```
- `steps(N, jump-none)` = land exactly on each frame. Without it: broken smooth sliding
- CSS sprite anims run off main thread — smooth even during heavy JS work

## Workflow 5: Sprite Swaps (Visemes)

```javascript
const MOUTH_MAP = { closed: 'mouth_closed.png', open: 'mouth_open.png',
  wide: 'mouth_wide.png', oo: 'mouth_oo.png', ee: 'mouth_ee.png' };

function swapSprite(el, newSrc, fade = 150) {
  el.style.transition = `opacity ${fade}ms`;
  el.style.opacity = '0';
  setTimeout(() => { el.src = newSrc; el.style.opacity = '1'; }, fade);
}
// Preload on init
Object.values(MOUTH_MAP).forEach(s => { new Image().src = `sprite_layers/mouths/${s}`; });
```
- 150ms fade is invisible but kills the jarring pop. Preload prevents first-swap flicker

## Workflow 6: Web Animations API (WAAPI)

```javascript
// Bounce — returns Promise for chaining
function bounceAvatar() {
  return document.querySelector('.avatar').animate([
    { transform: 'translateY(0)' }, { transform: 'translateY(-15px)' }, { transform: 'translateY(0)' }
  ], { duration: 300, easing: 'ease-out' }).finished;
}

// Chain: bounce -> alert -> pulse -> idle
async function alertSequence() {
  await bounceAvatar();
  setState('alert');
  await document.querySelector('.avatar').animate(
    [{ transform: 'scale(1)' }, { transform: 'scale(1.05)' }, { transform: 'scale(1)' }],
    { duration: 200, iterations: 2 }
  ).finished;
  setState('idle');
}

// commitStyles — persist end state, free resources (no fill:'forwards' memory leak)
function fadeOut(el) {
  const anim = el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 300 });
  anim.onfinish = () => { anim.commitStyles(); anim.cancel(); };
}
```
- `finished` is a Promise — `await` for sequencing. CSS keyframes can't do this
- `commitStyles()` + `cancel()` = persist state without `fill:'forwards'` memory leak
- Programmatic: pause/resume/reverse/playbackRate all available

## Workflow 7: View Transitions for Mode Switches

```javascript
async function toggleCompact(isCompact) {
  if (!document.startViewTransition) { applyCompact(isCompact); return; }
  await document.startViewTransition(() => applyCompact(isCompact)).finished;
}
function applyCompact(c) { document.querySelector('.avatar').classList.toggle('compact', c); }
```
```css
.avatar { view-transition-name: glitch-avatar; }
::view-transition-old(glitch-avatar),
::view-transition-new(glitch-avatar) { animation-duration: 0.25s; }
```
- Snapshots old/new state, crossfades automatically. Baseline all browsers late 2025
- Firefox 144+ (Oct 2025). Use feature detect fallback for Tauri/WebKit

## Workflow 8: Compact Mode

```css
:root { --avatar-size: 250px; --anim-speed: 1; }
.avatar.compact { --avatar-size: 100px; --anim-speed: 0.85; }
.avatar { width: var(--avatar-size); transition: width 0.3s, height 0.3s; }
.avatar[data-state="idle"] .layer.body {
  animation: breathing calc(4s / var(--anim-speed)) ease-in-out infinite;
}
```
- CSS custom property for size, NOT `transform: scale()` (distorts click targets)

## Performance Benchmarks (2025)

| Tech | 100 sprites | 1K sprites | 10K sprites | Use case |
|------|-------------|-----------|-------------|----------|
| CSS/SVG | 60fps | 60fps | 12fps | 1-50 elements (overlays) |
| Canvas 2D | 60fps | 60fps | 60fps | 100-50K (2D games) |
| WebGL | 60fps | 60fps | 60fps | 10K+ (heavy rendering) |

**Glitch = 3-5 layers. CSS is the right tool.** Canvas/WebGL add complexity for zero benefit at this scale. CSS anims also run off main thread.

## Performance Checklist

| Technique | Effect | Rule |
|-----------|--------|------|
| `will-change: transform` | GPU promote | `.avatar` parent ONLY (0.5-10MB/layer) |
| `contain: strict` | Isolate repaints | Use `layout paint` if sprite overflows |
| `content-visibility: auto` | Skip offscreen render | Hidden panels only, NOT always-visible avatar |
| `commitStyles()` + `cancel()` | Persist + free WAAPI | Instead of `fill:'forwards'` (leaks memory) |
| `prefers-reduced-motion` | Accessibility | `animation: none !important` in media query |
| Avoid `filter/box-shadow` | WebKit tax | Especially on Linux (worst CSS perf platform) |

## Quick Reference

| Action | Code | Notes |
|--------|------|-------|
| Switch state | `avatar.dataset.state = 'x'` | Mutual exclusivity |
| Sprite swap | `swapSprite(el, src)` | 150ms fade |
| Sprite sheet | `steps(N, jump-none)` | N = frame count |
| WAAPI animate | `el.animate([...], opts).finished` | Promise-based |
| View Transition | `document.startViewTransition(cb)` | Auto-crossfade |
| Pause | `animation-play-state: paused` | CSS or JS |

## Integration — Glitch Overlay
- **AI brain -> overlay:** WebSocket `{action: "setState", state: "talking"}`
- **TTS viseme:** ElevenLabs audio -> mouth sprite sequence at ~10fps
- **Tauri:** `window.emit("avatar-state", payload)` -> JS data-state update
- **Assets:** `/home/ndninja/projects/glitch/assets/sprite_layers/`

## Gotchas & Limits
- **Tauri/WebKit** slower than Chromium — no `filter`, `box-shadow`, `backdrop-filter`
- **Linux = worst CSS animation platform** — test early on actual machine
- **Audio sync:** CSS timers drift. Use Web Audio API timing for tight lip-sync
- **`contain: strict`** hides overflow — use `contain: layout paint` if sprite extends beyond box
- **View Transitions:** Feature-detect with `if (!document.startViewTransition)` fallback
- **Only animate `transform` and `opacity`** — everything else triggers layout/paint
- **Preload all sprites on init** — `new Image().src = url` before first swap
