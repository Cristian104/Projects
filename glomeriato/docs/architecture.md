# Glomeriato V2.1 — Technical Documentation
**Project Title:** Glomeriato V2.1 (The Transatlantic Snowball)  
**System Type:** Autonomous Algorithmic Trading Bot  
**Target Platform:** Trading 212 (Invest & CFD)  

---

# 1. SYSTEM OVERVIEW
Glomeriato V2.1 is an advanced autonomous trading system designed to synthesize high-frequency technical analysis with deep-reasoning AI sentiment. Unlike traditional bots that rely on static indicators, Glomeriato employs a **dual-agent AI brain** (DeepSeek-R1/Gemini) to interpret market news and technical triggers within a regime-aware framework.

### Design Philosophy
- **Risk-First Execution:** No trade is placed without a volatility-adjusted exit plan (Guardian).
- **Temporal Memory:** The system queries its own historical decisions to ensure consistency and learn from past cycles.
- **Financial Integrity:** Native accounting for the **0.15% T212 FX conversion fee** in every calculation.
- **Argos Loop:** An autonomous self-improvement pipeline that updates the bot’s ticker universe and parameters weekly based on macro-regime shifts.

---

# 2. COMPONENT REFERENCE

| Component | Purpose | Key Methods | Writes to DB |
| :--- | :--- | :--- | :--- |
| **Guardian** | Executes the Exit Matrix and dynamic position sizing. | `calculate_atr`, `evaluate_position`, `calculate_position_size` | `active_positions` (updates) |
| **Sentinel** | High-speed technical scanner and liquidity filter. | `screen_universe`, `calculate_urgency`, `check_mean_reversion` | None (ReadOnly) |
| **Brain** | Dual-agent (Analyst/Manager) AI sentiment synthesis. | `get_sentiment_score`, `generate_order_logic` | `intelligence_logs` |
| **Strategy** | Orchestrates the 30-minute cycle loop and execution. | `sync_reality`, `execute_cycle`, `place_orders` | `transaction_history`, `market_summaries` |
| **Config** | Centralized Pydantic-based settings and environment management. | `Settings` class | None |
| **Memory** | Synchronous PostgreSQL (psycopg2) interface. | `DBManager`, `get_ticker_history`, `update_highest_price` | All tables |
| **T212 Connector**| Interface for Trading 212 REST API and ticker mapping. | `place_order`, `get_portfolio`, `_load_mappings` | None |
| **Argos** | Autonomous weekly optimizer and research agent. | `filter_imminent_earnings`, `detect_market_regime` | `targets.json`, `argos_experiments` |

---

# 3. CONFIGURATION REFERENCE

| Name | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `TRADING_MODE` | `str` | `"CFD"` | Determines leverage (5.0 for CFD, 1.0 for Invest). |
| `ATR_TRAILING_MULTIPLIER` | `float` | `6.0` | Multiplier for the ATR-based trailing stop (Initial Risk R). |
| `ATR_TIME_DECAY_HOURS` | `float` | `6.0` | Hours to hold a losing position before "Dead Money" exit. |
| `MIN_BUY_CONVICTION` | `float` | `0.65` | Minimum Manager score (0.0-1.0) required to BUY. |
| `MAX_CAPITAL_DEPLOYED_PCT`| `float` | `0.80` | Safety ceiling; halts new entries if >80% capital is used. |
| `MAX_POSITION_PCT` | `float` | `0.08` | Maximum allocation for a single ticker (8% of balance). |
| `REGIME_FILTER_ENABLED` | `bool` | `True` | Requires broad market index > 50d SMA for new BUYs. |
| `BRAIN_MODE` | `str` | `"api"` | Switches between local Ollama (DeepSeek) or Google Gemini API. |

---

# 4. GUARDIAN EXIT MATRIX
The Guardian evaluates open positions every 30 minutes following this strict priority tree:

1.  **Trailing Stop:** 
    - *Condition:* `Price <= (Highest_Price_Since_Entry - (Current_ATR * 6.0))`
    - *Action:* `SELL_ALL`
2.  **Time-Decay (Dead Money):**
    - *Condition:* `Hours_Held >= 6.0` AND `(Current_Price - Entry_Price) < 0`
    - *Action:* `SELL_ALL`
3.  **Tier 1 Profit Ladder:**
    - *Condition:* `Price >= (Entry_Price + 1.0 * Initial_Risk_R)` AND `Tier == 0`
    - *Action:* `SELL_PARTIAL_30%`, `Set Tier = 1`
4.  **Tier 2 Profit Ladder:**
    - *Condition:* `Price >= (Entry_Price + 2.0 * Initial_Risk_R)` AND `Tier == 1`
    - *Action:* `SELL_PARTIAL_30%`, `Set Tier = 2`
5.  **Moonshot Hold:**
    - *Condition:* No criteria met.
    - *Action:* `HOLD` (Let the remaining 40% ride the trend).

---

# 5. SENTINEL SCORING
Sentinel screens the `targets.json` universe for liquidity and volatility before passing candidates to the Brain.

**Hard Filters:**
- Liquidity: `Price * Volume > 500,000` (USD/PLN)
- Price: `$2.00 <= Price <= $1,500.00`
- Volatility: `Annualized Volatility <= 150%`

**Urgency Scoring Formula:**
$$Urgency = (VolumeWeightedMomentum) \times (VolatilityExpansion)$$
- **VW-Momentum:** 5-day rolling average of `Log(Returns) * (Volume / Avg_Volume)`.
- **Volatility Expansion:** `(Current_Day_Range / Open_Price) / Annualized_Hist_Vol`.

---

# 6. ARGOS SELF-IMPROVEMENT PIPELINE
Argos runs every Sunday at 08:00 UTC to adapt the bot to the upcoming week's market regime.

1.  **Macro Research:** Uses Perplexity Sonar-Pro to identify high-alpha sectors and upcoming earnings.
2.  **Blackout Filtering:** Automatically removes tickers from `targets.json` that have earnings releases within the next 48 hours.
3.  **Regime Detection:** Performs K-Means clustering on SPY/Sector ETFs (RSI, ATR, MACD) to determine the current market cluster (0-3).
4.  **Parameter Injection:** Rewrites `targets.json` and injects updated ATR multipliers or position-sizing fractions into the system via `argos_experiments`.
5.  **Deployment:** Triggers `./relaunch.sh` to apply changes before Monday market open.

---

# 7. DATA FLOW

```text
[ targets.json ] 
       |
[ Sentinel Scan ] ----> (Liquidity/Urgency Filter) ----> [ Top 10 Candidates ]
                                                               |
[ Brain (Analyst) ] <--- (RSS News Feeds) ---------------------+
       |
[ Brain (Manager) ] <--- (Technical Data + Temporal Memory from DB)
       |
[ Strategy Logic ] ----> (Check Balance / FX Fees / Regime)
       |
[ T212 Connector ] ----> (Place Order via API)
       |
[ DB (Memory) ] <------- (Update active_positions & intelligence_logs)
```

---

# 8. KNOWN ISSUES & TECHNICAL DEBT
- **Telegram Notifications:** `app/connectors/telegram.py` is present but not integrated into the `strategy.py` loop.
- **Async Mismatch:** Project includes `asyncpg` and `SQLAlchemy` but uses synchronous `psycopg2` for all database operations.
- **Graceful Shutdown:** No SIGTERM handling; Docker kills can lead to uncommitted logs or dangling DB connections.
- **Rounding:** Polish (.WA) and Spanish (.MC) markets require integer share quantities; the bot handles these specifically but relies on ticker suffixes for detection.

---

# 9. OPERATIONS GUIDE

### Basic Management
- **Full Relaunch:** `./relaunch.sh` (Stages files, rebuilds containers, and starts system).
- **Hard Reset:** `./fresh_start.sh` (Wipes active positions and logs for a clean demo account start).
- **Monitoring:** `docker logs -f bot_official` for real-time trade logic.

### Troubleshooting Ticker Mapping
If the bot "sees" an opportunity but fails to execute:
1. Check `app/data/ticker_map.json` to ensure the Yahoo ticker (e.g., `AAPL`) is mapped to a T212 ID (e.g., `AAPL_US_EQ`).
2. Run `python scripts/discover_tickers.py` to refresh the mapping if IDs have changed.

### Manual Dashboard
Run `streamlit run app/dashboard.py` to view the Institutional Intelligence Dashboard, PnL tracking, and AI reasoning logs.
