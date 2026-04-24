# Vanitas: The OpenClaw Primary AI Assistant

Vanitas serves as the cornerstone OpenClaw primary AI assistant, facilitating seamless interaction with users through its dedicated Telegram bot, `@vanitas_oc_bot`. Leveraging the advanced capabilities of the Gemini 2.5 Flash model, Vanitas acts as the main session agent, intelligently processing user queries and orchestrating responses by delegating tasks to specialized OpenClaw sub-agents.

!!! info **Core Function:** Vanitas is the user's primary interface to the OpenClaw ecosystem, responsible for understanding intent and managing conversational flow.

## Key Capabilities

*   **Telegram Integration:** Accessible via `@vanitas_oc_bot`, providing a familiar and immediate communication channel for users.
*   **Advanced Conversational AI:** Powered by the `Gemini 2.5 Flash` model, enabling nuanced understanding, context retention, and coherent response generation.
*   **Task Orchestration:** Directs user requests to appropriate specialized agents within the OpenClaw framework, such as Argos for research or Mundi for specific data processing tasks.
*   **Session Management:** Maintains conversational state to provide a continuous and personalized user experience.

## Architecture & Integration

Vanitas operates within the OpenClaw Workspace, acting as the central hub for external interactions. Its core intelligence module communicates with the Gemini API, while its Telegram integration handles message ingress and egress.

### Model Backend

The `Gemini 2.5 Flash` model is chosen for its balance of speed and advanced reasoning capabilities, crucial for real-time interactive assistance.

!!! note **Performance:** The "Flash" variant ensures low-latency responses, making `@vanitas_oc_bot` highly responsive in real-time conversations.

### Telegram Interface

The Telegram bot uses a secure API token to interact with the Telegram Bot API. This token is typically managed as an environment variable to ensure security.

```bash
# Example environment variable for Telegram Bot Token
export TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_API_TOKEN"
```

### OpenClaw Agent Orchestration

Vanitas communicates with other OpenClaw agents, such as Argos and Mundi, typically through an internal messaging queue or direct API calls within the OpenClaw Workspace. It interprets user intent and formulates structured requests for these specialized agents.

## Configuration

Core configuration for Vanitas involves setting up API keys and bot tokens.

*   **Gemini API Key:** Required for authenticating with the Gemini API.
*   **Telegram Bot Token:** For `@vanitas_oc_bot` to connect to Telegram.

Example `.env` file snippet:

```ini
# .env (example)
GEMINI_API_KEY="your_gemini_api_key_here"
TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"
# Optional: List of authorized Telegram User IDs
AUTHORIZED_TELEGRAM_USERS="123456789,987654321"
```

!!! warning **Security Best Practice:** Always store API keys and sensitive tokens as environment variables or using a secure secrets management system. Never hardcode them directly into the application code.

## Interaction Workflow

Users interact with Vanitas directly through the Telegram application.

1.  **User Message:** A user sends a message to `@vanitas_oc_bot`.
2.  **Vanitas Ingest:** The message is received by the Vanitas Telegram handler.
3.  **Intent Analysis:** Vanitas, using `Gemini 2.5 Flash`, analyzes the user's message to understand their intent and identify any explicit requests for other OpenClaw services.
4.  **Task Delegation:** If a specialized task is identified (e.g., "find recent research on X"), Vanitas formats and dispatches the request to the relevant agent (e.g., Argos).
5.  **Response Synthesis:** Once the sub-agent completes its task, it returns the result to Vanitas. Vanitas then synthesizes this information into a user-friendly response.
6.  **User Response:** Vanitas sends the final response back to the user via Telegram.

## Maintenance & Troubleshooting

*   **Log Monitoring:** Regularly check Vanitas logs for errors, API call failures, or unexpected behavior.
    ```bash
    # Example: Viewing logs if running in Docker
    docker logs -f openclaw-vanitas-container-name
    ```
*   **API Key Validity:** Ensure both Gemini and Telegram API keys are active and have the necessary permissions.
*   **Network Connectivity:** Verify that the Vanitas service has outbound access to the Gemini API and inbound/outbound access to the Telegram Bot API.

## Related

*   OpenClaw Overview
*   Argos Agent
*   Mundi Agent
*   Peccata Agent
*   OpenClaw Tools Documentation
*   Nginx Proxy Configuration
---