# Changelog

## V0.5.2 — Gemini Dual-Backend (2026-02-25)

- **Brain:** Added Google Gemini API as hot-switchable backend ([ADR-004](decisions/adr-004.md))
- **Guardian:** Extracted into standalone 5-minute loop — exit latency 28min → 5min ([ADR-005](decisions/adr-005.md))
- **DB:** `bot_settings` table stores `brain_mode` for runtime dashboard toggle
- **Loss Analysis:** Research brief added on position loss patterns

## V0.5.1 — Institutional Architecture (2026-02-24)

- Full architecture documentation vault created
- Dashboard V2: dark-green glassmorphism UI, live metrics, intelligence tab, portfolio tab, console tab
- Position deduplication via UPSERT + UNIQUE index ([ADR-003](decisions/adr-003.md))
- Ghost restore guard: `was_recently_sold()` prevents T212 settlement-lag ghosts
- Graceful shutdown: SIGTERM/SIGINT handlers, clean cycle completion before exit
- UTC timezone normalization for `hours_held` Guardian calculation
- T212 API rate limiter: 500ms minimum interval, class-level throttle
- Telegram trade notifications: BUY, SELL_ALL, SELL_PARTIAL alerts
- Partial sell reconciliation: actual broker qty fetched post-fill

## V0.3-Pre — Resilience (2026-02-24)

- Graceful shutdown handlers
- UTC timezone fix for Guardian time-decay
- T212 rate limiter (500ms)
- Telegram notifications
- Partial sell broker reconciliation

## V0.2-Pre — Institutional Upgrade (2026-02-24)

- Temporal memory: Manager recalls last 3 intelligence logs per ticker
- Multi-stage Sentinel: Urgency + Mean Reversion filters
- Dashboard V2: glassmorphism, live metrics
- System console on dashboard
- Automated DB backups (rotated, every 30 min)
- Low Power Mode for off-market hours
- Partial sell support for Guardian tiered exits

## V0.1-Alpha — Remastered Architecture (2026-02-23)

- Initial V2.1 architecture
- PostgreSQL (`remastered_core`) replacing SQLite
- Dual-agent Brain (Analyst + Portfolio Manager)
