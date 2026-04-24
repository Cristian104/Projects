# MyBrain Portal — Claude Context

Personal dashboard for gym, nutrition, tasks, and personal data tracking.

## Stack
- **Backend**: Python/Flask, Jinja2 templates, SQLAlchemy
- **Frontend**: Vanilla JS + CSS custom design system (see CONTEXT.md for full tokens)
- **DB**: PostgreSQL `remastered_core` (shared with trading bot)
- **Port**: 5000 (local), 5000 (VPS) → mybrain.mybrain.world

## Run locally
```bash
cd ~/stacks/services/mybrain-portal
source venv/bin/activate
python run.py   # → localhost:5000
```

## Key files
| File | Purpose |
|------|---------|
| `run.py` | Entry point |
| `app/__init__.py` | Flask factory, blueprints registered here |
| `app/models/` | SQLAlchemy models |
| `app/routes/` | Flask blueprints per feature (gym, nutrition, tasks…) |
| `app/templates/` | Jinja2 HTML templates |
| `app/static/` | CSS, JS, assets |
| `CONTEXT.md` | Full design system: color tokens, spacing, typography |

## Design system (summary)
- Background: `#0F172A`, Surface: `#1E293B`, Accent: `#22C55E` (green)
- **Always use CSS variables** from `base.html :root` — never hardcode colors
- Border radius tokens: `--r-sm` 6px → `--r-xl` 18px
- Full token reference in `CONTEXT.md`

## Conventions
- All routes return rendered templates or JSON — no React/Vue
- Flash messages for user feedback
- DB migrations: add columns carefully, portal shares DB with bot

## Skills to use
| Task | Skill |
|------|-------|
| Adding/improving UI (new page, component, layout) | `/ui-ux-pro-max` |
| Building dashboard sections or data panels | `/interface-design:init` |
| Auditing templates against the design system | `/interface-design:audit` |
| Reading design context before touching UI | `/project-context` — reads CONTEXT.md |
| Full portal redesign | `/new-site` |
