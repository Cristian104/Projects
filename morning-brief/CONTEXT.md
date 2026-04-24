# Morning Brief — Design & Architecture Context

Read this before making ANY UI changes to this project.

## Stack

- **Framework**: Flask + Jinja2 templates (NOT Next.js, NOT React)
- **Serving**: Gunicorn, port 8009
- **DB**: SQLite (`news.db`, gitignored)
- **AI**: Gemini Flash for briefing/enrichment
- **Live URL**: news.mybrain.world

Templates: `templates/base.html`, `templates/index.html`, `templates/article.html`
Styles: inline `<style>` blocks inside each template (no separate CSS files)

---

## Design System — Apple/macOS Dark Aesthetic

The UI is intentionally modelled after Apple News, The Verge, and macOS system UI.
**Do NOT replace this with generic Tailwind or Bootstrap patterns.**

### Color Tokens

```css
/* Dark mode (default) */
--bg:          #000000;
--surface:     #0f0f0f;
--surface-2:   #1a1a1a;
--surface-3:   #252525;
--border:      rgba(255,255,255,0.08);
--border-h:    rgba(255,255,255,0.16);   /* hover state */
--text:        #f5f5f7;
--text-2:      #a1a1a6;
--text-3:      #6e6e73;
--red:         #ff375f;   /* primary accent — CTAs, section markers, category: world */
--blue:        #0a84ff;   /* secondary accent — category: tech */
--orange:      #ff9f0a;   /* importance indicator */
--green:       #30d158;   /* live/online indicator */

/* Light mode */
--bg:          #f5f5f7;
--surface:     #ffffff;
--red:         #d70015;
--blue:        #0071e3;
```

### Typography

- **Font**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif`
- **Load**: Inter via Google Fonts (300–700 weights, italic)
- **Anti-aliasing**: `-webkit-font-smoothing: antialiased` on body
- Headlines: `font-weight: 700`, `letter-spacing: -0.028em` to `-0.03em`
- Labels/badges: `text-transform: uppercase`, `letter-spacing: 0.1em+`
- Body copy: `line-height: 1.7–1.82`

### Key Patterns

**Header**: sticky, `backdrop-filter: blur(24px) saturate(180%)`, 56px tall
**Cards**: `border-radius: 13px`, subtle border, lift on hover (`translateY(-3px)`)
**Hero**: full-bleed image with gradient overlay (`rgba(0,0,0,0.94)` at bottom), 540px tall
**Section labels**: red left-border accent (`width:3px; background:var(--red)`)
**Animations**: scroll-reveal with `IntersectionObserver`, `cubic-bezier(0.16,1,0.3,1)` easing
**Badges**: pill shape (`border-radius: 20px`) for nav, rect (`border-radius: 3-4px`) for category tags
**Scrollbar**: 4px wide, transparent track, `var(--surface-3)` thumb

### Component Reference

| Component | File | Class |
|-----------|------|-------|
| Sticky header + nav | `base.html` | `.header`, `.header-inner` |
| Theme toggle (dark/light) | `base.html` | `.theme-toggle` |
| Hero card (full-bleed) | `index.html` | `.hero` |
| Featured 2-col row | `index.html` | `.featured-row`, `.featured-card` |
| 3-col article grid | `index.html` | `.grid`, `.card` |
| Source-keyed gradients | `index.html` | `.card[data-source="..."]` |
| Reading progress bar | `article.html` | `#readProgress` |
| Drop-cap first letter | `article.html` | `.article-body p:first-of-type::first-letter` |
| Related articles grid | `article.html` | `.related-section`, `.related-card` |

---

## How to Design UI Changes — Use These Tools

**ALWAYS use this workflow for any visual redesign or new page/component:**

### Step 1 — Google Stitch (MCP) — Design mockup first

Stitch MCP is configured. Use it BEFORE writing any HTML/CSS.

```
MCP tools: mcp__stitch-mcp__*
API key:   AQ.Ab8RN6LYoDCs8wnJrFurqZLNn4AftEVIFYHc1tEp9nExGHiU6A
```

**Workflow:**
```
1. mcp__stitch-mcp__list_projects          → find or confirm project
2. mcp__stitch-mcp__generate_screen_from_text → generate desktop + mobile designs
3. mcp__stitch-mcp__get_screen             → retrieve HTML as design reference
4. mcp__stitch-mcp__edit_screens           → iterate/refine
```

Parameters:
- `deviceType`: "DESKTOP" + "MOBILE" (always generate both)
- `modelId`: "GEMINI_3_PRO" for best quality

Extract from Stitch HTML: color tokens, spacing rhythm, component patterns.
Then re-implement in Flask/Jinja2 (inline CSS in templates) — do NOT copy Stitch HTML directly.

### Step 2 — Nano Banana (Imagen 4) — Generate images

For hero images, OG images, article thumbnails, placeholders:

```python
import google.genai as genai
from google.genai import types
import os

# Read key from ~/stacks/.env → GEMINI_API_KEY
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_images(
    model="imagen-4.0-generate-001",   # NOT imagen-3, NOT imagen-4-ultra
    prompt="<detailed prompt>",
    config=types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="16:9",           # heroes, OG
        # aspect_ratio="1:1",          # thumbnails
        output_mime_type="image/png",
    )
)
img_bytes = response.generated_images[0].image.image_bytes
with open("morning-brief/static/images/filename.png", "wb") as f:
    f.write(img_bytes)
```

Install if needed: `pip3 install google-genai --break-system-packages`
Read key: `grep GEMINI_API_KEY ~/stacks/.env`

Save images to: `morning-brief/static/images/`
Reference in templates as: `/static/images/filename.png`

**Daily Imagen 4 limit: 10 calls/day** (`DAILY_IMAGEN_LIMIT` in `enricher.py`).
When limit is hit, enricher falls back to category defaults:
- `static/images/default-tech.png` — dark navy, circuit board aesthetic
- `static/images/default-world.png` — dark crimson, globe/geopolitical aesthetic
- `static/images/default-entertainment.png` — dark purple, stage lighting aesthetic

### Step 3 — UI UX Pro Max / interface-design

For design system guidance invoke: `/ui-ux-pro-max` or `/interface-design:init`
This project is an **app/dashboard** — use `interface-design` not `ui-ux-pro-max` (marketing sites).

---

## Responsive Breakpoints

```css
@media (max-width: 960px) { /* 2-col grid */ }
@media (max-width: 860px) { /* featured row → 1-col */ }
@media (max-width: 768px) { /* hide header stats/time */ }
@media (max-width: 600px) { /* 1-col grid, smaller hero */ }
@media (max-width: 480px) { /* hide logo label */ }
```

---

## What NOT to Do

- Don't switch to Tailwind or Bootstrap — all styles are inline in templates
- Don't add external CSS files — keep styles in `<style>` blocks in each template
- Don't use React/Vue components — this is plain Flask/Jinja2
- Don't skip Stitch mockup — always design before coding
- Don't use generic stock imagery — use Nano Banana (Imagen 4) for all images
- Don't change the Apple/dark aesthetic without a Stitch design to guide it
