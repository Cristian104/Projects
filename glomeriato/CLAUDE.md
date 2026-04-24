# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Glomeriato V0.2 — The Transatlantic Snowball**
Autonomous algorithmic trading bot for Trading 212 (Invest & CFD), powered by **Gemini API** (`gemini-2.5-flash`). Develop on `main` branch.

---

## Commands

```bash
# Full system relaunch (git staging + docker build + start)
./relaunch.sh

# Wipe DB tables and restart (active_positions + intelligence_logs only)
./fresh_start.sh

# Manual launch — production
sudo docker compose --profile official up -d --build

# Manual launch — sandbox/lab (uses MockNewsAggregator)
sudo docker compose --profile lab up -d --build

# Stream bot logs
docker logs -f bot_official

# Dashboard web server (local dev)
uvicorn app.web.server:app --host 0.0.0.0 --port 8501

# Rotate backups manually
bash scripts/backup_manager.sh

# Discover / remap T212 ticker IDs (outputs to app/data/ticker_map.json)
python scripts/discover_tickers.py
```

There is no test suite. Sandbox testing uses `--profile lab` with `MockNewsAggregator`.

Docker uses two env files: `.env` (shared) + `.env.official` or `.env.lab` (profile-specific). The `stacks-net` Docker network must exist externally.

---

## Architecture

### Cycle timing

The `__main__` loop in `app/trading/strategy.py` runs on a **5-minute tick**:
- **Every 30 minutes** (`minute % 30 < 1`): full cycle — `sync_reality()` → Guardian pass → Sentinel scan → brain decisions → order execution → market summary
- **Every 5 minutes** (otherwise): Guardian-only exit pass on open positions
- **Every 2 hours** during market hours: Telegram 2h trade digest
- **22:30 Warsaw**: EOD summary via Gemini Flash → Telegram

### Data flow

```
targets.json → Sentinel.screen_universe()
                    ↓ (urgency + reversion candidates)
             strategy.process_region()
                    ↓ [regime gate → VIX gate → exposure gates]
             NewsAggregator → brain.triage_sentiment()   ← Analyst stage
                    ↓ (score ≥ 60 + RSI screen pass)
             brain.execute_decision()                     ← Manager stage
                    ↓ (BUY + conviction ≥ 0.65 + sector cap)
             trading212.place_order() → memory.open_position()
                    ↑
             memory.get_ticker_history(limit=3)  ← temporal memory
```

### Entry gates (evaluated in order, all must pass)

1. **Regime filter** — broad market index above `REGIME_SMA_PERIOD`-day SMA (±`REGIME_FILTER_TOLERANCE`). SPY for US, ^STOXX50E for EU.
2. **Volatility gate** — VIX (US) or VSTOXX (EU) must be below `VIX_PAUSE_THRESHOLD` (30.0).
3. **Max positions** — `MAX_CONCURRENT_POSITIONS` (10) open at once.
4. **Capital deployed** — total invested must be below `MAX_CAPITAL_DEPLOYED_PCT` (65%) of balance.
5. **Sector concentration** — at most `MAX_POSITIONS_PER_SECTOR` (2) positions per GICS sector.
6. **Cooldown** — tickers sold within 4h are skipped.
7. **Analyst score** — Gemini sentiment score ≥ 60/100.
8. **Technical screen** — URGENCY entries require RSI 60–80 + price > 20d SMA; REVERSION entries require RSI < 35.
9. **ADX gate** — `ADX_THRESHOLD` (25.0) required for momentum (URGENCY) entries; reversion entries bypass this.
10. **Manager conviction** — `MIN_BUY_CONVICTION` (0.65) floor on Manager's 0–1.0 output.

### Guardian exit matrix (`guardian.py:evaluate_position`)

Evaluated in strict priority order per position:

| Priority | Trigger | Action |
|----------|---------|--------|
| 0 | `price ≤ entry × (1 − 0.025)` | SELL_ALL — Hard Stop |
| 1 | After reaching 1.5R peak, `price ≤ entry × 1.003` | SELL_ALL — Breakeven Stop |
| 2 | `price ≤ highest_price − 3×ATR` (Chandelier) | SELL_ALL — Trailing Stop |
| 3 | Held ≥ 4h AND `gain < 0.5×ATR` | SELL_ALL — Time Decay |
| 4 | `price ≥ entry + 2×ATR`, tier==0 | SELL_PARTIAL 50% → tier 1 |
| 5 | `price ≥ entry + 3×ATR`, tier==1 | SELL_PARTIAL 50% → tier 2 |

`highest_price` updated each Guardian pass. All thresholds are configurable in `app/core/config.py:Settings`.

### Sentinel screening (`sentinel.py`)

`screen_universe()` returns two candidate buckets:
- **urgency** — top 10 by `(volume-weighted momentum) × (volatility expansion)` score, ADX-filtered
- **reversion** — stocks >2 StdDev below 20d SMA with 5m volume exhaustion spike

Hard filters before scoring: region-specific liquidity floor (EU 500k, US 1M), price $2–$1,500, market cap ≥ $100M, annualized volatility ≤ 150%.

### Brain (`brain.py:QuantBrain`)

Two-stage Gemini API pipeline (single model, conceptually two roles):
1. **Analyst** — scores raw headlines 0–100 + one-sentence reason
2. **Manager** — synthesizes analyst score + technicals + last 3 `intelligence_logs` rows → JSON `{Order, Conviction, Reasoning}`

JSON parse failure triggers one retry with a simplified prompt; on second failure defaults to HOLD. `BRAIN_MODE` is readable from DB at runtime (`get_setting("brain_mode")`).

### Ticker mapping (two-step)

Yahoo Finance tickers (`AAPL`, `SAP.DE`) used internally everywhere. `trading212.py._load_mappings()` converts them to T212 instrument IDs (`AAPL_US_EQ`, `SAPd_EQ`) at order time via `app/data/ticker_map.json`. Missing mappings cause silent order failure — check this file first.

### Regional market hours (Europe/Warsaw TZ)

| Region | Open | Close |
|--------|------|-------|
| EU | 08:48 | 17:42 |
| US | 14:30 | 22:30 |

**Session filters**: No new entries in the first 90 min on Mondays (`AVOID_MONDAY_OPEN_MINUTES`); no entries after 16:00 on Fridays (`AVOID_FRIDAY_CLOSE_HOUR`). Off-hours (non-weekend): 3 random tickers sampled hourly for temporal memory, no orders placed.

Polish (`.WA`) and Spanish (`.MC`) tickers require whole-share quantities (`int()` rounding); `.WA` capped at 60 shares.

### Database schema (PostgreSQL — `remastered_core`)

| Table | Purpose |
|-------|---------|
| `active_positions` | Live holdings; Guardian's source of truth (`tier`, `highest_price`, `entry_atr`) |
| `intelligence_logs` | All AI scan decisions; last 3 rows per ticker feed temporal memory |
| `transaction_history` | Financial audit trail with FX fees and post-trade balance |
| `market_summaries` | Per-cycle executive briefs for the dashboard |
| `bot_settings` | Runtime key-value store (e.g. `brain_mode` can be toggled without restart) |

All DB access is synchronous psycopg2 through `app/core/memory.py:DBManager`.

---

## Key Conventions

- **Logging**: `loguru` only. Never `print()`.
- **AI temperature**: Always `0.1` — do not raise it.
- **Financial precision**: Deduct 0.15% FX fee on spend side (`/ 1.0015`). Reference `trading212.py:place_order()`.
- **Guardian is exit authority**: All stop/profit logic belongs in `guardian.py` only.
- **Sentinel is entry gate**: Any ticker reaching the brain must have passed `apply_hard_filters()` first.
- **Config**: `app/core/config.py:Settings` is the single source of truth. Use `settings.*` — no ad-hoc `os.getenv()`.
- **Fails open**: VIX fetch, regime filter, and technical data failures all return `True` (don't block trading on data issues).

## Known Issues

- **Telegram** (`app/connectors/telegram.py`) is wired for `send_digest()` and `send_eod_summary()` from the main loop, but `TelegramBot` is not injected into `process_region()` — individual trade alerts queue in `_notif_queue` and are only sent on the 2h digest schedule.
- **`asyncpg` and `SQLAlchemy`** are imported/listed as dependencies but unused; codebase uses synchronous psycopg2 exclusively.
- **Timezone drift**: `guardian.py` time-decay check uses `datetime.now(timezone.utc)` and converts positions timestamps assuming UTC. Docker container is `TZ=Europe/Warsaw`. If migrating timestamps, update `memory.py` inserts and all comparisons together.
- **`sync_reality()` uses `os.getenv()`** to init `Trading212` and `DBManager` in `GlomeriatoV01.__init__` — bypasses `Settings`. These should be migrated to `settings.*`.

## Skills to use

| Task | Skill |
|------|-------|
| Review code changes for quality after edits | `/simplify` |
| Research improvements before implementing | Use the `investment-research-analyst` Agent |
