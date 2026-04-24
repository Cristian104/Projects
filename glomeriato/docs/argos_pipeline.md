# 🤖 Argos Autonomous Self-Improvement Pipeline

**Argos** is the autonomous self-improvement orchestrator for the **Glomeriato** trading bot. Operating as a closed-loop self-developing AI system, Argos dynamically analyzes market regimes, assesses bot performance, synthesizes new strategies, and safely implements codebase improvements without human intervention. 

In this architecture, **Argos decides WHAT to improve**, while **Claude Code decides HOW to implement it**.

---

## 🕒 Execution Schedule
The pipeline runs automatically via cron on **Sundays at 09:00 (Warsaw Time)**, preparing the system for the upcoming trading week before markets open.

---

## 🔄 Full Pipeline Steps (In Order)

1. **DB Metrics & Performance Profiling (30-Day Window):** 
   Extracts trailing 30-day KPIs from the PostgreSQL database (`remastered_core`), including P&L, win rate, average hold times, AI conviction stats, and fee burdens.
2. **Perplexity Real-Time Market Research:** 
   Queries the `sonar-pro` model for live market data (regimes, earnings blackouts, macro events) to provide external grounding.
3. **Parameter Simulation:** 
   Runs local historical simulations (`param_sim.py`) against recent data to find mathematically optimal trading parameters.
4. **Gemini 2.5 Pro Synthesis:** 
   Fuses DB metrics, Perplexity research, and simulation data to generate a structured JSON payload containing a ranked list of architectural improvements and parameter recommendations.
5. **Claude Code Execution (VPS):** 
   Connects to the VPS via SSH to automatically implement the highest-ranked improvements, applying parameter updates and earnings blackouts directly to the codebase.
6. **Report & Delivery:** 
   Compiles an execution summary, stores the experiment in the database, and delivers the final report via the Vanitas gateway to Telegram.

---

## 🔍 Perplexity `sonar-pro` Integration

Argos uses Perplexity's `sonar-pro` model as its "eyes" on the live market to escape the knowledge cutoff of standard LLMs. 

### Queries Executed
1. **Market Regime Detection:** Analyzes current momentum vs. mean-reversion trends, VIX levels, and sector rotation leaders for EU (DAX, CAC40) and US (S&P500, NASDAQ) equities.
2. **Parameter Grounding:** Asks for academic and institutional consensus on ATR multipliers and time-decay parameters tailored to *today's* specific volatility regime.
3. **Risk Management:** Identifies tickers entering earnings blackouts (reporting within 7 days), high-momentum sectors, and severe macro events (Fed/ECB rate decisions, CPI drops) that necessitate a trading pause.

### Cost & Configuration
- **Model:** `sonar-pro`
- **Max Tokens:** 1200 per query.
- **Temperature:** `0.1` (Strict, factual, quantitative).
- **Cost Efficiency:** Highly constrained token usage (3 queries per week) keeps operational costs negligible while providing institutional-grade market context.

---

## 🧠 Gemini 2.5 Pro Synthesis & JSON Structure

Gemini 2.5 Pro acts as the "Architect." Using Google Search grounding and a low temperature (`0.05`), it digests the raw data to produce a strict JSON blueprint for Claude Code to execute.

### Expected JSON Output Structure
```json
{
  "weekly_assessment": "Summary of bot health and market conditions.",
  "ranked_improvements": [
    {
      "rank": 1,
      "title": "Dynamic ATR Scaling",
      "task_prompt": "DETAILED instructions for Claude Code with file paths (app/core/config.py)...",
      "difficulty": "EASY|MEDIUM|HARD",
      "risk": "LOW|MEDIUM|HIGH",
      "expected_impact": "+2% win rate by avoiding premature stop-outs in high VIX.",
      "auto_implement": true
    }
  ],
  "earnings_blackout": ["AAPL", "NVDA"],
  "macro_pause": false,
  "param_recommendations": {
    "ATR_TRAILING_MULTIPLIER": 3.0,
    "ATR_TIME_DECAY_HOURS": 4.0,
    "MIN_BUY_CONVICTION": 0.70,
    "MAX_POSITION_PCT": 0.08
  },
  "new_ideas": [
    {
      "title": "Volume Profile Integration",
      "description": "Filter entries by VPOC...",
      "effort_weeks": 2
    }
  ]
}
```
*Note: Argos will only auto-implement the Rank 1 improvement if `auto_implement` is `true`, `difficulty` is EASY/MEDIUM, and `risk` is LOW/MEDIUM.*

---

## 🛠️ Claude Code Executor Pattern (SSH)

The physical changes to the codebase are made autonomously using an SSH Executor Pattern.

1. **Invocation:** Argos connects to the live deployment server (`76.13.251.113`) via SSH using a secure key.
2. **Payload Delivery:** It passes the Gemini-generated `task_prompt` as a JSON string to a bash wrapper: `claude_executor.sh`.
3. **Execution & Validation:** Claude Code spins up on the VPS, reads the target files, writes the new code, and automatically verifies Python syntax (`python3 -m py_compile`).
4. **Rebuild:** If required, the executor natively triggers a Docker rebuild (`docker compose build`) to deploy the updated bot seamlessly.
5. **Return:** A JSON status line (files changed, rebuild status, success state) is returned via standard output back to the Argos orchestrator.

---

## 🛡️ Safety Mechanisms

To prevent the AI from breaking a live financial system, Argos implements several hardcoded fail-safes.

### Minimum Data Threshold
Before touching any code, Argos checks if there is statistically significant data.
- **Rule:** The bot must have completed at least **5 trades (`total_buys >= 5`)** in the 30-day window.
- **Action:** If the threshold is not met, Argos skips code changes to prevent overfitting on noise, defaulting to "Research-Only Mode."

### Rate-Limit Retry Logic
Claude Code API limits can cause implementation failures.
- **Detection:** If the executor returns `rate_limited: true`.
- **Action:** Argos drops a flag file (`/tmp/argos-claude-retry.flag`) containing a 24-hour timestamp lock.
- **Recovery:** The next cron run will check this file. If the 24-hour window has not expired, it safely skips codebase modifications while still delivering the research report.

---

## ♻️ The 3-Layer Feedback Loop

Glomeriato learns and adapts across three distinct persistence layers:

1. **`targets.json` (The Universe):** 
   Modified directly via Claude Code to apply weekly *Earnings Blackouts*, dynamically excluding volatile tickers from the Sentinel scanner before earnings reports.
2. **`argos_experiments` (The Memory):** 
   A PostgreSQL table logging every weekly JSON plan, parameter tweaks, and expected outcomes. This allows future Argos runs to evaluate if last week's "improvement" actually worked.
3. **`market_summaries` (The Context):** 
   Database tables (`transaction_history`, `intelligence_logs`) that provide the hard empirical P&L and conviction data fed back into Perplexity and Gemini to start the next loop.
