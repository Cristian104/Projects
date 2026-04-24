# Knowledge Base — Claude Context

MkDocs-powered personal knowledge base → knowledge.mybrain.world

## Stack
- **Generator**: MkDocs with Material theme
- **Port**: 8008 (VPS)
- **Source**: `docs/` directory (Markdown files)

## Run locally
```bash
cd ~/stacks/services/knowledge-base
pip install mkdocs-material
mkdocs serve   # → localhost:8000
```

## Build & deploy
```bash
mkdocs build   # generates site/ directory
# VPS auto-deploys via GitHub Actions on push
```

## Key files
| File | Purpose |
|------|---------|
| `mkdocs.yml` | Site config, nav structure, theme |
| `docs/` | All Markdown content |
| `docs/index.md` | Home page |

## Conventions
- All content in `docs/` as Markdown
- Navigation defined in `mkdocs.yml` under `nav:`
- Use Material theme admonitions: `!!! note`, `!!! warning`, etc.
- Images in `docs/assets/`
- The `scribe-docs` Claude agent auto-generates and publishes docs here

## Skills to use
| Task | Skill |
|------|-------|
| Generate and publish docs for any project | `/docs` — reads source, writes Markdown, saves to knowledge base |
| Create a NotebookLM notebook from docs | `/notebooklm` |
