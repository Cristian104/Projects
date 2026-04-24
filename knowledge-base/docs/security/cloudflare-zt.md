# Cloudflare Zero Trust

All web services are protected by Cloudflare Zero Trust with Google OAuth. No service is directly accessible via IP:Port from the internet.

## Architecture

```
User (browser)
    │
    ▼
Cloudflare Edge (*.mybrain.world)
    │  Zero Trust Access check
    │  Google OAuth required
    ▼
Cloudflare Tunnel (outbound from VPS)
    │
    ▼
localhost:PORT (service on VPS)
```

The VPS makes an **outbound** connection to Cloudflare — no inbound ports needed.

## Access Policy

- **Application:** `*.mybrain.world` (wildcard covers all subdomains)
- **Auth method:** Google OAuth
- **Allowed email:** `crifris@gmail.com`
- **Session duration:** 24 hours (instant auth enabled)

## Services Behind Zero Trust

| Subdomain | Internal Port | Service |
|-----------|--------------|---------|
| mybrain.mybrain.world | 5000 | MyBrain Portal |
| n8n.mybrain.world | 5678 | n8n automation |
| finance.mybrain.world | 8080 | Firefly III |
| actual.mybrain.world | 5006 | Actual Budget |
| knowledge.mybrain.world | 8008 | This knowledge base |
| dashboard.mybrain.world | 8501 | Trading dashboard |
| code.mybrain.world | 9090 | code-server |
| news.mybrain.world | 8009 | Intelligence Feed |
| dockge.mybrain.world | 5001 | Dockge (Docker manager) |

## Cloudflare Tunnel Service

The tunnel runs as a systemd service:

```bash
# Check tunnel status
sudo systemctl status cloudflared

# View tunnel logs
sudo journalctl -u cloudflared -n 50
```

## Managing Access

To add another authorized email:
1. Cloudflare dashboard → Zero Trust → Access → Applications
2. Select the `*.mybrain.world` application
3. Edit policy → Add email to allow list

To revoke a session:
1. Zero Trust → Access → Active Sessions
2. Revoke the session for the user
