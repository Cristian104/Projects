This documentation outlines the architecture, logic, and operational parameters of the `QuantBrain` module, the dual-agent AI core of the Glomeriato V2.1 trading system.

---

# 🧠 QuantBrain: Dual-Agent AI Architecture

The `QuantBrain` module implements a hierarchical decision-making process using Google Gemini. It separates rapid sentiment triage from deep reasoning and execution, ensuring that market news is synthesized with technical data and historical memory before any trade is issued.

## 1. Agent Roles & Pipeline

The system operates in a three-stage pipeline, mimicking the structure of a professional quantitative hedge fund.

### Stage 1: The Analyst (Rapid Sentiment Triage)
*   **Role:** Performs initial "noise reduction" on raw news headlines.
*   **Input:** Ticker symbol and a list of recent RSS headlines.
*   **Output:**
    *   **Sentiment Score:** An integer (0–100).
    *   **Reason:** A concise, one-sentence justification for the score.
*   **Logic:** Focuses purely on immediate market impact and headline sentiment without considering technicals or portfolio state.

### Stage 2: The Portfolio Manager (Execution & Synthesis)
*   **Role:** The lead decision-maker. It cross-checks the Analyst's triage against technical levels, current portfolio holdings, and temporal memory.
*   **Input:** Analyst report, Technical indicators (from Sentinel), Portfolio state, and Historical logs.
*   **Output:** A strict JSON object containing the final trade order.
*   **Logic:** Uses "Temporal Reasoning" to identify trends or reversals in sentiment compared to previous scans.

### Stage 3: The Reporter (Market Synthesis)
*   **Role:** Generates a human-readable transactional summary of the last 30 minutes of activity.
*   **Input:** Recent intelligence logs and trade actions.
*   **Output:** A Markdown-formatted executive summary for the dashboard.

---

## 2. Prompt Engineering & Instruction Sets

### Stage 1: Analyst Prompt
> "Read the provided headlines and output ONLY a score from 0 to 100 (0 is maximum bearish, 50 is neutral, 100 is maximum bullish) and exactly one sentence explaining the reason for interest."

### Stage 2: Manager Prompt (Temporal Reasoning Protocol)
The Manager is instructed to follow a specific protocol to prevent "jittery" trading:
*   **Acceleration vs. Reversal:** Determine if sentiment is gaining momentum or fading.
*   **Conflict Resolution:** If current news contradicts the technical thesis, the Manager must prioritize the most recent data but justify the shift in reasoning.
*   **Memory Integration:** Injects `intelligence_logs` (last X scans) to provide context on whether a "bearish" headline is new information or a continuation of an old story.

---

## 3. Data Schema & Conviction Scoring

### JSON Decision Format
The Manager must output a raw JSON object with the following structure:
```json
{
    "Order": "BUY | SELL | HOLD",
    "Conviction": 0.85,
    "Reasoning": "Synthesis of sentiment trend and technical support levels."
}
```

### Conviction Scoring (0.0 to 1.0)
*   **0.0 - 0.3:** Low confidence. Usually results in a `HOLD` or no action.
*   **0.4 - 0.6:** Moderate confidence. May trigger partial sells or small exploratory buys.
*   **0.7 - 1.0:** High confidence. Strong alignment between News Sentiment, Technical Indicators, and Historical Thesis.

---

## 4. Technical Configuration & Reliability

### Model Settings
*   **Engine:** Google Gemini (configured via `GEMINI_MODEL`).
*   **Temperature:** Fixed at `0.1`. This ensures high determinism and prevents the "hallucination" of creative but unprofitable trading strategies.
*   **Safety:** The system uses regex-based stripping to remove `<think>` blocks and Markdown fences (` ```json `) before parsing.

### Retry & Fail-Safe Logic
If the Manager fails to produce valid JSON:
1.  **Regex Cleaning:** Attempts to extract JSON content from within the response.
2.  **Minimalist Retry:** If `BRAIN_JSON_RETRY` is enabled, the system sends a second, ultra-low-complexity prompt to force a JSON response.
3.  **Default to HOLD:** If all parsing fails, the system defaults to `{"Order": "HOLD", "Conviction": 0.0}` to protect capital.

---

## 5. Decision Flow Summary
1.  **News Ingest:** `Sentinel` fetches headlines.
2.  **Triage:** `Analyst` converts text to a 0–100 score.
3.  **Synthesis:** `Manager` reads (Score + Technicals + Memory + Portfolio).
4.  **Validation:** `Manager` validates if the conviction meets the threshold.
5.  **Execution:** `DBManager` logs the intelligence, and `Trading212` connector receives the order.
