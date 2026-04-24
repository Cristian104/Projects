# Changelog

All notable changes to this project will be documented in this file.

---

## [V0.5-Pre] - 2026-02-24 (The Deduplicating Transatlantic)

### 🔒 Fixed — Position Deduplication (`fix/position-dedup`)
- `_initialize_db()` now runs an idempotent migration that consolidates existing duplicate `active_positions` rows via weighted-average entry price, summed quantity, max highest_price, and latest ATR/conviction.
- Added `CREATE UNIQUE INDEX IF NOT EXISTS uq_active_positions_ticker` — one row per ticker enforced at the DB level.
- `open_position()` converted to UPSERT:
  - **New BUY path**: `ON CONFLICT (ticker) DO UPDATE` accumulates quantity and recalculates weighted-average entry price. `entry_atr`, `entry_conviction`, and `highest_price` are kept at their most favourable values.
  - **Sync-restore path** (timestamp supplied): `ON CONFLICT (ticker) DO NOTHING` — real positions are never overwritten by a ghost restore.

### 👻 Fixed — Ghost Restore Guard (`fix/ghost-restore`)
- Added `DBManager.was_recently_sold(ticker, hours=2)` — queries `transaction_history` for `SELL` or `SELL_PARTIAL` actions within the last N hours.
- `sync_reality()` restore loop now checks `was_recently_sold()` before reinstating a broker position; tickers in settlement cooldown emit `⏭️ Skipping restore` and are skipped, preventing T212 settlement-lag ghost restores.

### 🎨 Feature — Dashboard V2 (`feat/dashboard-v2`)
- Complete rewrite of `app/dashboard.py` with dark-green palette (`#05100A` background, `#00D26A` primary, `#00FF87` accent).
- CSS animations: `fadeInUp`, `pulse-dot`, `scan-line`, `glow-text`, `card-in`.
- **Navbar strip**: brand name with glow animation, pulsing `● LIVE` dot, `V0.4` badge, live HH:MM:SS clock.
- **Four metric cards**: Cash Balance (live from T212), Open Positions (deduplicated count), Est. P&L (summed `ppl` from broker portfolio), Next Cycle countdown (MM:SS to next :00/:30).
- **Executive Summary**: styled left-border `div` with latest `market_summaries` content.
- **Three tabs**:
  - `⬡ Intelligence` — expanders with sentiment progress bars, Analyst + Manager reasoning columns.
  - `◈ Portfolio` — two-column glass-card grid per position (entry, qty, time held, trailing stop distance, next-tier progress bar, conviction badge).
  - `⌥ Console` — colorized log output (`SUCCESS`=green, `WARNING`=yellow, `ERROR`=red), auto-scroll to bottom via injected `<script>`, Clear button.
- Auto-refresh every 15 s retained.

---

## [V0.3-Pre] - 2026-02-24 (The Resilient Transatlantic)

### 🛑 Fixed — Graceful Shutdown
- Added `SIGTERM` and `SIGINT` signal handlers to `GlomeriatoV01.__init__()`.
- Module-level `_running` flag replaces `while True:` — Docker `docker stop` now waits for the current cycle to complete before exiting.
- `wait_for_next_window()` is skipped if shutdown was requested, so exit is near-instant post-cycle.
- Logs `🛑 Graceful shutdown complete.` on clean exit.

### 🕐 Fixed — UTC Timezone Normalization
- Guardian `hours_held` calculation in `strategy.py` now uses `datetime.now(timezone.utc)` vs `pos['timestamp'].replace(tzinfo=timezone.utc)`.
- Eliminates potential timezone drift between the container (`TZ=Europe/Warsaw`) and Postgres naive timestamps.

### ⚡ Fixed — T212 API Rate Limiter
- Class-level `_last_request_time` and `_min_interval = 0.5s` added to `Trading212`.
- `_rate_limit()` method throttles all HTTP calls globally to 500ms minimum interval.
- Applied to: `get_cash_balance`, `cancel_pending_orders`, `get_pending_orders`, `get_owned_tickers`, `get_detailed_portfolio`, `place_order`.
- Existing 429 exponential backoff retained as a second layer.

### 📱 Added — Telegram Trade Notifications
- `TelegramBot` (previously dead code) now instantiated in `GlomeriatoV01.__init__()`.
- BUY alert sent after every successful order in `process_region()`.
- EXIT alerts sent after `SELL_ALL` and `SELL_PARTIAL_30` fills in `run_cycle()`.
- All Telegram calls wrapped in `try/except` — network failures never block trading.

### ✅ Fixed — Partial Sell Reconciliation
- After `SELL_PARTIAL_30` fills, `get_detailed_portfolio()` is called to fetch the **actual** broker quantity.
- DB updated with broker qty instead of locally-computed `full_qty * 0.70`.
- If broker qty == 0: `close_position()` called + discrepancy logged as WARNING.
- If broker qty differs from expected by >0.01: delta logged as WARNING before DB update.

### 🧹 Chore — Remove Unused Dependencies
- Removed `asyncpg>=0.30.0` from `pyproject.toml`.
- Removed `sqlalchemy[asyncio]>=2.0.0` from `pyproject.toml`.
- Fixed `DATABASE_URL` property in `config.py` to use `postgresql+psycopg2://` driver string.
- Docker image approximately 150MB lighter.

---

## [V0.2-Pre] - 2026-02-24 (The Institutional Upgrade)

### 🚀 Added
- **Temporal Memory:** The 14b Portfolio Manager now recalls the last 3 intelligence logs for every ticker, enabling trend-aware reasoning.
- **Multi-Stage Sentinel:** Implemented "Urgency" (momentum/volatility) and "Mean Reversion" mathematical filters.
- **Apple x TheVerge Dashboard:** Complete UI overhaul with glassmorphism, custom typography, and Apple-style widget metrics.
- **System Console:** Live terminal log mirroring directly on the dashboard.
- **Automated Backups:** Rotated backup system (last 10 runs) triggered automatically every 30 minutes.
- **Low Power Mode:** Resource-saving logic for off-market hours (3 random scans per hour).
- **Transactional Summaries:** DeepSeek-14b generated executive briefs focusing on trades, alpha candidates, and market logic.

### 🛡️ Changed/Improved
- **Robust Reality Sync:** 2-way portfolio synchronization that handles broker downtime and prevents accidental "ghost" purges.
- **Partial Sell Support:** Strategy logic now fully supports the Guardian's tiered profit ladders (30% partial sells).
- **Adaptive Market Hours:** Dynamic scan windows supporting pre-market and after-hours volatility.
- **Rich CLI:** Integrated `rich` library for beautiful, structured terminal output with progress bars.

### 🐛 Fixed
- **Indentation Stability:** Resolved multiple Python indentation errors in the main strategy loop.
- **DB Constraint Fixes:** Expanded `action` column length to support descriptive transactional logs.

---

## [Pre-Alpha V0.1] - 2026-02-23 (The Remastered Architecture)
- Initial V2.1 architecture with PostgreSQL and Dual-Agent Brain.
