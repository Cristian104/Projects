# SSH Hardening

## Current Configuration

SSH is the only direct access method to the VPS. It is hardened as follows:

| Setting | Value | File |
|---------|-------|------|
| `PasswordAuthentication` | `no` | `/etc/ssh/sshd_config` |
| `PermitRootLogin` | `no` | `/etc/ssh/sshd_config` |
| Auth method | SSH key (ed25519) only | — |

## SSH Key

- **Algorithm:** ed25519
- **Local path:** `~/.ssh/id_ed25519` (private), `~/.ssh/id_ed25519.pub` (public)
- **Connect:** `ssh -i ~/.ssh/id_ed25519 jorg@76.13.251.113`

## Applying Changes

After editing `/etc/ssh/sshd_config`:

```bash
sudo systemctl reload ssh
```

## Disable Password Auth (reference command)

```bash
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config && sudo systemctl reload ssh
```

## Disable Root Login (reference command)

```bash
sudo sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config && sudo systemctl reload ssh
```

## Verify Config

```bash
grep -E '^(PermitRootLogin|PasswordAuthentication)' /etc/ssh/sshd_config
```

Expected output:
```
PasswordAuthentication no
PermitRootLogin no
```

## Locked Out Recovery

If you lose your SSH key access:

1. Use **Hostinger VNC Console** (VPS panel → Console button) — bypasses SSH entirely
2. From VNC, restore your key or reset SSH config
3. The Hostinger SSH key (`crisestrada.med@gmail.com`) registered in the portal can also be used for Hostinger rescue tools
