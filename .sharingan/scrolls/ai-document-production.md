---
name: ai-document-production
domain: Workflow/Documents
level: 2-tomoe
description: End-to-end workflow for producing illustrated professional documents — AI-generated corporate illustrations via Nano Banana 2 + HTML/CSS layout + WeasyPrint PDF rendering. Validated on Copilot for M365 reference card (Feb 28, 2026).
sources:
  - type: codebase
    title: "Copilot Reference Card HTML"
    url: "file:///home/ndninja/output/copilot_reference_card.html"
    date: "2026-02-28"
    confidence: high
  - type: codebase
    title: "NB2 batch generation script"
    url: "file:///tmp/nb2_batch.py"
    date: "2026-02-28"
    confidence: high
    notes: "Ephemeral script — pattern is what matters, not the file"
  - type: related-scroll
    title: "Nano Banana Pro (NB2 image generation)"
    url: "file:///home/ndninja/.sharingan/scrolls/nano-banana-pro.md"
    date: "2026-02-28"
    confidence: high
last_updated: 2026-02-28
sources_count: 3
can_do_from_cli: true
---

# AI Document Production — Illustrated Professional Documents

## Mental Model

Turn written content (Markdown, outlines, specs) into polished illustrated documents by combining:

1. **AI image generation** (NB2) for consistent visual aids
2. **HTML/CSS** for precise layout control
3. **WeasyPrint** for PDF rendering from the same HTML source

This gives you both a responsive HTML version and a print-ready PDF from one source. The images are generated with JSON structured prompting to ensure visual consistency across the full set.

---

## The Workflow

```
Markdown/outline → Plan illustrations → Generate with NB2 → Build HTML → Render PDF
```

### Step 1: Content Analysis
- Read the source document and identify natural section breaks
- Plan one illustration per section (6-8 images typical)
- Define the visual concept for each (metaphor, diagram, icon set)

### Step 2: Lock a Visual Style Template
Create a JSON prompt template that locks style, lighting, and color palette across all images:

```json
{
    "prompt": "[VARIES PER IMAGE]",
    "negative_prompt": "photorealistic, dark, cluttered, childish, watermark, neon, text, labels",
    "style": "Modern flat-design corporate illustration. Clean vectors, subtle gradients, professional.",
    "composition": {
        "layout": "[VARIES — grid, flow, centered]",
        "framing": "[VARIES — wide, medium, close-up]",
        "focus": "Sharp throughout, no blur"
    },
    "lighting": {
        "type": "Soft ambient, flat design lighting",
        "color_temperature": "[LOCKED — e.g., cool blues/teals]"
    },
    "color_grading": "[LOCKED — e.g., teal #0891B2, blue #3B82F6, gray #6B7280, white bg]"
}
```

**Key insight:** Only change `prompt`, `composition.layout`, and `composition.framing` per image. Keep `style`, `lighting`, `color_grading`, and `negative_prompt` identical across all generations. This is what produces a cohesive visual set.

### Step 3: Generate Images with NB2

```python
from google import genai
from google.genai import types
import json

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",  # NB2
    contents=json.dumps(prompt_dict),
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",  # Landscape for documents
            image_size="2K",       # 2K for final, 0.5K for drafts
        ),
    ),
)
```

**Parallel generation:** Images are independent — generate all in parallel (separate python processes or async). 5-6 images takes ~10-15 seconds total.

**Cost:** ~$0.04-0.07 per image at 1K-2K. A full document with 6-8 images costs under $1.

### Step 4: Build the HTML Document

Structure:
```html
<div class="header">Title + subtitle</div>
<section class="bg-[color]">
  <div class="section-header">Number badge + title</div>
  <div class="section-body">
    <img src="illustration.png" class="illustration">
    <p>Content text</p>
    <div class="example-card">Prompt examples</div>
    <div class="callout">Tips/notes</div>
  </div>
</section>
```

**Design patterns that work:**
- Color-coded sections (teal, blue, green, amber, purple) with matching header backgrounds
- Numbered circle badges for section headers
- Example cards with left colored borders in 2-column grids
- Callout boxes with colored backgrounds for tips/warnings
- Illustrations at 160-175px max-height with `object-fit: contain`

### Step 5: Render PDF with WeasyPrint

```python
import weasyprint

html = weasyprint.HTML(filename='document.html', base_url='.')
doc = html.render()
print(f'Page count: {len(doc.pages)}')
doc.write_pdf('output.pdf')
```

**`base_url='.'` is critical** — tells WeasyPrint to resolve image paths relative to the HTML file location.

---

## Page Fitting Tips

Getting content to fit exactly N pages (no orphaned footer or trailing paragraph) requires iterative tightening:

| What to reduce | Default | Tight | Impact |
|----------------|---------|-------|--------|
| `@page margin` | 0.6in | 0.5in | ~1 line per page |
| Section `margin-bottom` | 2rem | 1.25rem | ~0.5 line per section |
| Section body `padding` | 1.5rem | 1.25rem | Small savings |
| Illustration `max-height` | 220px | 160px | ~2 lines per image |
| Callout `padding` | 1.25rem | 1rem | ~0.5 line per callout |
| Footer `margin-top` + `padding` | 2rem + 1.5rem | 0.5rem + 0.5rem | ~2 lines |

**Workflow:** Render → check page count via `len(doc.pages)` → tighten → re-render. WeasyPrint renders in under 2 seconds so iteration is fast.

**`page-break-inside: avoid`** on sections prevents mid-section breaks (good for print readability).

---

## Aspect Ratios for Different Document Types

| Document | Image aspect | Notes |
|----------|-------------|-------|
| Reference card / handout | 16:9 | Wide illustrations work in portrait letter layout |
| Presentation / slides | 16:9 | Matches slide dimensions |
| Social media post | 1:1 or 4:5 | Square or tall |
| Tall infographic | 9:16 | Single-column vertical |
| Banner / header | 21:9 | Ultra-wide strip |

---

## Style Presets

### Corporate / Training Material
```json
"style": "Modern flat-design corporate illustration. Clean vectors, subtle gradients.",
"color_grading": "teal (#0891B2), blue (#3B82F6), gray (#6B7280), white background",
"negative_prompt": "photorealistic, dark, cluttered, childish, watermark, neon, text, labels"
```

### Technical Documentation
```json
"style": "Clean technical diagram style. Precise, labeled, minimal color.",
"color_grading": "Monochrome blue with accent orange for highlights",
"negative_prompt": "artistic, painterly, decorative, watermark"
```

### Creative / Marketing
```json
"style": "Vibrant illustrated marketing style. Bold colors, friendly characters.",
"color_grading": "Bright brand colors, gradients allowed, white or colored backgrounds",
"negative_prompt": "corporate, boring, stock photo, watermark"
```

---

## What NB2 Handles Well for Documents

- **Flat-design icons and illustrations** — consistent corporate style
- **Conceptual metaphors** — robot assistant, transformation flows, data connections
- **Multi-quadrant layouts** — 2x2 grids with distinct icons per quadrant
- **Circular flow diagrams** — iteration cycles, process loops
- **Character with accessories** — showing roles/modes via floating objects

## What to Avoid

- **Don't ask NB2 to render text inside images** for documents — put text in HTML instead. NB2 *can* do text, but HTML text is sharper, searchable, and editable.
- **Don't use NB2 for precise data infographics** — charts, org charts, and labeled diagrams have occasional spatial accuracy issues. Use HTML/CSS or a charting library instead.
- **Don't generate at 4K** unless printing large format — 2K is plenty for letter-size PDF.

---

## Deliverable Checklist

- [ ] Source Markdown/outline reviewed
- [ ] JSON style template locked (style, lighting, colors, negative_prompt)
- [ ] All illustrations generated and visually inspected
- [ ] HTML document built with all sections, cards, callouts
- [ ] PDF rendered and page count verified (no orphaned content)
- [ ] Both HTML + PDF delivered (HTML for screen, PDF for print/email)

---

## First Project: Copilot for M365 Reference Card (Feb 28, 2026)

- **Source:** `Beginners_Reference_Card.md` (written by Gemini)
- **Output:** 6-page PDF + responsive HTML
- **Images:** 6 NB2 illustrations at 2K, corporate flat-design
- **Style:** Teal/blue corporate palette, Segoe UI typography
- **Total image cost:** ~$0.45
- **Time:** ~20 minutes end-to-end (including style iteration)
- **Files:** `output/copilot_reference_card.html`, `output/Copilot_Reference_Card.pdf`
