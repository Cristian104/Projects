# OpenClaw 2.0 - Multi-Agent AI Gateway

OpenClaw 2.0 serves as the **multi-agent AI gateway** within the `stacks` monorepo, providing a robust platform for deploying and managing specialized AI agents. It integrates DeepSeek-R1 (via Ollama) and Gemini models, enabling sophisticated interactions through a Telegram bot interface, secure sandbox isolation, and a comprehensive tool system.

!!! info Purpose
> OpenClaw orchestrates various AI agents, allowing them to operate within isolated environments and interact with external systems via a defined toolset.

## Architecture Overview

OpenClaw 2.0 is designed for production deployment on a VPS, distinct from local development environments. Its core components facilitate secure execution and management of AI agents.

- **`services/openclaw2/`**: This directory contains the main application logic and production configuration for the OpenClaw gateway.
- **`openclaw-workspace/`**: This serves as the **sandbox workspace**, mounted as `/workspace/` inside the OpenClaw execution environment. It provides a secure, isolated space for agents to perform tasks without affecting the host system.

!!! warning Configuration
> The configuration for OpenClaw (e.g., `services/openclaw2/openclaw.json`) contains production secrets and is **`.gitignore`d**. Never commit this file.

## Key Agents

OpenClaw hosts several specialized AI agents, each with a distinct role:

-   **Vanitas** (`main` agent):
    -   **Model**: `gemini-2.5-flash`
    -   **Telegram Handle**: `@vanitas_oc_bot`
    -   **Role**: Primary assistant for general queries and tasks.
-   **Peccata** (`peccata` agent):
    -   **Model**: `gemini-2.5-pro`
    -   **Telegram Handle**: `@peccata_bot`
    -   **Role**: Engineering sub-agent, specialized in technical tasks and code assistance.
    -   **TTS**: Uses `MEDIA:/workspace/...` path format for text-to-speech outputs (no MIME prefix required).
-   **Argos** (`argos` agent):
    -   **Model**: `gemini-2.5-pro`
    -   **Role**: Autonomous self-improvement loop, focused on enhancing the system's capabilities.

## Operational Commands (VPS)

OpenClaw 2.0 is managed as a systemd service on the VPS.

### Restarting the Gateway

After any configuration changes or updates to the `services/openclaw2/` directory, the gateway service must be restarted.

```bash
sudo systemctl restart openclaw-gateway.service
```

### Viewing Logs

To monitor the OpenClaw gateway's activity and troubleshoot issues, you can inspect its logs.

-   **Systemd Journal (recent logs):**
    ```bash
    sudo journalctl -u openclaw-gateway.service --since "5 min ago" --no-pager
    ```
-   **Daily Log File (detailed history):**
    ```bash
    cat /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
    ```

### Rebuilding Sandbox Image

If there are changes to the sandbox environment or dependencies, the Docker image for the sandbox may need to be rebuilt.

```bash
docker build -t openclaw-sandbox-jorg:bookworm-slim -f /tmp/Dockerfile.openclaw-jorg .
```

!!! tip Ports
> The OpenClaw gateway listens on port `18789` on the VPS.

## Related

-   Vanitas Agent
-   Peccata Agent
-   Argos Agent
-   Glomeriato V2.1 Instructional Context
-   Trading Bot Overview
---