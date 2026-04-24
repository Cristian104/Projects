# Backups

## Storage

All backups go to **Google Drive** via `rclone`.
Remote name: `gdrive` | Target folder: `VPS-Backups/`

## What Gets Backed Up

| Data | Source | Frequency |
|------|--------|-----------|
| MyBrain DB (SQLite) | `~/stacks/services/mybrain-portal/instance/` | Weekly |
| PostgreSQL dump | `remastered_core` via `pg_dump` | Weekly |
| Docker configs | `~/stacks/services/*/docker-compose.yml` | Weekly |
| n8n workflows | `~/stacks/services/n8n/` | Weekly |

## Backup Script

```bash
~/stacks/scripts/backup.sh
```

Runs every **Sunday at 04:00 Warsaw** (after Docker cleanup at 03:00).

## Manual Backup

```bash
bash ~/stacks/scripts/backup.sh
```

## Restore

```bash
# List backups
rclone ls gdrive:VPS-Backups/

# Download a specific backup
rclone copy gdrive:VPS-Backups/mybrain-2026-03-05.tar.gz ./

# Restore SQLite
tar -xzf mybrain-2026-03-05.tar.gz -C ~/stacks/services/mybrain-portal/instance/
```
