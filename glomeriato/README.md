# 🌌 Glomeriato V0.5 (Pre-Release)

**The Deduplicating Transatlantic** — An autonomous algorithmic trading bot for **Trading 212 (Invest & CFD)**, powered by dual-agent **DeepSeek-R1** via Ollama.

> V0.5 fixes two critical live-trading data integrity bugs discovered in V0.3 (position deduplication + ghost restore cooldown) and ships a full minimalist pro dashboard redesign with login screen.

---

### 🚀 Key Capabilities

- **🧠 Dual-Agent Intelligence**:
  - **Analyst (8b)**: Rapid news sentiment triage with per-ticker RSS feeds.
  - **Manager (14b)**: Deep reasoning with **Temporal Memory** (last 3 intelligence logs per ticker).
- **🛡️ Guardian Exit Matrix**: Dynamic trailing stops (6×ATR), 4-hour time-decay, and tiered 30% profit ladders.
- **🛰️ Multi-Stage Sentinel**: Urgency (momentum/volatility) and Mean Reversion mathematical screening.
- **📊 Institutional Dashboard**: Apple × TheVerge aesthetic with real-time intelligence logs and system console.
- **🔋 Low Power Mode**: 3 random ticker scans per hour during off-market hours to build temporal memory.
- **📱 Telegram Alerts**: Real-time BUY and EXIT notifications on every trade.
- **🛑 Graceful Shutdown**: SIGTERM exits cleanly after the current cycle — no more mid-execution kills.

---

### 🆕 What's New in V0.5

| Fix | Description |
|-----|-------------|
| **Position Dedup** | UPSERT replaces INSERT — ALV.DE 3-row bug eliminated; unique DB index enforced |
| **Ghost Restore Guard** | `was_recently_sold()` cooldown prevents T212 settlement-lag restores |
| **Dashboard V2** | Dark-green palette, CSS animations, glass position cards, 4 live metric cards |
| **P&L Card** | Live unrealised P&L pulled from T212 broker portfolio each refresh |
| **Next-Cycle Countdown** | MM:SS timer to next :00/:30 mark, visible in the navbar metric row |

---

### 🛠️ Quick Start

#### Launch
```bash
./relaunch.sh
```

#### Monitor
```bash
docker logs -f bot_official        # live logs
# or open http://localhost:8501    # dashboard
```

#### Shutdown (graceful)
```bash
docker stop bot_official           # sends SIGTERM, waits for cycle end
```

---

### 🏗️ Directory Overview

```
app/
  trading/     → strategy.py (main loop), guardian.py (exits), sentinel.py (screening)
  intelligence/→ brain.py (dual-agent DeepSeek), news_aggregator.py
  connectors/  → trading212.py (broker API), telegram.py (notifications)
  core/        → memory.py (PostgreSQL), config.py (settings)
notebook/      → Obsidian-formatted research and operations documentation
scripts/       → backup_manager.sh, discover_tickers.py
```

---

### 📚 Documentation

See `notebook/Releases/V0.5-Pre.md` and `notebook/Glomeriato_V0.5_Pre-Release/` for:
- `Architecture.md` — fix breakdown and rationale
- `Operations.md` — deployment, verification queries, monitoring

---

*Developed for autonomous transatlantic equity growth.*
