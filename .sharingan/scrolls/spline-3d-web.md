---
name: spline-3d-web
domain: 3D/Web
level: 2-tomoe
description: Browser-based 3D design tool for creating interactive web elements. Embed 3D scenes directly in websites with mouse-reactive animations. Full Code API for programmatic control.
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
  - type: web
    title: "Spline Pricing Page"
    url: "https://spline.design/pricing"
    date: "2026-02"
    confidence: high
last_updated: 2026-02-17
can_do_from_cli: partial
---

# Spline — 3D Design for the Web

## Mental Model

Spline is a browser-based 3D design tool — think Figma but for 3D. You create or remix interactive 3D scenes and export them as embeddable web components. Assets respond to mouse movement, clicks, scroll, and keyboard — making websites feel premium.

**Key differentiator:** Everything runs in the browser. No Unity, no Blender. Design, animate, add physics/interactions, and export to web/iOS/Android from one tool.

**Code API vs Real-time API:** The *Code API* (`@splinetool/runtime`) lets external code control scenes programmatically. The *Real-time API* is for connections created inside the Spline editor (webhooks, external data). They're separate systems.

## Prerequisites

| Requirement | Details | Free Tier? |
|---|---|---|
| Spline account | Sign up at [spline.design](https://spline.design) | Yes — unlimited personal files, watermarked exports |
| Modern browser | Chrome/Edge recommended (WebGL required) | Yes |
| Node.js (for dev) | Required for `@splinetool/runtime` or `react-spline` | N/A |
| AntiGravity (optional) | AI website builder at antigravity.ai | Free tier available |

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

### Workflow 1: Find and Remix a Community 3D Asset

**When to use:** You need a 3D element but don't want to model from scratch.

1. Go to **spline.design/community**
2. Browse or search for assets (e.g., "robot", "particle", "abstract")
3. Preview the asset — check if it has the interactivity you want
4. Click **Remix** — duplicates it into your workspace as an editable copy
5. Modify as needed — hide elements, change materials/colors
6. Export (see Workflow 2)

**Gotchas:**
- Free plan: unlimited personal files but exports have watermark.
- Some assets have logos or text baked in — hide unwanted layers in the editor.
- Complex assets have deep node trees — toggle visibility rather than restructuring.

### Workflow 2: Export for Web Embedding

**When to use:** Your Spline scene is ready to put on a website.

1. In Spline editor, click **Export** (top right)
2. Go to **Code Export** section
3. Configure **Play Settings**:
   - **Hide background color** if integrating over a dark/custom background
   - Adjust animation/interaction settings
4. Choose export type:
   - **Spline Viewer** (free) — `<spline-viewer>` web component
   - **Code Export** (Pro plan) — React/Vanilla JS with full Code API access
5. Click **Update Code Export**
6. Copy the `prod.spline.design` URL

**Embed URL format:** `https://prod.spline.design/xxxxx/scene.splinecode`

**Important:** Only `.splinecode` files work with the runtime/viewer. `.spline` files are editor-only.

**Gotchas:**
- If integrating into a dark site, ALWAYS hide the background color in play settings first.
- The embed URL starts with `prod.spline.design` — this is what you paste into code.
- Preview before integrating: paste the URL into [fetch.sub](https://fetch.sub) to check the exported asset.

### Workflow 3: Programmatic Control with Code API

**When to use:** You need to control the 3D scene from your app code (animate on button click, read/set variables, respond to object interactions).

**Vanilla JS:**
```html
<canvas id="canvas3d"></canvas>
<script type="module">
import { Application } from '@splinetool/runtime';

const canvas = document.getElementById('canvas3d');
const app = new Application(canvas);
app.load('https://prod.spline.design/xxxxx/scene.splinecode')
  .then(() => {
    const cube = app.findObjectByName('Cube');
    cube.position.x += 10;
  });
</script>
```

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

**Gotchas:**
- Code API requires **Professional plan** ($25/mo).
- Spline Viewer embed (free) does NOT expose the Code API — no `findObjectByName`, no `emitEvent`.
- Always install both `@splinetool/react-spline` AND `@splinetool/runtime`.

### Workflow 4: Integrate with AI Website Builder (AntiGravity)

**When to use:** You want an AI agent to build a full website around your 3D scene.

1. Create a website scaffold in AntiGravity by describing what you want
2. Optionally provide design inspiration from [godly.website](https://godly.website) or [landbook.com](https://landbook.com)
3. Paste your Spline embed URL and ask the agent to integrate it
4. Iterate — adjust colors, layout, copy via natural language

**Gotchas:**
- Give the AI a brand guidelines document for consistent output.
- [SINGLE SOURCE] This workflow was demonstrated with AntiGravity specifically; adaptable to Claude Code, Cursor, or other AI coding tools.

### Workflow 5: Deploy to Production

1. **Static sites:** Netlify (free, drag-and-drop or CLI deploy) → `*.netlify.app`
2. **Next.js/React:** Vercel (free tier, `vercel deploy`)
3. **Custom domain:** DNS settings per platform

## Code API Reference

### React Component Props

| Prop | Type | Description |
|------|------|-------------|
| `scene` | `string` | Scene URL (required) — must be `.splinecode` |
| `onLoad` | `(spline) => void` | Fires when scene is fully loaded |
| `renderOnDemand` | `boolean` | On-demand rendering (default: `true`) |
| `className` | `string` | CSS classes for container |
| `style` | `object` | Inline styles for container |

### Event Handler Props

| Prop | Fires when... |
|------|---------------|
| `onSplineMouseDown` | Mouse button pressed on object |
| `onSplineMouseUp` | Mouse button released on object |
| `onSplineMouseHover` | Mouse enters object |
| `onSplineKeyDown` | Key pressed while scene focused |
| `onSplineKeyUp` | Key released while scene focused |
| `onSplineStart` | Start event triggers |
| `onSplineScroll` | Scroll event on scene |
| `onSplineLookAt` | Look-at event triggers |
| `onSplineFollow` | Follow event triggers |

Event callback receives `(e)` where `e.target.name` is the object name.

### Application Methods (from `onLoad` callback)

| Method | Description |
|--------|-------------|
| `findObjectByName(name)` | Get scene object by name |
| `findObjectById(uuid)` | Get scene object by UUID |
| `emitEvent(eventName, nameOrUuid)` | Trigger an animation event |
| `emitEventReverse(eventName, nameOrUuid)` | Trigger event in reverse |
| `setZoom(zoom)` | Set initial camera zoom |
| `setVariable(name, value)` | Set a single scene variable |
| `setVariables(obj)` | Set multiple scene variables |

### Emittable Event Types

`mouseDown`, `mouseHover`, `mouseUp`, `keyDown`, `keyUp`, `start`, `lookAt`, `follow`

### Lazy Loading Pattern
```jsx
const Spline = React.lazy(() => import('@splinetool/react-spline'));

<Suspense fallback={<div>Loading 3D scene...</div>}>
  <Spline scene="https://prod.spline.design/xxxxx/scene.splinecode" />
</Suspense>
```

## Full Feature Set (from official docs)

**Design:** Parametric objects, booleans, extrusion, pen tool, shape blending, 3D sculpting, 3D paths, cloner motion, text

**Materials (18+ layer types):** Color, image, video, gradient, noise, Fresnel, rainbow, toon, outline, glass, matcap, displacement, pattern, depth/3D gradient, plus bump/roughness mapping

**Lighting:** Directional, point, spot lights + soft shadows

**Camera:** Post-processing effects, depth of field, fog

**Animation:** State-based system, timeline, animatable properties, physics

**Interactions:** 24+ event types (mouse, keyboard, scroll, collision, drag-drop, trigger areas, variable change, API triggers) and 16+ action types (sound, transitions, video, links, scene reset, camera switching, conditionals, object create/destroy)

**AI Features (paid add-on):** AI 3D world generation ("Spell"), AI textures, AI style transfer

**Export targets:** Web (viewer/code), iOS (Swift/SwiftUI), Android (Kotlin/APK/AAB), visionOS, GLTF/GLB, USDZ, STL, image, video

**Integrations:** Figma, Framer, Webflow, Notion, Shopify, Wix, Wix Studio, Typedream, Tome, Toddle

## Integration with Ninja Toolkit

- **Prompt Toolkit (Next.js):** Add interactive 3D hero section using `@splinetool/react-spline/next` for SSR placeholder
- **Glitch avatar:** Spline could generate 3D web components for a browser-based companion
- **Content pipeline:** 3D thumbnails or interactive demo pages for YouTube video topics

## Limitations & Gaps

- **GUI required for creation:** Building/editing 3D scenes requires the Spline browser editor. Cannot be done from CLI.
- **CLI-possible tasks:** Embedding exported scenes, Code API integration, deploying sites with embeds
- **No local rendering:** Assets served from prod.spline.design CDN — requires internet
- **Code API gated:** Full programmatic control requires Professional plan ($25/mo). Free tier only gets `<spline-viewer>` embeds.
- **Performance:** Large scenes (>5MB) hurt mobile load times. No built-in LOD/progressive loading.
- **No local .splinecode hosting:** Files must be hosted on Spline's CDN (or self-hosted with workarounds)
- **Hana Canvas:** 2D design feature (infinite canvas, vectors, auto-layout) — not deeply explored yet

## Related Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Spline Community | spline.design/community | Browse/remix 3D assets |
| Spline Docs | docs.spline.design | Official documentation |
| Spline Academy | academy.spline.design | Video tutorials |
| react-spline GitHub | github.com/splinetool/react-spline | React/Next.js package |
| @splinetool/runtime | npmjs.com/package/@splinetool/runtime | Vanilla JS runtime |
| @splinetool/viewer | npmjs.com/package/@splinetool/viewer | Web component viewer |
| Design Inspiration | godly.website | Landing page designs |
| Design Inspiration | landbook.com | Searchable by niche |
| Component Library | 21st.dev | UI components with AI-ready prompts |

## Tips & Best Practices

1. **Performance first:** Keep scenes under 3MB. Fewer polygons = faster load. Use lazy loading for below-fold scenes.
2. **Hide backgrounds:** When embedding over custom backgrounds, always toggle off Spline background in play settings.
3. **Next.js SSR:** Use `@splinetool/react-spline/next` import for automatic blurred placeholder during load.
4. **Mobile fallback:** Consider a static image fallback for devices that can't handle WebGL.
5. **Event naming:** Objects in Spline must be named (not "Object 1") for `findObjectByName` to be useful.
6. **Brand consistency:** Feed your AI agent a brand guidelines markdown for consistent colors/typography around 3D embeds.
7. **Free tier strategy:** Use `<spline-viewer>` web component for display-only scenes. Only upgrade to Pro when you need Code API (programmatic control).
