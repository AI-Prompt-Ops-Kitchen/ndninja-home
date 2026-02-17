---
name: spline-3d-web
domain: 3D/Web
level: 1-tomoe
description: Browser-based 3D design tool for creating interactive web elements. Embed 3D scenes directly in websites with mouse-reactive animations.
sources:
  - type: youtube
    title: "AntiGravity + Spline Builds Insane 3D Websites (NEW Skill)"
    url: "https://www.youtube.com/watch?v=csOEsfiBfvo"
    channel: "RoboNuggets"
    date: "2026-02"
    confidence: medium
last_updated: 2026-02-17
can_do_from_cli: partial
---

# Spline — 3D Design for the Web

## Mental Model

Spline is a browser-based 3D design tool — think Figma/Canva but for 3D assets. You create or remix interactive 3D scenes and export them as embeddable web components (iframes, JS snippets, or React components). The assets are interactive — they respond to mouse movement, clicks, and scroll, making websites feel premium.

**Key differentiator:** Everything runs in the browser. No Unity, no Blender installs. Design, animate, and export to web from one tool.

## Prerequisites

| Requirement | Details | Free Tier? |
|---|---|---|
| Spline account | Sign up at [spline.design](https://spline.design) | Yes — 3 remixed assets at a time |
| Modern browser | Chrome/Edge recommended (WebGL required) | Yes |
| AntiGravity (optional) | AI website builder at antigravity.ai | Free tier available |

## Core Workflows

### Workflow 1: Find and Remix a Community 3D Asset

**When to use:** You need a 3D element but don't want to model from scratch.

1. Go to **spline.design/community**
2. Browse or search for assets (e.g., "robot", "particle", "abstract")
3. Preview the asset — check if it has the interactivity you want (mouse follow, hover effects, etc.)
4. Click **Remix** — duplicates it into your workspace as an editable copy
5. Modify as needed — hide elements by clicking them and toggling visibility, change materials/colors
6. Export (see Workflow 2)

**Gotchas:**
- Free plan allows 3 remixed assets simultaneously. Archive old ones to free up slots.
- Some assets have logos or text baked in — hide unwanted layers in the editor.
- Complex assets have deep node trees — focus on toggling visibility rather than restructuring.

### Workflow 2: Export for Web Embedding

**When to use:** Your Spline scene is ready to put on a website.

1. In Spline editor, click **Export** (top right area)
2. Go to **Code Export** section
3. Configure **Play Settings**:
   - **Hide background color** if integrating over a dark/custom background (critical for dark sites)
   - Adjust any animation/interaction settings as needed
4. Choose the right **framework** at the top:
   - **Vanilla JS** — for plain HTML/JS sites (most common)
   - **React** — for React/Next.js projects
   - Other frameworks available
5. Click **Update Code Export**
6. Copy the **prod.spline.design URL** — this is your embed URL

**Embed URL format:** `https://prod.spline.design/xxxxx/scene.splinecode`

**Gotchas:**
- The embed URL starts with `prod.spline.design` — this is the key piece to give to your AI agent or paste into code.
- If integrating into a dark site, ALWAYS hide the background color in play settings first.
- If unsure which framework, take a screenshot of the options and ask your AI agent which matches your build.

**Preview before integrating:** Paste the `prod.spline` URL into [fetch.sub](https://fetch.sub) to preview the exported asset in isolation.

### Workflow 3: Integrate into a Website with AI (AntiGravity)

**When to use:** You want an AI agent to build a website around your 3D scene.

1. Create a website scaffold in AntiGravity by describing what you want
2. Optionally provide **design inspiration** from:
   - [godly.website](https://godly.website) — infinite canvas of landing page designs
   - [landbook.com](https://landbook.com) — searchable by niche, shows color palettes
3. Have AntiGravity generate the base site with a placeholder 3D element
4. Install the **Spline skill** (a skill.md file that gives the AI agent Spline context)
5. Provide the Spline embed URL and ask the agent to integrate it
6. Iterate — adjust colors, layout, copy via natural language prompts

**Gotchas:**
- Give AntiGravity a **brand guidelines document** (colors, typography) for consistent output.
- The AI may place the 3D element as a background — specify if you want it positioned differently.
- [SINGLE SOURCE] This workflow was demonstrated with AntiGravity specifically; adaptable to Claude Code, Cursor, or Codex with the same Spline skill.md.

### Workflow 4: Deploy to Production

**When to use:** Website is ready to go live.

1. For simple static sites: **Netlify** (free, drag-and-drop deploy)
   - Ask your AI agent to deploy via Netlify CLI
   - Results in a `*.netlify.app` URL
2. For complex builds: **Vercel** or **GitHub Pages**
3. Custom domain: Connect via DNS settings (guides available per platform)

## Command Reference (for AI Agent Integration)

| Action | How | Notes |
|--------|-----|-------|
| Get Spline skill.md | Download from creator's description link | Gives AI agent full Spline context |
| Embed 3D scene | `<script type="module" src="https://unpkg.com/@splinetool/viewer/build/spline-viewer.js"></script><spline-viewer url="PROD_URL"></spline-viewer>` | Vanilla JS method |
| React integration | `npm install @splinetool/react-spline` then `<Spline scene="PROD_URL" />` | For Next.js/React projects |
| Preview export | Paste prod.spline URL into fetch.sub | Quick visual check |

## Integration with Ninja Toolkit

- **Glitch avatar:** Spline could generate 3D web components for a future browser-based Glitch companion
- **Content pipeline:** 3D thumbnails or interactive demo pages for YouTube video topics
- **Prompt Toolkit:** Interactive 3D landing page instead of flat design

## Limitations & Gaps

- **GUI required for creation:** Building/editing 3D scenes requires the Spline browser editor. Cannot be done from CLI.
- **CLI-possible tasks:** Embedding exported scenes (copy URL, write HTML/React code), deploying sites with Spline embeds
- **No local rendering:** Spline assets require internet connection to load (served from prod.spline.design CDN)
- **Performance:** 3D scenes add significant page weight. Large scenes (>5MB) hurt mobile load times.
- **Free tier limits:** 3 concurrent remixed assets. Archive to free slots.
- [UNVERIFIED] Exact export format options may vary by Spline plan tier.

## Related Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Spline Community | spline.design/community | Browse/remix 3D assets |
| Spline Docs | docs.spline.design | Official documentation |
| Design Inspiration | godly.website | Landing page designs |
| Design Inspiration | landbook.com | Searchable by niche |
| Component Library | 21st.dev | UI components with AI-ready prompts |
| Asset Preview | fetch.sub | Preview exported Spline scenes |

## Tips & Best Practices

1. **Performance first:** Keep 3D scenes lean. Fewer polygons = faster load. Aim for <3MB.
2. **Hide backgrounds:** When embedding over custom backgrounds, always toggle off the Spline background color in play settings.
3. **Brand consistency:** Generate a brand guidelines markdown file from an existing design and feed it to your AI agent for consistent colors/typography.
4. **Mobile testing:** 3D scenes are heavy on phones. Always test mobile view after integration.
5. **Skill files:** The Spline skill.md pattern (giving AI agents tool context) is reusable — create similar files for any tool you want AI agents to use.
