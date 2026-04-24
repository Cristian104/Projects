# Argos: Glomeriato's Autonomous Self-Improvement Orchestrator

Argos is the core self-improvement agent for the Glomeriato V2.1 trading bot, designed to autonomously analyze performance, synthesize improvements, and trigger their implementation. It operates on a weekly schedule, running every Sunday at 09:00 Warsaw time.

!!! info Argos decides *WHAT* to improve. Claude Code decides *HOW* to implement it. This forms a closed self-development loop.

## Core Pipeline (The Improvement Loop)

Argos orchestrates a multi-stage pipeline to ensure continuous optimization of the Glomeriato bot:

1.  **DB Metrics Analysis**:
    *   Analyzes 30 days of PostgreSQL database metrics, including:
        *   Trading performance (total buys/sells, gross buy/sell values, fees).
        *   Account balance fluctuations (min/max/latest).
        *   Intelligence logs (average/stddev conviction, buy/sell signals, high/low conviction trades).
        *   Trade holding periods and returns (average/max hold hours, average return percentage, winning trades).
        *   Winning ticker breakdown.

2.  **Market Context (`Perplexity Sonar-Pro`)**:
    *   Leverages `Perplexity Sonar-Pro` to gather external market intelligence:
        *   Identifies current market regimes.
        *   Provides sector-specific context.
        *   Flags upcoming earnings blackouts.

3.  **Improvement Synthesis (`Gemini 2.5 Pro`)**:
    *   Combines internal performance metrics with external market context.
    *   Utilizes `Gemini 2.5 Pro` (with search grounding) to:
        *   Generate a ranked list of potential improvements for Glomeriato.
        *   Propose strategic ideas to optimize trading.

4.  **Code Implementation (`Claude Code Execution`)**:
    *   Selects the top-ranked improvement.
    *   Triggers the Claude Code script on the VPS to automatically implement the change.

5.  **Validation & Rebuild**:
    *   Confirms that the implemented code change compiles successfully.
    *   Initiates a rebuild of the Docker bot containers.
    *   Executes a test cycle to validate functionality.

6.  **Reporting & Delivery**:
    *   Generates a comprehensive report of the improvement process.
    *   Delivers the report via Vanitas to Telegram for stakeholder awareness.

## Configuration & Access

Argos relies on several environment variables and hardcoded values for its operation.

!!! warning Sensitive API keys are hardcoded in the source for demonstration/default purposes. In production, these should be managed securely (e.g., environment variables, secrets management).

### Database Connection

Argos connects directly to the `remastered_core` PostgreSQL database.
```
DB_HOST     = "172.17.0.1"
DB_PORT     = 5432
DB_NAME     = "remastered_core"
DB_USER     = "admin"
DB_PASSWORD = "remastered_secure_pass"
```

### API Keys

```
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "AIzaSyAddwWNW0r49P-kAw3iIYCGq5R-XTpB6Wg"))
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "pplx-KZBsgEZmsj9Y5SI53ExAeP4OPnPMC6QFsmNHlF9rQq5OtYb2N")
```

### AI Gateway

Argos communicates with a local AI gateway for completions.
```
GATEWAY_URL   = "http://172.17.0.1:18789/v1/chat/completions"
GATEWAY_TOKEN = "839f89a481ec25ad98808be2c0f60ad50f8382aef481006aa8c9133ddf9b0dde"
```

### VPS & Executor Details

For code implementation, Argos interacts with a remote VPS via SSH.
```
VPS_HOST    = "76.13.251.113"
VPS_USER    = "jorg"
SSH_KEY     = "/workspace/ssh/id_ed25519"
BOT_DIR     = "/home/jorg/stacks/bot"
EXECUTOR    = "/home/jorg/stacks/scripts/claude_executor.sh"
```

## Usage

Argos can be run manually with specific command-line arguments:

*   **Manual Run**: `python /workspace/argos/improve.py`
    *   Executes the full improvement pipeline, potentially leading to code changes.

*   **Dry Run**: `python /workspace/argos/improve.py --dry-run`
    *   Performs all analysis and improvement synthesis steps but *does not* trigger any actual code changes or rebuilds. Useful for testing and evaluation.

*   **Reset Demo**: `python /workspace/argos/improve.py --reset-demo`
    *   Resets the Trading 212 demo balance, likely used in conjunction with testing improvement cycles.

## Related

*   Vanitas
*   Claude Code
*   Glomeriato V2.1
*   Docker Compose
*   PostgreSQL
*   Glomeriato Overview
---