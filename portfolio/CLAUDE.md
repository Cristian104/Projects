# Portfolio Site — Claude Context

Personal portfolio site → portfolio.mybrain.world

## Stack
- **Framework**: Next.js (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Port**: 3000 (local), 3010 (VPS)

## Run locally
```bash
cd ~/stacks/sites/portfolio/app
npm run dev   # → localhost:3000
```

## Key files
| Path | Purpose |
|------|---------|
| `app/` | Next.js app directory (App Router) |
| `app/page.tsx` | Home page |
| `app/layout.tsx` | Root layout, metadata, fonts |
| `app/components/` | Reusable UI components |
| `public/` | Static assets (images, icons) |
| `tailwind.config.ts` | Tailwind customisation |

## Conventions
- App Router only — no `pages/` directory
- Server components by default; add `"use client"` only when needed
- Tailwind for all styling — no CSS modules or inline styles
- Images: use `next/image` with proper width/height

## Skills to use
| Task | Skill |
|------|-------|
| Full redesign or building a new site from scratch | `/new-site` — uses Google Stitch + UI UX Pro Max, deploys to VPS |
| Adding/improving UI components, layouts, styling | `/ui-ux-pro-max` |
| Building a dashboard or app-like section | `/interface-design:init` |
| Auditing existing UI against design system | `/interface-design:audit` |
| Extracting design patterns from existing code | `/interface-design:extract` |
| Reading design context before starting work | `/project-context` |
