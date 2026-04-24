# VPS & Services Reference

Comprehensive guide to the primary VPS (Hostinger KVM 4) and all active services.

## VPS Specs

- **Host:** Hostinger KVM 4
- **IP:** 76.13.251.113
- **User:** `jorg`
- **Location:** Europe (Warsaw TZ)
- **OS:** Debian/Ubuntu (Standard KVM image)
- **Access:** SSH via `jorg@76.13.251.113` (using ed25519 key).

## Services Directory

All services except OpenClaw Gateway run as Docker containers, mostly managed via Docker Compose. Connectivity is managed via Cloudflare Tunnels; no ports are exposed to the public internet except through `cloudflared`.

| Service | Public URL | Local Port | Docker Container |
|---------|------------|------------|-------------------|
| **MyBrain Portal** | [mybrain.world](https://mybrain.world) | 5000 | `mybrain` |
| **OpenClaw Gateway** | [openclaw.mybrain.world](https://openclaw.mybrain.world) | 18789 | *Systemd Service* |
| **Trading Dashboard** | [dashboard.mybrain.world](https://dashboard.mybrain.world) | 8501 | `dashboard` |
| **News Reader** | [news.mybrain.world](https://news.mybrain.world) | 8009 | `news` |
| **Portfolio** | [portfolio.mybrain.world](https://portfolio.mybrain.world) | 3010 | `portfolio` |
| **Knowledge Base** | [knowledge.mybrain.world](https://knowledge.mybrain.world) | 8008 | `knowledge-base` |
| **n8n** | [n8n.mybrain.world](https://n8n.mybrain.world) | 5678 | `n8n` |
| **Code Server** | [code.mybrain.world](https://code.mybrain.world) | 9090 | `code-server` |
| **Dockge** | [dockge.mybrain.world](https://dockge.mybrain.world) | 5001 | `dockge` |
| **PostgreSQL** | - | 5432 | `remastered_db` |
| **Deploy Webhook** | [deploy.mybrain.world](https://deploy.mybrain.world) | 9191 | *Systemd Service* |

## Key Directories

| Path | Purpose |
|------|---------|
| `~/stacks/` | Root of the monorepo. |
| `~/stacks/bot/` | Glomeriato trading bot (official & lab). |
| `~/stacks/services/` | Dockerized services (Portal, OpenClaw, KB). |
| `~/stacks/sites/` | Frontend sites (Portfolio). |
| `~/stacks/morning-brief/` | News aggregation & briefing logic. |
| `~/stacks/openclaw-workspace/` | Filesystem mount for AI agent sandbox. |
| `~/stacks/scripts/` | Maintenance, backup, and deployment scripts. |
| `~/stacks/infrastructure/` | Docker infrastructure (Dockge). |

## Deployment Workflow

The VPS employs an automated "Push to Deploy" pipeline:

1. **Push:** Local changes are pushed to `main` branch on GitHub (`Cristian104/stacks`).
2. **Action:** GitHub Actions triggers a POST request to the VPS Deploy Webhook.
3. **Webhook:** `deploy-webhook.py` (port 9191) receives the request, pulls the latest code, and rebuilds the affected container:
   ```bash
   git pull origin main
   docker compose up -d --build <service>
   ```

## Environment Variables

- **Shared:** `~/stacks/.env` (Gemini API keys, Telegram tokens).
- **Service-Specific:** Inside each directory (e.g., `~/stacks/bot/.env`).
- **Webhook Secret:** `/etc/stacks-deploy.env` (authorized via GHA `DEPLOY_SECRET`).
- **Database:** `DATABASE_URL=postgresql://admin:password@localhost:5432/remastered_core` (Localhost on VPS).

## Management Commands

### Logging & Monitoring
```bash
# View deploy webhook logs
journalctl -u stacks-deploy.service -f

# View OpenClaw gateway logs
journalctl -u openclaw-gateway.service -f

# View container logs
docker logs -f bot_official
docker logs -f mybrain

# Check active ports
sudo ss -tulpn | grep LISTEN
```

### Manual Service Restart
```bash
# Restart Systemd services
sudo systemctl restart openclaw-gateway
sudo systemctl restart stacks-deploy

# Rebuild Docker stacks manually
cd ~/stacks/services/mybrain-portal && docker compose up -d --build
```

### Database Management
```bash
# Connect to PostgreSQL directly from VPS
docker exec -it remastered_db psql -U admin -d remastered_core
```
