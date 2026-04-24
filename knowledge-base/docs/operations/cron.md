# Cron Jobs

All crons run under user `jorg` on the VPS. View with: `crontab -l`

| Schedule | Job | Log |
|----------|-----|-----|
| Every hour | Morning brief collector (RSS fetch) | `~/stacks/morning-brief/collector.log` |
| 08:00 Mon–Fri | Morning brief delivery via Vanitas | `~/stacks/morning-brief/briefing.log` |
| 06:00 Mon–Fri | Argos daily analysis | `/tmp/argos-daily.log` |
| 08:00 Sunday | Argos weekly research | `/tmp/argos-weekly.log` |
| 09:00 Sunday | Argos self-improvement run | `/tmp/argos-improve.log` |
| 03:00 Sunday | Docker cleanup (prune + build cache) | `~/stacks/scripts/docker-cleanup.log` |
| 04:00 Sunday | GDrive backup | `~/stacks/scripts/backup.log` |

## Useful Commands

```bash
# View all cron jobs
crontab -l

# Tail Docker cleanup log
tail -f ~/stacks/scripts/docker-cleanup.log

# Run backup manually
bash ~/stacks/scripts/backup.sh

# Run Docker cleanup manually
bash ~/stacks/scripts/docker-cleanup.sh
```
