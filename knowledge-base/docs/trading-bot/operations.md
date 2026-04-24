# Operations

## Daily Commands

```bash
# Stream live logs
docker logs -f bot_official

# Check bot status
docker ps | grep bot_official

# Relaunch (git pull + rebuild)
cd ~/stacks/remastered_bot && ./relaunch.sh

# Full rebuild
sudo docker compose --profile official up -d --build
```

## Start / Stop

```bash
# Start production bot
sudo docker compose --profile official up -d --build

# Stop cleanly (waits for current cycle to finish)
sudo docker compose --profile official down

# Start lab/test bot
sudo docker compose --profile lab up --build bot-lab

# Remove orphaned containers
sudo docker compose --profile official up -d --remove-orphans
```

## Database (PostgreSQL)

```bash
# Connect
docker exec -it remastered_db psql -U admin -d remastered_core

# View open positions
SELECT ticker, entry_price, highest_price, tier, timestamp FROM active_positions;

# View recent transactions
SELECT ticker, action, quantity, price, created_at FROM transaction_history ORDER BY created_at DESC LIMIT 20;

# View intelligence logs
SELECT ticker, sentiment_score, order_issued, conviction, created_at FROM intelligence_logs ORDER BY created_at DESC LIMIT 20;
```

## Ghost Position Recovery

If the bot loses sync with the broker (e.g., after a crash), `sync_reality()` runs automatically at the start of each full cycle. It:

1. Fetches live portfolio from T212
2. Restores missing positions to the DB (`DO NOTHING` on conflict — won't overwrite live data)
3. Skips tickers sold in the last 2 hours (settlement lag protection)

Manual trigger:
```bash
docker exec bot_official python3 -c "from app.trading.strategy import GlomeriatoV01; g = GlomeriatoV01(); g.sync_reality()"
```

## Deduplication Issues

If `active_positions` has duplicate rows (pre-V0.5 deployments):
```sql
-- Check for duplicates
SELECT ticker, COUNT(*) FROM active_positions GROUP BY ticker HAVING COUNT(*) > 1;
```

The idempotent migration in `_initialize_db()` consolidates duplicates automatically on restart.

## Docker Maintenance

```bash
# View all containers
docker ps -a

# View disk usage
docker system df

# Clean up stopped containers and unused images
docker system prune -f

# Rebuild only the bot (not DB)
sudo docker compose --profile official up -d --build bot_official
```

## Switching Brain Backend

Via the dashboard at [dashboard.mybrain.world](https://dashboard.mybrain.world) — toggle between Gemini (fast, ~2min cycle) and local Ollama (slow, ~30min cycle).

Or directly in the database:
```sql
UPDATE bot_settings SET value = 'gemini' WHERE key = 'brain_mode';
-- or
UPDATE bot_settings SET value = 'local' WHERE key = 'brain_mode';
```

## Monitoring

- **Dashboard:** [dashboard.mybrain.world](https://dashboard.mybrain.world)
- **Telegram:** Buy/sell alerts sent to configured Telegram bot
- **Logs:** `docker logs -f bot_official`
