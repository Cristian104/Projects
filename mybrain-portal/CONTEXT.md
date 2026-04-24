# MyBrain Portal — Context

## Design System

### Color Tokens (CSS Variables in base.html :root)
| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#0F172A` | Page background |
| `--surface` | `#1E293B` | Cards, panels, sidebar |
| `--surface-input` | `#0F172A` | Form inputs |
| `--accent` | `#22C55E` | Primary green CTA, active nav, icons |
| `--accent-dim` | `rgba(34,197,94,0.1)` | Accent background fills |
| `--accent-border` | `rgba(34,197,94,0.25)` | Accent-tinted borders |
| `--text-primary` | `#F1F5F9` | Main body text |
| `--text-secondary` | `#CBD5E1` | Secondary / label text |
| `--text-muted` | `#94A3B8` | Hints, placeholders, timestamps |
| `--danger` | `#EF4444` | Delete actions, error states |
| `--warning` | `#F59E0B` | Warnings, caution badges |
| `--border-subtle` | `rgba(255,255,255,0.07)` | Panel card borders |
| `--border-medium` | `rgba(255,255,255,0.12)` | Dividers, active borders |

### Border Radius Tokens
| Token | Value |
|-------|-------|
| `--r-sm` | `6px` |
| `--r-md` | `10px` |
| `--r-lg` | `14px` |
| `--r-xl` | `18px` |

### Typography
- **UI Body:** Space Grotesk (Google Fonts) — all body/label text
- **Headings:** Archivo (Google Fonts) — font-weight 800–900 for page titles
- **Page header pattern:** `font-family: Archivo; font-size: 1.7rem; font-weight: 900` with a colored FA icon in a rounded box

### Icons
- **Library:** Font Awesome 6 (loaded in base.html)
- **Solid:** `fas fa-*` — most icons
- **Brand:** `fab fa-*` — Docker, GitHub, etc. (must use `fab`, not `fas`)
- **Regular:** `far fa-*` — outline variants

---

## Architecture

- **Stack:** Flask/Python + Jinja2 templates + Font Awesome 6 + Tailwind CSS CDN + ApexCharts
- **Template inheritance:** `base.html` → page templates via `{% block content %}`
- **Static files:** `app/static/` (global/css, global/img, dashboard/js, auth/)
- **Database:** PostgreSQL (`remastered_core`), SQLite fallback for local dev
- **Deploy:** git push → GitHub Actions → VPS Docker rebuild
- **Pre-start hook:** `update_db.py` runs before gunicorn (creates tables + migrations)

---

## Key Files

```
services/mybrain-portal/
  app/
    templates/
      base.html                    ← sidebar, nav, design tokens (:root vars), mobile CSS
      main/dashboard.html          ← bento grid, stats, tasks, apps, charts
      main/dev_panel.html          ← developer tools, user management
      auth/login.html              ← split-screen, animated bg rings, quote carousel
      gym/index.html               ← gym hero banner
      gym/programs.html            ← program manager list
      nutrition/today.html         ← nutrition hero banner
      nutrition/programs.html      ← nutrition program manager
      apps/index.html              ← app launcher grid
    static/
      global/img/mybrain-logo.png      ← sidebar logo + login brand mark
      global/img/favicon-192.png       ← favicon (all pages)
      global/img/gym-banner.png        ← gym page hero
      global/img/nutrition-banner.png  ← nutrition page hero
      dashboard/js/dashboard.js        ← ApexCharts, task CRUD, animations
      auth/js/login.js                 ← quote carousel
      auth/js/fluid.js                 ← Three.js fluid animation (login left pane)
  update_db.py                     ← runs before gunicorn, creates tables + migrations
```

---

## UI Component Patterns

### Panel Card
```html
<div class="panel-card">
  <!-- bg: var(--surface), border: 1px solid var(--border-subtle), border-radius: var(--r-lg), padding: 20px -->
</div>
```

### Stat Cards
```html
<div class="stat-card-new">
  <div class="icon-wrap">...</div>
  <div class="progress-track">...</div>
</div>
```

### Buttons
| Class | Purpose |
|-------|---------|
| `.btn-save` | Green CTA (primary action) |
| `.btn-sm` | Ghost/secondary small button |
| `.btn-cancel` | Cancel / dismiss |

### Badges
```html
<span class="badge-mini badge-work">work</span>
<span class="badge-mini badge-personal">personal</span>
<span class="badge-mini badge-dev">dev</span>
<span class="badge-mini badge-health">health</span>
```

### Modals
```html
<div class="modal-overlay" id="myModal">
  <div class="modal-box">...</div>
</div>
<!-- Open with: document.getElementById('myModal').classList.add('active') -->
<!-- base CSS: .modal-overlay.active { display: flex; } -->
```

Also valid: `modal-card` variant for card-style modals.

### Sidebar Nav
```html
<nav class="nav-links">
  <a href="/page" class="nav-item {% if active %}active{% endif %}">
    <i class="fas fa-icon"></i>
    <span>Label</span>
  </a>
</nav>
```
- Collapses to 60px (icon-only) at 768px breakpoint
- Active state handled by `.nav-item.active` class
- New nav items need `uhm()` permission check in base.html

### Page Header Pattern
```html
<div style="display:flex; align-items:center; gap:12px; margin-bottom:24px;">
  <div style="background:var(--accent-dim); border:1px solid var(--accent-border);
              border-radius:var(--r-md); padding:10px 12px;">
    <i class="fas fa-icon" style="color:var(--accent); font-size:1.3rem;"></i>
  </div>
  <div>
    <h1 style="font-family:Archivo; font-size:1.7rem; font-weight:900;
               color:var(--text-primary); margin:0;">Page Title</h1>
    <p style="color:var(--text-muted); font-size:0.85rem; margin:0;">Subtitle</p>
  </div>
</div>
```

### Empty States
```html
<div style="text-align:center; padding:40px; border:2px dashed var(--border-subtle);
            border-radius:var(--r-lg);">
  <i class="fas fa-icon" style="font-size:2.5rem; opacity:0.3; color:var(--text-muted);"></i>
  <p style="color:var(--text-muted); margin-top:12px;">Nothing here yet</p>
</div>
```

### Dev Panel Forms
```html
<div class="dev-sub-section">
  <!-- auto-styled inputs, labels, selects -->
</div>
```

---

## Page Transitions

CSS `@keyframes pageIn/pageOut` + JS intercepts nav clicks:
- Body gets `page-enter` class on load → fade + slide up animation
- Body gets `page-exit` class on nav away → fade + slide out
- Defined in `base.html`

---

## Task Animations

Classes used in dashboard task list:
- `anim-in` / `anim-out-left` / `anim-out-right` — slide directions
- `animating-out` — currently exiting
- `deleting` — being removed from DOM

Smooth height animation wrapper:
```css
.smooth-height-wrapper {
  transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
```

---

## ApexCharts Usage

Radial ring charts (macro rings, etc.) need their container:
```css
display: flex;
flex-wrap: wrap;
justify-content: center;
```

Charts initialized in `dashboard/js/dashboard.js`.

---

## Static Images (app/static/global/img/)

| File | Usage |
|------|-------|
| `mybrain-logo.png` | Sidebar logo + login brand mark |
| `favicon-192.png` | Browser tab favicon (all pages) |
| `gym-banner.png` | Gym page hero banner |
| `nutrition-banner.png` | Nutrition page hero banner |
| `agents-banner.png` | Agents page hero |
| `dashboard-hero-bg.png` | Available but currently unused |
| `login-bg.png` | DO NOT USE — broken, shows CSS text. Use CSS animated rings instead |

---

## Known Gotchas

1. **Brand FA icons:** Docker, GitHub, etc. need `fab fa-docker` not `fas fa-docker`. Bare icon names stored in DB auto-get `fas` prepended by template unless they already contain a space.

2. **Modal activation:** Use `.classList.add('active')` — base CSS expects `.modal-overlay.active { display: flex; }`.

3. **Quick-add row:** Needs `.active { display: flex !important; }` to show inline form row.

4. **ApexCharts radial rings:** Container must have `display:flex; flex-wrap:wrap; justify-content:center` or chart positioning breaks.

5. **Login background:** `login-bg.png` is broken (renders as CSS text). The login page uses CSS animated rings (`@keyframes`) — do not replace with a static image.

6. **Docker build:** `update_db.py` must run before gunicorn starts (handled in entrypoint). If you add new tables, update `update_db.py`.

7. **Mobile sidebar:** Collapses to 60px at 768px breakpoint. Nav item `<span>` labels are hidden. Only icon shows.

8. **New nav items:** Must add `uhm()` permission check in `base.html`'s nav section or the link won't render for restricted users.

9. **Never hardcode hex colors.** Always use CSS token vars (`var(--accent)`, `var(--bg)`, etc.).

---

## Stitch Design Reference

- **MyBrain Portal Stitch project ID:** `17870514152139637350`
- Use `mcp__stitch-mcp__get_screen` to retrieve reference HTML
- Available screens: Dashboard Desktop, Agents Desktop, Gym Desktop, Nutrition Desktop, Settings Desktop, Workout Desktop, Mobile Dashboard

---

## Design Continuity Rules

1. Always use design token CSS vars — never hardcode hex colors
2. New pages must extend base.html: `{% extends "base.html" %}{% block content %}`
3. Page headers: Archivo font, weight 900, with colored FA icon in rounded box
4. Empty states: dashed border, centered, 2.5rem icon at 0.3 opacity
5. Forms in dev panel: use `.dev-sub-section` wrapper for auto-styled inputs
6. New nav items: add to `base.html .nav-links` with `uhm()` permission check
