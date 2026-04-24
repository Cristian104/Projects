# My Brain — Knowledge Base

Central documentation for all infrastructure, bots, and services running on the VPS.

## Quick Reference

| Service | URL | Port |
|---------|-----|------|
| MyBrain Portal | [mybrain.world](https://mybrain.world) | 5000 |
| n8n | [n8n.mybrain.world](https://n8n.mybrain.world) | 5678 |
| Trading Dashboard | [dashboard.mybrain.world](https://dashboard.mybrain.world) | 8501 |
| Finance (Firefly) | [finance.mybrain.world](https://finance.mybrain.world) | 8080 |
| Actual Budget | [actual.mybrain.world](https://actual.mybrain.world) | 5006 |
| Code Server | [code.mybrain.world](https://code.mybrain.world) | 9090 |
| News Feed | [news.mybrain.world](https://news.mybrain.world) | 8009 |
| Knowledge Base | [knowledge.mybrain.world](https://knowledge.mybrain.world) | 8008 |

## VPS

- **Host:** 76.13.251.113 (Hostinger KVM 4)
- **SSH:** `ssh -i ~/.ssh/id_ed25519 jorg@76.13.251.113`
- **Storage:** 193GB — cleaned weekly by cron (Sunday 03:00)

## Key Directories

```
~/stacks/
  services/          # All Docker stacks
  scripts/           # Maintenance scripts
  knowledge/         # Old notebook docs (trading bot versions)
  morning-brief/     # News pipeline
```
