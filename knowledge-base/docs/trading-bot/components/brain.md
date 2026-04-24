# QuantBrain — Dual-Agent AI

**File:** `app/intelligence/brain.py`

QuantBrain is the AI decision engine. It processes Sentinel's shortlist through a two-stage agent pipeline — mimicking the structure of a professional quant fund — before issuing a final trade order.

## Agent Architecture

```
Sentinel candidates
        │
        ▼
┌───────────────────┐
│  Stage 1: Analyst │  Gemini 2.5 Flash — rapid sentiment triage
│  (8b equivalent)  │  Input: ticker + headlines
│                   │  Output: score (0-100) + reason
└────────┬──────────┘
         │  score ≥ 60 → proceed
         ▼
┌─────────────────────────┐
│ Stage 2: Portfolio Mgr  │  Gemini 2.5 Flash — deep synthesis
│  (14b equivalent)       │  Input: score + technicals + portfolio + memory
│                         │  Output: Order + Conviction + Reasoning (JSON)
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ Stage 3: Report │  Executive summary for dashboard
└─────────────────┘
```

## Stage 1 — Analyst

**Task:** Convert raw news headlines into a sentiment score.

| Output Field | Type | Range |
|-------------|------|-------|
| `score` | int | 0 (bearish) → 100 (bullish) |
| `reason` | str | One sentence |

Tickers scoring below 60 are eliminated — they never reach the Manager.

## Stage 2 — Portfolio Manager

**Task:** Final execution decision with full context.

**Inputs:**
- Analyst sentiment report
- Technical indicators from Sentinel (price levels, ATR)
- Current portfolio state (open positions, cash balance)
- Historical intelligence logs (last N scans — temporal memory)

**Temporal Reasoning Protocol:**
- Check if current sentiment **accelerates** or **reverses** the prior trend
- If news contradicts the technical thesis → prioritize most recent, justify the shift
- Historical memory prevents acting on stale stories already priced in

**Output JSON:**
```json
{
    "Order": "BUY | SELL | HOLD",
    "Conviction": 0.85,
    "Reasoning": "Synthesis of sentiment trend and technical levels."
}
```

## Conviction Scoring

| Range | Meaning | Typical Action |
|-------|---------|----------------|
| 0.0 – 0.3 | Low confidence | HOLD, no action |
| 0.4 – 0.6 | Moderate | Small buy or partial sell |
| 0.7 – 1.0 | High | Strong BUY, full position sizing |

Conviction flows directly into Guardian's position sizing formula.

## Backends

| Mode | Model | Speed | Notes |
|------|-------|-------|-------|
| `gemini` | gemini-2.5-flash | ~2 min/cycle | Default production mode |
| `local` | Ollama DeepSeek-R1 | ~20-30 min/cycle | Offline fallback |

Hot-switchable at runtime via dashboard toggle — no restart needed.

## Reliability

- **Temperature:** Always `0.1` — low variance, consistent JSON output
- **JSON parsing:** Regex cleaning strips `<think>` blocks and markdown fences
- **Retry:** If Manager fails to produce valid JSON, sends a minimal retry prompt
- **Default to HOLD:** If all parsing fails → `{"Order": "HOLD", "Conviction": 0.0}` — capital protected

## Configuration

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google AI API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` |
| `BRAIN_MODE` | `gemini` or `local` (hot-switchable) |
| `TEMPERATURE` | Fixed at `0.1` |
