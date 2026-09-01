# Projects

Source code for all Brain projects. Each folder is an independent deployable service.

## Structure

| Project | Description |
|---------|-------------|
| `glomeriato/` | Algorithmic trading bot for Trading 212 |
| `mybrain-portal/` | Personal dashboard (gym, nutrition, tasks) |
| `portfolio/` | Portfolio site (Next.js) |
| `morning-brief/` | News pipeline — RSS + AI briefing |
| `knowledge-base/` | MkDocs knowledge base |
| `cvManager/` | AI-powered CV manager & job application assistant |
| `nexus/` | AI CLI session manager (Electron) |

## Workflow

```
git checkout -b feat/<project>/<description>
# work and test locally with your own .env
git checkout main && git merge feat/<project>/<description>
git push origin main  # triggers auto-deploy to VPS via Brain
```

## Environment Variables

Each project has a `.env.example` listing required variables.
Copy it to `.env` and fill in your own values for local development.
Real production secrets are managed separately and never committed.

## Adding a New Project

1. Create a new folder with your project code
2. Add a `docker-compose.yml` (needed for VPS deploy)
3. Add a `.env.example` listing all required env vars
4. Push to `main`
