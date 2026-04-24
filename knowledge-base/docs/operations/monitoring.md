# System Monitoring & Alerts

This document outlines the essential tools and practices for monitoring the various services and agents within the `infrastructure` of the `stacks` monorepo. Effective monitoring ensures system health, prompt issue detection, and operational stability.

## Container Management: Dockge

Dockge provides a web-based interface for managing Docker Compose stacks, offering a quick visual overview of container status, logs, and resource usage.

!!! info
> Dockge is typically accessible on port `5001` on the VPS.

To access:
1. Open a web browser.
2. Navigate to `http://YOUR_VPS_IP:5001`.
3. Log in with your configured credentials.

From the Dockge dashboard, you can:
*   View container status (running, stopped, unhealthy).
*   Access real-time container logs.
*   Start, stop, restart, or update services.

## Systemd Service Monitoring: `journalctl`

Critical background services are often managed by `systemd`. The `journalctl` utility is the primary tool for inspecting their logs and status.

!!! tip
> Use `journalctl` to diagnose issues with services like `OpenClaw Gateway` or custom `scripts` running as services.

**Common Commands:**
*   **View recent logs for a service:**
    ```bash
    sudo journalctl -u <service_name>.service --since "5 min ago" --no-pager
    ```
    _Example for OpenClaw Gateway:_
    ```bash
    sudo journalctl -u openclaw-gateway.service --since "5 min ago" --no-pager
    ```
*   **Follow logs in real-time:**
    ```bash
    sudo journalctl -u <service_name>.service -f
    ```
*   **View logs since boot:**
    ```bash
    sudo journalctl -u <service_name>.service -b
    ```

## Docker Container Logs: `docker logs`

For individual Docker containers, direct log inspection via the `docker logs` command is essential. This is particularly useful for debugging application-level issues within specific services.

!!! note
> Within the `bot` project (`Glomeriato`), all system events are logged using `loguru`, making container logs highly structured and informative.

**Common Commands:**
*   **View real-time logs for a container:**
    ```bash
    docker logs -f <container_name>
    ```
    _Example for Glomeriato bot:_
    ```bash
    docker logs -f bot_official
    ```
*   **View all logs for a container (historical):**
    ```bash
    docker logs <container_name>
    ```
*   **View logs with timestamps:**
    ```bash
    docker logs -t <container_name>
    ```

## Agent-Driven Telegram Alerts

Several AI agents integrated into the system leverage Telegram for real-time notifications, alerts, and interaction. This provides immediate feedback on critical events, automated reports, or operational statuses.

!!! info
> Telegram API tokens are configured via shared environment variables (e.g., `~/stacks/.env`).

**Key Agents Utilizing Telegram:**
*   **Vanitas**: The primary assistant (`@vanitas_oc_bot`), often provides general system updates or responses.
*   **Peccata**: The engineering sub-agent (`@peccata_bot`), may issue alerts related to development processes or system health.
*   **morning-brief**: Delivers AI-generated news briefings.

These agents are configured to send messages to specific Telegram chats or users, providing an additional layer of monitoring and communication.

## Critical Monitoring Ports (VPS)

For direct access and debugging, understanding the key ports exposed by services on the VPS is crucial.

| Port  | Service                        | Monitoring Use Case                                    |
| :---- | :----------------------------- | :----------------------------------------------------- |
| `5001` | Dockge                         | Overall Docker container health & management           |
| `8501` | Trading Dashboard              | Real-time trading bot performance & metrics            |
| `18789` | OpenClaw Gateway               | Access to agent services (check if gateway is up)      |
| `8009` | Morning Brief / News Reader    | Check if news pipeline is operational                  |

---
## Related
*   Runbooks
*   Nginx Configuration
*   OpenClaw Overview
*   Trading Bot Operations
*   Vanitas Agent
*   Peccata Agent
*   Glomeriato Overview