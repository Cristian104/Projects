# fail2ban

fail2ban monitors logs and automatically bans IPs that show signs of brute-force attacks.

## Installation

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Current Status

```bash
# Overall status
sudo fail2ban-client status

# SSH jail status
sudo fail2ban-client status sshd
```

## Default SSH Jail Settings

| Setting | Default | Meaning |
|---------|---------|---------|
| `maxretry` | 5 | Failed attempts before ban |
| `findtime` | 10 min | Window to count failures |
| `bantime` | 10 min | How long to ban the IP |

## Useful Commands

```bash
# View all banned IPs
sudo fail2ban-client status sshd

# Unban an IP manually
sudo fail2ban-client set sshd unbanip <IP>

# View fail2ban logs
sudo tail -f /var/log/fail2ban.log
```

## Custom Configuration (optional)

To override defaults, create `/etc/fail2ban/jail.local`:

```ini
[sshd]
enabled = true
maxretry = 3
bantime = 1h
findtime = 10m
```

Then restart:
```bash
sudo systemctl restart fail2ban
```
