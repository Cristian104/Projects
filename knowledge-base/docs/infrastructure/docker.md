# Docker Services

## Container Naming Convention

Every container is named to match its Cloudflare subdomain:
`<name>` container → `<name>.mybrain.world`

Check all names are correct:
```bash
bash ~/stacks/scripts/sync_container_names.sh
```

## Common Commands

```bash
# See all running containers
docker ps

# Restart a service
docker compose -f ~/stacks/services/<service>/docker-compose.yml restart

# View logs
docker logs -f <container-name>

# Disk usage
docker system df

# Manual cleanup (also runs weekly via cron)
bash ~/stacks/scripts/docker-cleanup.sh
```

## Maintenance

Automated weekly cleanup runs every **Sunday at 03:00** — removes dangling images, stopped containers, and stale build cache. Never removes active service images or volumes.
