# Infrastructure Overview

## Hosts

| Host | Role | IP |
|------|------|----|
| VPS (Hostinger KVM 4) | Primary — runs everything | 76.13.251.113 |
| Local machine | Trading bot + Ollama (GPU) | 172.22.198.142 |

All services except Ollama run on the VPS. The local machine exists only for GPU inference.

## Network

All services are exposed via **Cloudflare Tunnels** — no ports open to the internet except through Cloudflare.
The tunnel daemon (`cloudflared`) runs as a systemd service on the VPS.

Internal Docker network: `172.17.0.0/16`
From inside containers, reach VPS host at: `172.17.0.1`

## Stack Overview

```
VPS (76.13.251.113)
├── cloudflared          → Cloudflare tunnel (all *.mybrain.world subdomains)
├── mybrain              → MyBrain Portal (Flask, port 5000)
├── n8n                  → Workflow automation (port 5678)
├── finance              → Firefly III (port 8080)
├── actual               → Actual Budget (port 5006)
├── dashboard            → Trading dashboard (port 8501)
├── news                 → Morning brief news reader (port 8009)
├── code                 → Code Server (port 9090)
├── knowledge            → This docs site (port 8008)
├── whiskey              → Whiskey cellar tracker (port 8011)
├── bot_official         → Glomeriato trading bot
├── remastered_db        → PostgreSQL 15 (port 5432)
├── openclaw-sbx-shared  → OpenClaw agent sandbox
└── dockge               → Docker stack manager (port 5001)
```
