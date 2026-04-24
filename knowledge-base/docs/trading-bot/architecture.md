# Core Components

This documentation covers the three pillars of the Glomeriato trading system: **Sentinel**, **QuantBrain**, and **Guardian**. They work in a unified pipeline to identify opportunities, validate with AI, and manage risk.

---

## 🔄 System Interaction Flow

```
Sentinel.screen_universe()
    │  Filters 500+ tickers → top 10 by urgency score
    ▼
QuantBrain.triage_sentiment()
    │  News sentiment triage for top candidates
    ▼
QuantBrain.execute_decision()
    │  Combines news + technicals + history → BUY/HOLD
    ▼
Guardian.calculate_position_size()
    │  ATR volatility + AI conviction → PLN budget
    ▼
Guardian.evaluate_position()  ← runs every cycle
    │  Exit Matrix: trailing stop, time decay, profit tiers
    ▼
Order execution
```

---

## 🛰️ Sentinel
**File:** `app/trading/sentinel.py`

High-speed technical scanner. Filters the full ticker universe down to a high-probability shortlist.

### Hard Filters

| Filter | Rule |
|--------|------|
| Liquidity | Daily turnover ≥ $500k |
| Price range | $2.00 – $1,500.00 |
| Market cap | ≥ $100M |
| Volatility ceiling | Annualized volatility ≤ 150% |

### Scoring

- **Urgency Score:** `(Volume-Weighted Momentum) × (Volatility Expansion)` — higher = imminent breakout
- **Mean Reversion:** Assets >2 standard deviations from 20-day SMA with volume exhaustion on 5m timeframe

### Output

Returns top 10 "Urgency" candidates + any "Mean Reversion" triggers.

---

## 🧠 QuantBrain
**File:** `app/intelligence/brain.py`

Dual-agent AI decision engine. Synthesizes market sentiment with technical data and historical memory.

### Three-Stage Process

**Stage 1 — Analyst**

- Task: Rapid sentiment triage
- Input: Raw RSS headlines
- Output: Sentiment score (0–100) + single-sentence rationale

**Stage 2 — Portfolio Manager**

- Task: Final execution decision
- Input: Analyst report + technical levels + portfolio state + historical memory
- Uses **Temporal Reasoning** to check if current trends confirm or conflict with past history
- Output: Strict JSON — `Order` (BUY/SELL/HOLD), `Conviction` (0.0–1.0), `Reasoning`

**Stage 3 — Market Summary**

- Post-cycle synthesis
- Produces Markdown summary of the last 30 minutes for the dashboard

### Configuration

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Model name (e.g. `gemini-2.5-flash`) |
| `TEMPERATURE` | Always `0.1` — kept low for logical consistency |

---

## 🛡️ Guardian
**File:** `app/trading/guardian.py`

Risk engine and sole exit authority. Manages position sizing and runs the exit matrix every cycle.

### Dynamic Position Sizing

- **Base risk:** Max 2% of portfolio value per trade
- **Scaling:** Budget scaled by QuantBrain conviction score
- **Hard cap:** No single position > 15% of total portfolio

### Exit Matrix

| Rule | Trigger | Action |
|------|---------|--------|
| Trailing Stop | Price ≤ `Highest_Price − (ATR × Multiplier)` | `SELL_ALL` |
| Time Decay | Held > N hours while in a loss | `SELL_ALL` |
| Tier 1 Profit | Price reaches `Entry + 1R` | `SELL_PARTIAL_30` |
| Tier 2 Profit | Price reaches `Entry + 2R` | `SELL_PARTIAL_30` |
| Moonshot | Within safe parameters | `HOLD` (remaining 40%) |

---

## ⚙️ Key Configuration Parameters

| Parameter | Default | Component | Description |
|-----------|---------|-----------|-------------|
| `ATR_TRAILING_MULTIPLIER` | 3.0 | Guardian | Trailing stop sensitivity |
| `ATR_TIME_DECAY_HOURS` | 48 | Guardian | Max hours to hold an underwater position |
| `MAX_PORTFOLIO_RISK` | 0.02 | Guardian | % of capital at risk per trade |
| `LIQUIDITY_THRESHOLD` | 500,000 | Sentinel | Min daily turnover |
| `TEMPERATURE` | 0.1 | Brain | LLM temperature (always fixed) |
