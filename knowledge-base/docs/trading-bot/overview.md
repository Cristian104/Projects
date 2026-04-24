# Glomeriato Trading Bot

**Glomeriato** is an autonomous algorithmic trading bot for Trading 212. It runs a 30-minute cycle: scanning the market, evaluating with dual-agent AI, and executing orders — entirely without human intervention.

## Quick Reference

| Item | Value |
|------|-------|
| Platform | Trading 212 (CFD/Invest) |
| Language | Python 3.12 |
| AI Backend | Google Gemini 2.5 Flash (API) or local Ollama |
| Database | PostgreSQL (`remastered_core`) |
| Host | VPS — `76.13.251.113` |
| Dashboard | [dashboard.mybrain.world](https://dashboard.mybrain.world) |

## Start / Stop

```bash
# Production launch
cd ~/stacks/remastered_bot
sudo docker compose --profile official up -d --build

# Full relaunch (git pull + rebuild)
./relaunch.sh

# Stream logs
docker logs -f bot_official

# Stop
sudo docker compose --profile official down
```

## The 30-Minute Cycle

```
:00 / :30  →  sync_reality()      Reconcile DB with live broker positions
           →  Guardian pass        Evaluate exits for all open positions
           →  Sentinel scan        Score 90+ tickers → top 10 candidates
           →  Brain decision       Dual-agent AI: Analyst + Portfolio Manager
           →  Order execution      BUY / SELL_PARTIAL / SELL_ALL via T212 API
           →  Backup               DB snapshot saved

:05/:10/:15/:20/:25  →  Guardian-only pass   Exit checks every 5 min
```

## Containers

| Container | Purpose | Port |
|-----------|---------|------|
| `bot_official` | Trading bot | — |
| `remastered_db` | PostgreSQL | 5432 |
| `glomeriato_dashboard` | Streamlit dashboard | 8501 |

## Key Files

| File | Purpose |
|------|---------|
| `app/trading/sentinel.py` | Market scanner |
| `app/trading/guardian.py` | Risk engine / exit authority |
| `app/intelligence/brain.py` | Dual-agent AI brain |
| `app/trading/strategy.py` | Main cycle orchestrator |
| `app/connectors/trading212.py` | T212 API connector |
| `app/core/config.py` | All configuration settings |

## Conventions

- Use `loguru` only — never `print()`
- All money math deducts 0.15% FX fee: `value / 1.0015`
- AI temperature always `0.1`
- Guardian is the **only** component that can exit a position
