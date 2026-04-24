# Glomeriato — Complete Context

**Everything a Claude instance needs to work on this project without getting lost.**
Architecture details live in `CLAUDE.md`. This file covers: full file map, how modules wire together, environment setup, DB schema, dashboard, common bugs, and gotchas.

---

## Project Structure

```
bot/
├── app/
│   ├── trading/
│   │   ├── strategy.py       ← Main loop entry point (run this to start the bot)
│   │   ├── guardian.py       ← All exit logic — trailing stop, profit tiers, time decay
│   │   └── sentinel.py       ← Ticker screening — urgency + mean reversion candidates
│   ├── intelligence/
│   │   ├── brain.py          ← QuantBrain — Gemini API (Analyst + Manager stages)
│   │   ├── news_aggregator.py← Google News RSS fetcher (async, aiohttp)
│   │   └── mock_news.py      ← Fake news for lab/sandbox testing
│   ├── connectors/
│   │   ├── trading212.py     ← T212 REST API — place orders, get portfolio, cash balance
│   │   └── telegram.py       ← Telegram bot — 2h digest + EOD summary
│   ├── core/
│   │   ├── config.py         ← Settings (Pydantic) — single source of all config
│   │   └── memory.py         ← DBManager — ALL PostgreSQL access goes through here
│   └── web/
│       ├── server.py         ← FastAPI dashboard server (port 8501)
│       ├── templates/
│       │   ├── base.html     ← Shared layout, CSS design system
│       │   ├── login.html    ← Password login page
│       │   └── dashboard.html← Main trading dashboard UI
│       └── static/
│           └── style.css     ← Dashboard styles
├── app/data/
│   ├── targets.json          ← 188 tickers scanned each cycle
│   └── ticker_map.json       ← Yahoo Finance → T212 instrument ID mapping
├── scripts/
│   └── discover_tickers.py   ← Rebuilds ticker_map.json from T212 API
├── docker-compose.yml        ← Two profiles: official (live bot) + lab (simulation)
├── Dockerfile                ← Python 3.12, installs requirements
├── .env                      ← Shared env (Gemini key, DB creds, Telegram)
├── .env.official             ← Live profile env (T212 live key + URL)
├── .env.lab                  ← Lab profile env (T212 demo key + URL)
├── relaunch.sh               ← Full rebuild + restart
└── fresh_start.sh            ← Wipe DB tables + restart (dev only)
```

---

## Environment Variables

### `bot/.env` (shared — committed as `.env.example`)
```
GEMINI_API_KEY=AIzaSyBuyHpi8lc7tpHwYOTpaeIB1JdMM1AZTFo
GEMINI_MODEL=gemini-2.5-flash
DB_HOST=stacks-postgres
DB_NAME=remastered_core
DB_USER=admin
DB_PASSWORD=<password>
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>
DASHBOARD_PASSWORD=glomeriato        ← login password for dashboard.mybrain.world
```

### `bot/.env.official` (live trading)
```
T212_API_KEY=<live key>
T212_SECRET_KEY=<live secret>
T212_BASE_URL=https://live.trading212.com/api/v0   ← MUST be live, not demo
TRADING_MODE=CFD
```

### `bot/.env.lab` (simulation)
```
T212_API_KEY=<demo key>
T212_BASE_URL=https://demo.trading212.com/api/v0
TRADING_MODE=CFD
```

**Critical:** `Trading212.__init__` reads `T212_BASE_URL` from `os.getenv()` directly — if this env var is missing or points to demo, all orders go to the demo account silently.

---

## Docker

```bash
# Start official bot (live trading)
docker compose --profile official up -d --build

# Start lab bot (simulation, uses MockNewsAggregator)
docker compose --profile lab up -d --build

# Start dashboard only
docker compose up -d dashboard

# View logs
docker logs -f bot_official

# Requires external network (create once on VPS):
docker network create stacks-net
```

The `stacks-net` network is external — if it doesn't exist, ALL containers fail to start with a cryptic error.

DB host inside Docker: `stacks-postgres` (the PostgreSQL container on stacks-net).
DB port from VPS host: `localhost:5434` (mapped to 5432 inside the container).

---

## How the Bot Works (module by module)

### `strategy.py` — The Orchestrator
Runs a **5-minute tick loop**. The `__main__` block at the bottom calls `GlomeriatoV01.run()`.

Every tick:
- Every **5 minutes**: Guardian exit pass on all open positions
- Every **30 minutes** (`minute % 30 < 1`): full cycle (see below)
- Every **2 hours** during market hours: Telegram digest via `send_digest()`
- **22:30 Warsaw**: EOD summary via `generate_eod_summary()` → Telegram

Full 30-min cycle:
1. `sync_reality()` — reconciles `active_positions` DB vs live T212 portfolio
2. Guardian exits — evaluates all open positions
3. `sentinel.screen_universe()` — screens tickers, returns `urgency[]` + `reversion[]`
4. `process_region()` — for each candidate: regime gate → VIX gate → exposure gates → news → brain → order

### `sentinel.py` — Entry Filter
`screen_universe(tickers, region)` returns two buckets:
- **urgency**: top 10 by `(volume-weighted momentum) × (volatility expansion)` — requires ADX > 25
- **reversion**: stocks > 2 StdDev below 20d SMA with 5m volume exhaustion

Hard filters before scoring: liquidity floor (EU 500k, US 1M price×vol), price $2–$1,500, market cap ≥ $100M, annualized vol ≤ 150%.

`get_regional_tickers()` splits `targets.json` into EU/US pools based on Warsaw timezone. Off-hours = 3 random tickers sampled hourly for memory building only.

### `brain.py` — QuantBrain (Gemini API)
Two-stage pipeline using `gemini-2.5-flash`:

1. `triage_sentiment(ticker, headlines)` — Analyst: outputs `Score: 0-100` + `Reason: ...`
2. `execute_decision(ticker, analyst_report, technicals, portfolio, history)` — Manager: outputs JSON `{Order, Conviction, Reasoning}`

If JSON parse fails → one retry with simplified prompt → on second failure defaults to `{"Order": "HOLD", "Conviction": 0.0}`.

**When Gemini API budget runs out**: `_query_gemini()` throws → returns `""` → JSON parse fails → perpetual HOLD. No "budget exceeded" appears in the trade logs — the bot just never buys.

`COMPANY_MAP` in `config.py` translates tickers to search queries for Google News:
```python
"SAP.DE": "SAP SE stock news"
"NVDA":   "NVIDIA Corporation stock news"
# tickers NOT in the map → "{ticker} stock news"
```
Only 5 tickers are in the map — most use the generic fallback.

### `news_aggregator.py` — Google News RSS
Async (aiohttp). Fetches top 5 articles from Google News RSS, returns top 2 headlines to brain.
No API key required — public RSS feed.

### `trading212.py` — T212 Connector
- Rate-limited: 500ms minimum between calls
- `place_order(ticker, quantity)`: positive qty = BUY, negative = SELL
- Ticker translation: Yahoo Finance `AAPL` → T212 `AAPL_US_EQ` via `ticker_map.json`
- `.WA` and `.MC` tickers → whole share quantities only (`int()` rounding)
- Missing ticker in map → order fails silently with log warning

### `memory.py` — DBManager
All DB access. Never write raw SQL elsewhere. Key methods:
- `open_position()` — UPSERT (accumulates into existing row with weighted avg entry)
- `close_position()` — DELETE from active_positions
- `log_decision()` — INSERT into intelligence_logs (every brain scan)
- `log_transaction()` — INSERT into transaction_history (only on actual orders)
- `get_ticker_history(ticker, limit=3)` — feeds temporal memory to brain Manager
- `get_setting(key)` / `set_setting(key, value)` — runtime key-value store

---

## Database Schema

PostgreSQL on `stacks-postgres`, database `remastered_core`.

### `active_positions`
```sql
id              SERIAL PRIMARY KEY
ticker          VARCHAR(50) UNIQUE   ← unique constraint — one row per ticker
entry_price     NUMERIC              ← weighted average entry (UPSERT accumulates)
highest_price   NUMERIC              ← updated every Guardian pass for Chandelier stop
entry_atr       NUMERIC              ← ATR at time of entry
quantity        NUMERIC              ← total shares held
tier            INTEGER              ← 0=untriggered, 1=after 50% sold, 2=after another 50%
entry_conviction NUMERIC             ← Manager conviction at entry
timestamp       TIMESTAMP
```

### `intelligence_logs`
```sql
id                  SERIAL PRIMARY KEY
ticker              VARCHAR(50)
sentiment_score     NUMERIC          ← Analyst score 0-100
analyst_reason      TEXT
manager_order       VARCHAR(50)      ← BUY / SELL / HOLD
manager_conviction  NUMERIC          ← 0.0–1.0
manager_reasoning   TEXT
timestamp           TIMESTAMP
```
Last 3 rows per ticker are fed to the Manager as temporal memory.

### `transaction_history`
```sql
id                  SERIAL PRIMARY KEY
ticker              VARCHAR(50)
action              VARCHAR(20)      ← BUY, SELL, SELL_PARTIAL
quantity            NUMERIC
price_executed      NUMERIC
fee_cost            NUMERIC          ← 0.15% FX fee
total_value_pln     NUMERIC
account_balance_after NUMERIC
timestamp           TIMESTAMP
```

### `market_summaries`
```sql
id        SERIAL PRIMARY KEY
summary   TEXT                ← AI-generated cycle brief
timestamp TIMESTAMP
```

### `bot_settings`
```sql
key        VARCHAR(64) PRIMARY KEY
value      TEXT
updated_at TIMESTAMP
```
Default row: `brain_mode = 'local'` — **must be set to `'api'`** for Gemini to work.
Check: `SELECT * FROM bot_settings;`
Fix: `UPDATE bot_settings SET value='api' WHERE key='brain_mode';`

---

## Dashboard (`app/web/`)

FastAPI + Jinja2 + vanilla JS. Live at `dashboard.mybrain.world` (Cloudflare tunnel → `localhost:8501`).

### Auth
Cookie-based HMAC auth. Password from `DASHBOARD_PASSWORD` env var (default: `"glomeriato"`).
Session expires after 8 hours. Cookie name: `dash_session`.

### Routes
| Route | What it does |
|-------|-------------|
| `GET /` | Dashboard (requires auth, redirects to /login if not) |
| `GET /login` | Login page |
| `POST /login` | Authenticate, set cookie |
| `GET /logout` | Clear cookie |
| `GET /api/status` | Market open/closed + Warsaw clock |
| `GET /api/kpi` | Cash balance, open positions count, next cycle countdown |
| `GET /api/positions` | All rows from active_positions |
| `GET /api/portfolio` | Live T212 portfolio (real-time pnl) |
| `GET /api/logs?filter=all\|trades\|high` | intelligence_logs (last 200) |
| `GET /api/summary` | Latest market_summaries row |
| `GET /api/console` | Last 150 lines of app.log (colorized HTML) |
| `GET /api/pending` | Pending T212 orders |
| `GET /export/intelligence` | intelligence_logs CSV download |
| `GET /export/transactions` | transaction_history CSV download |
| `GET /export/positions` | active_positions CSV download |

### Templates
- `base.html` — shared CSS design system (dark theme, monospace terminal aesthetic)
- `login.html` — minimal login form
- `dashboard.html` — full SPA-like dashboard, polls `/api/*` every few seconds via JS

### TemplateResponse API (Starlette 0.36+)
**Always use the new keyword API** — old positional API causes `TypeError: unhashable type: 'dict'`:
```python
# ✅ Correct (Starlette 0.36+)
templates.TemplateResponse(request=request, name="login.html", context={"error": None})

# ❌ Broken (Starlette < 0.36 API — will crash with unhashable dict error)
templates.TemplateResponse("login.html", {"request": request, "error": None})
```

---

## Why the Bot Stops Trading — Diagnostic Checklist

Run these in order before touching any code:

```bash
# 1. Check Gemini budget (most common cause of no trades)
docker logs bot_official 2>&1 | grep -iE "gemini|quota|error|budget" | tail -20

# 2. Confirm T212 URL is live (not demo)
docker exec bot_official env | grep T212_BASE_URL
# Must be: https://live.trading212.com/api/v0

# 3. Check brain_mode in DB
docker exec -it stacks-postgres psql -U admin -d remastered_core \
  -c "SELECT * FROM bot_settings;"
# brain_mode must be 'api' — default is 'local' which disables Gemini

# 4. Check what the bot is actually doing
docker logs -f bot_official | grep -E "HOLD|BUY|SELL|gate|regime|VIX|ADX|conviction|Sentinel"

# 5. Check entry gates aren't blocking everything
# Regime filter (SPY/STOXX50E below 50d SMA) → blocks ALL entries for that region
# VIX > 30 → blocks ALL entries for that region
# ADX < 25 → blocks momentum (urgency) entries (reversion still allowed)

# 6. Check ticker_map.json for missing mappings
# Orders for unmapped tickers fail silently
docker exec bot_official python scripts/discover_tickers.py  # refresh the map
```

### Silent failure modes
| Symptom | Cause |
|---------|-------|
| Perpetual HOLD, no orders | Gemini API budget exhausted |
| Orders placed but nothing in T212 | `T212_BASE_URL` pointing to demo account |
| "HOLD" with conviction 0.0 | `brain_mode` set to `'local'` in bot_settings |
| Specific ticker never trades | Missing from `ticker_map.json` |
| All EU or all US blocked | Regime filter (index below SMA) |
| Everything blocked | VIX/VSTOXX > 30 threshold |

---

## Gemini API — Cost & Keys

**API Key**: `AIzaSyBuyHpi8lc7tpHwYOTpaeIB1JdMM1AZTFo`
**Model**: `gemini-2.5-flash` (cheap text generation, ~$0.0001/1K tokens)
**Budget**: Google Cloud Console → API key quota

Per full 30-min cycle:
- `triage_sentiment()` — 1 call × up to 10 tickers = 10 calls
- `execute_decision()` — 1 call × up to 10 tickers = 10 calls
- JSON retry on failure — up to +10 extra calls
- `generate_market_summary()` — 1 call
- EOD `generate_eod_summary()` — 1 call/day

~21+ calls per cycle × 48 cycles/day ≈ 1,000 calls/day. At flash rates this is ~$0.50–2/day.

**The real budget killer was** `morning-brief/enricher.py` using Imagen 4 ($0.04/image) — now capped at 10/day.

---

## Deployment

**Never SSH to edit code.** Always: edit locally → `git push origin main` → auto-deploys.

```
git push origin main
       ↓
GitHub Actions (.github/workflows/deploy.yml)
       ↓ detects changed files under bot/
POST https://deploy.mybrain.world/deploy {"service": "bot"}
       ↓
Webhook on VPS (port 80, secured with DEPLOY_SECRET)
       ↓
git pull + docker compose up -d --build (profile: official)
```

### What triggers a bot deploy
Any file change under `bot/` on the `main` branch triggers `service=bot`. The webhook handler on the VPS does:
```bash
cd ~/stacks/bot
git pull
docker compose --profile official up -d --build
```

### Dashboard deploy
Dashboard is a separate container (`glomeriato_dashboard`) but lives in the same `bot/docker-compose.yml`. A push to `bot/` rebuilds both bot and dashboard together.

### Manual deploy (VPS only — for emergencies)
```bash
cd ~/stacks/bot
git pull
docker compose --profile official up -d --build
docker logs -f bot_official
```

### Deploy troubleshooting
```bash
# Check GitHub Actions run
gh run list --repo Cristian104/stacks --limit 5

# Check webhook delivered (VPS logs)
# The webhook is at deploy.mybrain.world — handled by a small FastAPI app on the VPS

# Check bot container rebuilt successfully
docker ps | grep bot_official
docker logs bot_official --tail 50
```

---

## Key Conventions (never break these)

- `loguru` only — never `print()` for system events
- AI temperature always `0.1` — do not raise
- FX fee: divide spend by `1.0015` (0.15%) on every financial calculation
- All exit logic → `guardian.py` only
- All entry filtering → `sentinel.py` + gates in `strategy.py`
- New config → `app/core/config.py:Settings` only — never `os.getenv()` inline
- All DB access → `app/core/memory.py:DBManager` only — no raw psycopg2 elsewhere
- `stacks-net` Docker network must exist externally before any container starts

---

## Known Issues

- **`brain_mode` DB default is `'local'`** — must be manually set to `'api'` after first DB init or fresh_start.sh
- **Telegram individual alerts**: Trade alerts queue in `_notif_queue` but only sent on 2h digest — not immediately on execution
- **`asyncpg` + `SQLAlchemy`**: Listed as dependencies and imported but unused — codebase is synchronous psycopg2 only
- **`sync_reality()` bypasses Settings**: Uses `os.getenv()` directly instead of `settings.*`
- **`COMPANY_MAP` only covers 5 tickers**: Most tickers use generic `"{ticker} stock news"` query which may return irrelevant news
- **Missing `ticker_map.json` entries**: Many EU tickers may be absent — run `discover_tickers.py` when adding new tickers to `targets.json`
