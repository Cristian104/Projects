# Firewall Configuration

Three independent firewall layers protect the VPS.

## Layer 1 — Hostinger Hardware Firewall

Configured in the Hostinger VPS control panel. Operates at the network infrastructure level — before traffic even reaches the server.

| Rule | Port | Protocol | Action |
|------|------|----------|--------|
| SSH | 22 | TCP | Accept |
| Default | * | * | Drop |

**Important:** This is the outermost layer. Even if UFW or iptables fail, this blocks everything except port 22.

To edit: Hostinger Panel → VPS → Firewall.

!!! warning "Don't delete the port 22 rule"
    Without it, you lose all SSH access. Recovery requires Hostinger VNC console.

## Layer 2 — UFW (OS Firewall)

```bash
# Check status
sudo ufw status

# Current rules
To                         Action      From
22/tcp                     ALLOW       Anywhere
```

UFW alone is **not sufficient** for Docker containers — Docker bypasses UFW by writing iptables rules directly.

## Layer 3 — iptables DOCKER-USER Chain

Docker bypasses UFW. This iptables rule closes that gap by blocking all new external connections to Docker-managed ports:

```bash
# View current rules
sudo iptables -L DOCKER-USER -n --line-numbers
```

Expected output:
```
Chain DOCKER-USER (1 references)
num  target     prot opt source               destination
1    ACCEPT     0    --  0.0.0.0/0  0.0.0.0/0  ctstate RELATED,ESTABLISHED
2    DROP       0    --  0.0.0.0/0  0.0.0.0/0  ctstate NEW
```

!!! warning "Not persistent across reboots"
    iptables rules are lost on reboot. To make persistent:
    ```bash
    sudo apt install iptables-persistent
    sudo netfilter-persistent save
    ```

## Layer 4 — Docker Port Binding

All Docker services are bound to `127.0.0.1` in their `docker-compose.yml`:

```yaml
ports:
  - "127.0.0.1:5000:5000"  # ✅ Internal only
  # - "5000:5000"           # ❌ Never — exposes to 0.0.0.0
```

Services are only accessible via Cloudflare Tunnel, which connects from inside the VPS to `localhost`.

## What Ports Are Actually Open

```bash
# Check all listening ports (excluding loopback)
sudo ss -tlnp | grep -v '127.0.0.1' | grep -v '::1'
```

Currently exposed to the internet:
- **Port 22** — SSH (protected by key-only auth + fail2ban)
- Everything else — blocked or internal-only
