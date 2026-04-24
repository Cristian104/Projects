# Cloudflare Tunnels Setup

This document outlines the Cloudflare Tunnel configuration used to expose internal services from the VPS to the public internet securely without opening firewall ports.

## Overview
Glomeriato's infrastructure relies on **Cloudflare Tunnels (Argo Tunnels)** to provide secure access to web services. This approach ensures that the VPS remains invisible to the public internet, with the exception of SSH (Port 22).

- **Tunnel ID:** `36d04fd6`
- **Security Policy:** All public traffic is proxied through Cloudflare. The VPS firewall (Group ID: `230111`) is configured to drop all incoming traffic except for SSH.

## Architecture
1.  **Cloudflare Edge:** Receives HTTPS requests for `*.mybrain.world`.
2.  **cloudflared (Service):** A lightweight daemon running on the VPS that maintains an outbound-only connection to Cloudflare.
3.  **Local Routing:** `cloudflared` routes incoming requests from the tunnel to the specific local ports where services are running.

## Exposed Services
The following services are currently routed through the tunnel:

| Public Domain | Local Port | Service Description |
| :--- | :--- | :--- |
| `mybrain.mybrain.world` | `5000` | MyBrain Portal (Dashboard) |
| `knowledge.mybrain.world` | `8008` | MkDocs Knowledge Base |
| `news.mybrain.world` | `8009` | Morning Brief / News Reader |
| `portfolio.mybrain.world` | `3010` | Portfolio Site (Next.js) |

## Service Management
The `cloudflared` agent runs as a `systemd` service on the VPS.

### Commands
- **Check Status:** `sudo systemctl status cloudflared`
- **Restart Tunnel:** `sudo systemctl restart cloudflared`
- **View Logs:** `sudo journalctl -u cloudflared -f`

## Configuration & Maintenance
The tunnel is primarily managed via the **Cloudflare Zero Trust Dashboard**. 

### Adding a New Service
1.  **Deploy the Service:** Ensure the new service is running locally on a specific port (e.g., `8080`).
2.  **Cloudflare Dashboard:**
    *   Navigate to **Networks > Tunnels**.
    *   Select the tunnel (`36d04fd6`) and click **Configure**.
    *   Under **Public Hostname**, add a new entry (e.g., `newservice.mybrain.world` -> `http://localhost:8080`).
3.  **Verification:** The change is usually instantaneous. Test the new URL in a browser.

## Troubleshooting
- **502 Bad Gateway:** The tunnel is up, but the local service is down. Check if the Docker container or local process is running on the expected port.
- **1033 Tunnel Not Found:** The `cloudflared` service on the VPS might be stopped. Check the service status via `systemctl`.
- **DNS Issues:** Ensure the CNAME record for the subdomain is correctly pointing to the Cloudflare Tunnel ID in the Cloudflare DNS settings.
