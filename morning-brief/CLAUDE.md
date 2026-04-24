# Morning Brief — Claude Context

RSS news collector + AI briefing pipeline delivered via Telegram each morning.

## Stack
- **Web app**: Flask + Gunicorn → news.mybrain.world (port 8009)
- **DB**: SQLite at `news.db` (gitignored — local/VPS only)
- **AI**: Gemini Flash for briefing generation
- **Delivery**: Telegram bot

## Run locally
```bash
cd ~/stacks/morning-brief
source venv/bin/activate  # or pip install -r requirements.txt
python app.py   # → localhost:8009
```

## Key files
| File | Purpose |
|------|---------|
| `app.py` | Flask web app — news reader UI |
| `collector.py` | RSS feed fetcher, stores to news.db |
| `briefing.py` | AI briefing generator (Gemini Flash) |
| `docker-compose.yml` | VPS deployment |
| `news.db` | SQLite DB (gitignored) |

## Key paths (VPS)
- Scripts: `~/stacks/services/openclaw2/workspace/morning_brief/`
- Gateway token: in `.env`

## Conventions
- SQLite only — no PostgreSQL
- News.db is gitignored: never commit it
- Gemini Flash for all AI calls (cheap, fast enough for news)
