```markdown
---
name: spline-3d-web
domain: 3D/Web
level: 3-tomoe
description: Browser-based 3D design tool for creating interactive web elements. Embed 3D scenes directly in websites with mouse-reactive animations and scroll-triggered sequences. Full Code API for programmatic control. Native Webflow integration for no-code interaction binding.
sources:
  - type: youtube
    title: "AntiGravity + Spline Builds Insane 3D Websites (NEW Skill)"
    url: "https://www.youtube.com/watch?v=csOEsfiBfvo"
    channel: "RoboNuggets"
    date: "2026-02"
    confidence: medium
  - type: docs
    title: "Spline Official Documentation"
    url: "https://docs.spline.design"
    date: "2026-02"
    confidence: high
  - type: github
    title: "react-spline — Official React/Next.js component"
    url: "https://github.com/splinetool/react-spline"
    date: "2026-02"
    confidence: high
  - type: youtube
    title: "Build Beautiful Websites with AI Agents + Spline 3D (Full Walkthrough)"
    url: "https://youtu.be/R9c_JQrEtu8"
    channel: "RoboNuggets"
    date: "2026-02"
    confidence: medium
  - type: web
    title: "Spline Pricing Page"
    url: "https://spline.design/pricing"
    date: "2026-02"
    confidence: high
  - type: youtube
    title: "Create a 3D Scroll Animation for Beginners – Spline + Framer Tutorial"
    url: "https://www.youtube.com/watch?v=j5sEe5NQtUU"
    channel: "Spline"
    date: "2026-02"
    confidence: high
  - type: youtube
    title: "New Spline & Webflow Integration"
    url: "https://www.youtube.com/watch?v=NhtNciucUOE"
    channel: "Timothy Ricks"
    date: "2026-02"
    confidence: high
  - type: youtube
    title: "Expo in 100 Seconds"
    url: "https://www.youtube.com/watch?v=vFW_TxKLyrE"
    channel: "Fireship"
    date: "2026-02"
    confidence: high
last_updated: 2026-02-19
can_do_from_cli: partial
mangekyo_eligible: false
---

# Spline — 3D Design for the Web

## Mental Model

Spline is a browser-based 3D design tool — think Figma but for 3D. You create or remix interactive 3D scenes and export them as embeddable web components. Assets respond to mouse movement, clicks, **scroll position**, and keyboard — making websites feel premium and cinematic.

**Key differentiator:** Everything runs in the browser. No Unity, no Blender. Design, animate, add physics/interactions, and export to web/iOS/Android from one tool.

**Code API vs Real-time API:** The *Code API* (`@splinetool/runtime`) lets external code control scenes programmatically. The *Real-time API* is for connections created inside the Spline editor (webhooks, external data). They're separate systems.

**Scroll animations:** Spline's state-based system + scroll event trigger enables **staggered, multi-object animations keyed to page scroll position** — leaf growth, camera dolly, rotations — all declaratively in the editor, no timeline coding required.

## Prerequisites

| Requirement | Details | Free Tier? |
|---|---|---|
| Spline account | Sign up at [spline.design](https://spline.design) | Yes — unlimited personal files, watermarked exports |
| Modern browser | Chrome/Edge recommended (WebGL required) | Yes |
| Node.js (for dev) | Required for `@splinetool/runtime` or `react-spline` | N/A |
| Webflow (optional) | Native embed integration via Spline component | Webflow account required |

## Pricing Tiers (verified Feb 2026)

| Plan | Price | Key Features |
|------|-------|-------------|
| **Free** | $0 | Unlimited personal files, web exports with Spline watermark |
| **Starter** | $15/mo ($12/yr) | 2 editors, no watermark, video imports, asset library |
| **Professional** | $25/mo ($20/yr) | Unlimited editors, **code & mobile exports**, version history |
| **Team** | $36/seat/mo (yr) | Team folders, extra AI credits |
| **Enterprise** | Custom | SAML SSO, SOC 2, priority support |

**Critical:** Code export (React/Next.js/Vanilla JS Code API) requires **Professional** plan. Free/Starter only get Spline Viewer embeds.

## Core Workflows

### Workflow 1: Scroll-Triggered 3D Animations

**When to use:** Plant growth, character animation, camera pan — anything keyed to page scroll.

**Setup:**
1. In Spline, create **states** for each keyframe (e.g., leaf small, leaf grown)
2. Select your object group → **Add Event** → **Scroll**
3. Configure scroll type:
   - **Steps mode:** Transition between states per mouse wheel tick
   - **Page mode:** Animate based on entire page scroll position
   - **Start From:** top/middle/bottom of viewport (when animation begins)
   - **Start At:** pixel offset on page where animation begins
   - **End After:** total pixels of scroll to complete animation
4. Add **transitions** for each object — define state path (base → state 1 → state 2) and stagger timing for each
5. **Pivot positioning:** Hold Cmd+Opt, click object, drag origin point so scaling/rotation feels natural (e.g., leaf grows from root, not center)
6. Export and embed

**Example:** 400px page scroll animates plant: leaf 1 grows (0-100px), leaf 2 (100-200px), leaf 3 (200-300px), leaf 4 (300-400px) — each with 0.2s stagger for visual flow.

**Gotchas:**
- Pivot point matters. A leaf centered will shrink toward its center; pivoted at the base will grow outward.
- State transitions need explicit timing — copy/paste transitions and tweak each one's delay for stagger effect.
- Preview in **Play Mode** before exporting; scroll behavior only shows in live export, not editor canvas.

### Workflow 2: Webflow Native Integration (No-Code)

**When to use:** You're building in Webflow and want 3D interactivity controlled by Webflow interactions (hover, scroll, element trigger).

**Setup:**
1. Export Spline scene: **Export** → **Code Export** → copy the `prod.spline.design` URL
2. In Webflow, add **Spline component** (embed) and paste URL
3. Set Spline element:
   - `position: sticky` to keep it visible while scrolling past hero sections
   - Place other sections with `margin-top: negative 100vh` to layer over it
4. Create **interactions** in Webflow:
   - **Page Load trigger:** Spline action (e.g., head bobbing rotation on loop)
   - **Scroll In View trigger:** Spline action (e.g., character Y/Z position, full 360° rotation keyed to scroll %)
   - **Hover trigger:** Spline action (e.g., cap rotation on button hover)
5. Each Spline action references **object names from editor** (head, cap, body) — must be named in Spline for this to work

**Example:** Webflow scroll trigger → pull character up 220px Y, push forward 210px Z, spin 6.5° Y — all in visual Webflow interaction builder, no JavaScript.

**Advantage over Code API:** Fully visual interaction binding. No React/JavaScript needed. Webflow designers can wire 3D animations without touching code.

**Gotchas:**
- Webflow interaction Spline actions use **object name matching** — if Spline object is renamed, Webflow loses reference. Use consistent naming.
- Rotation values in Webflow are in degrees, not radians. Negative values rotate CCW.
- Only **Professional Spline plan** exports to Webflow integration. Free tier cannot be embedded this way.

### Workflow 3: Remix Community Assets

**When to use:** You need a 3D element but don't want to model from scratch.

1. Go to **spline.design/community**
2. Browse or search for assets (e.g., "robot", "particle", "plant")
3. Click **Remix** — duplicates into your workspace as an editable copy
4. Modify: hide elements, change materials, adjust scale/position
5. Export (see Workflow 2 / Scroll setup)

**Licensing:** All community files are **CC0 1.0 Universal** (public domain) — no restrictions on use.

### Workflow 4: Programmatic Control with Code API

**When to use:** You need to control the 3D scene from external app code (animate on button click, read/set variables).

**React / Next.js:**
```bash
npm install @splinetool/react-spline @splinetool/runtime
```
```jsx
import Spline from '@splinetool/react-spline';

export default function App() {
  function onLoad(spline) {
    const obj = spline.findObjectByName('Cube');
    obj.position.x += 10;
  }
  return <Spline scene="https://prod.spline.design/xxxxx/scene.splinecode" onLoad={onLoad} />;
}
```

**Next.js SSR with blurred placeholder:**
```jsx
import Spline from '@splinetool/react-spline/next';
// Automatically renders a blurred placeholder server-side while loading
```

**Vanilla JS:**
```javascript
import { Application } from '@splinetool/runtime';
const app = new Application(canvas);
app.load('https://prod.spline.design/xxxxx/scene.splinecode').then(() => {
  const cube = app.findObjectByName('Cube');
  cube.position.x += 10;
});
```

**Available frameworks:** Vanilla JS, React, Next.js, Three.js, react-three-fiber

**Gotchas:**
- Code API requires **Professional plan** ($25/mo).
- Free tier `<spline-viewer>` embed does NOT expose `findObjectByName`, `emitEvent`.
- Must install both `@splinetool/react-spline` AND `@splinetool/runtime`.

### Workflow 5: Export for Web & Preview

1. In Spline, click **Export** → **Code Export**
2. Configure **Play Settings:**
   - **BG Color** → hide for transparent background
   - **Page Scroll** → Yes/No
   - **Orbit/Pan/Zoom** → lock/allow movement
   - **Touch controls** → 1/2/3 finger orbit, pinch zoom
   - **Animated Turntable** → auto-rotation speed/direction
   - **Geometry quality** → compression level
3. Choose export type:
   - **Spline Viewer** (free) — `<spline-viewer>` web component
   - **Code Export** (Pro) — React, Next.js, Vanilla, Three.js, r3f
4. Copy **`prod.spline.design` URL**
5. **Preview directly:** Open URL in browser tab to test before integrating

**Embed format:** `https://prod.spline.design/xxxxx/scene.splinecode` (must be `.splinecode`, not `.spline`)

## Code API Reference

### React Component Props

| Prop | Type | Description |
|------|------|-------------|
| `scene` | `string` | Scene URL (required) |
| `onLoad` | `(spline) => void` | Fires when fully loaded |
| `renderOnDemand` | `boolean` | On-demand rendering (default: `true`) |

### Event Handlers

| Prop | Fires when... |
|------|---------------|
| `onSplineMouseDown`, `onSplineMouseUp`, `onSplineMouseHover` | Mouse interaction |
| `onSplineKeyDown`, `onSplineKeyUp` | Keyboard interaction |
| `onSplineStart`, `onSplineScroll`, `onSplineLookAt`, `onSplineFollow` | Animation/state events |

### Application Methods (from `onLoad`)

| Method | Description |
|--------|-------------|
| `findObjectByName(name)` | Get object by name |
| `emitEvent(eventName, nameOrUuid)` | Trigger animation event |
| `setVariable(name, value)` | Set scene variable |
| `setZoom(zoom)` | Set camera zoom |

## Full Feature Set

**Design:** Parametric objects, booleans, extrusion, pen tool, sculpting, 3D paths, cloner motion, text

**Materials (18+ types):** Color, image, video, gradient, noise, Fresnel, glass, matcap, displacement, bump/roughness

**Animation:** State-based system, **scroll events**, physics, timeline

**Interactions:** 24+ event types (scroll, mouse, keyboard, collision, drag-drop, trigger areas, variable change, API triggers)

**Export targets:** Web (viewer/code), iOS (Swift/SwiftUI), Android (Kotlin), visionOS, GLTF/GLB, USDZ, STL, video

**Integrations:** Figma, Framer, **Webflow** (native component), Notion, Shopify, Wix, Typedream, Tome

**AI Features (paid add-on):** 3D world generation, AI textures, style transfer

## Limitations & Gaps

- **GUI required for creation:** Scenes cannot be built programmatically — only edited in browser. [SINGLE SOURCE — Spline docs don't explicitly forbid headless scene creation, but no API exists for it]
- **CLI-only tasks:** Embedding exports, Code API integration, deploying sites
- **No local-first rendering:** Assets served from prod.spline.design CDN — requires internet
- **Code API gated:** Full programmatic control requires Professional plan. Free tier only gets `<spline-viewer>`
- **Performance:** Large scenes (>5MB) impact mobile. No built-in LOD. [SINGLE SOURCE — inferred from Spline Academy best practices]
- **Webflow interaction scope:** Spline actions in Webflow limited to predefined transforms (position, rotation). Custom event handlers require Code API + React
- **Mobile app export:** Spline exports iOS/Android, but no Expo/React Native integration documented. For cross-platform mobile, use Code API in Expo/React Native separately
- **Self-hosting:** Pro plan only. Docs confirm downloadable code exports can be self-hosted; Spline CDN URLs are not required

## Tips & Best Practices

1. **Scroll animation performance:** Keep scroll animations to <5MB. Preview in real browser before deploying — scrollbar behavior varies across devices
2. **Pivot first:** Set object pivots *before* creating states. Pivot at base/root for growth animations; center for rotations
3. **Staggered timing:** Copy/paste transitions and offset each by 0.1-0.2s for visual flow — lag between objects feels intentional
4. **Webflow workflow:** Build 3D asset in Spline (Pro plan), export URL, drop into Webflow Spline component, bind all interactions in Webflow UI — zero code
5. **Name objects:** All objects must be explicitly named in Spline editor for `findObjectByName` and Webflow integration to work
6. **Next.js SSR:** Use `@splinetool/react-spline/next` for automatic blurred placeholder during load
7. **Mobile fallback:** WebGL not guaranteed on older phones — consider static image fallback
8. **Preview before integrate:** Open `prod.spline.design` URL directly in browser tab to catch issues (background color, missing elements)
9. **Free tier strategy:** Use `