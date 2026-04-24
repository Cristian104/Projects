# Security Overview

This document summarizes the security posture of the VPS infrastructure.

## Defense Layers

Security is implemented in multiple independent layers, so that if one fails, others remain in place.

```
Internet
    │
    ▼
┌─────────────────────────────────┐
│  Hostinger Hardware Firewall    │  Port 22 (SSH) only — all else dropped
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Cloudflare (Web Services)      │  Zero Trust + Google OAuth for *.mybrain.world
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  UFW (OS Firewall)              │  Port 22 allow, everything else default deny
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  iptables DOCKER-USER chain     │  Blocks external NEW connections to Docker ports
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Docker port binding            │  All services bound to 127.0.0.1 (not 0.0.0.0)
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  SSH Hardening                  │  Key-only auth, root login disabled, fail2ban
└─────────────────────────────────┘
```

## Security Checklist

| Control | Status | Details |
|---------|--------|---------|
| Hostinger hardware firewall | ✅ Active | Port 22 only, all else dropped |
| UFW | ✅ Active | Port 22 allow |
| SSH key-only auth | ✅ Enabled | `PasswordAuthentication no` |
| SSH root login | ✅ Disabled | `PermitRootLogin no` |
| fail2ban | ✅ Running | Watching sshd jail |
| Docker port binding | ✅ Done | All ports on `127.0.0.1` |
| DOCKER-USER iptables | ✅ Active | Blocks external Docker access |
| Cloudflare Zero Trust | ✅ Active | Google OAuth on `*.mybrain.world` |
| Cloudflare Tunnel | ✅ Active | No inbound ports needed for services |

## What's Exposed to the Internet

| Port | Service | Protection |
|------|---------|------------|
| 22 | SSH | Key-only + fail2ban + Hostinger firewall |
| 443 | Web services via Cloudflare | Google OAuth (Zero Trust) |

Everything else is either internal-only or blocked at the hardware firewall.

## Quick Audit

```bash
# Check open ports
sudo ss -tlnp

# Check UFW status
sudo ufw status

# Check fail2ban
sudo fail2ban-client status sshd

# Check iptables DOCKER-USER chain
sudo iptables -L DOCKER-USER -n

# Check SSH config
grep -E '^(PermitRootLogin|PasswordAuthentication|MaxAuthTries)' /etc/ssh/sshd_config
```
