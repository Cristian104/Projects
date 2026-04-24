I will first locate the configuration file to ensure I have the full context of the `Settings` class and its current location.

I will read the configuration file to confirm its current contents and identify where to integrate the new `REGIME_FILTER_TOLERANCE` parameter.

I'll add the `REGIME_FILTER_TOLERANCE` parameter to the `Settings` class in `app/core/config.py` and then generate the requested configuration reference.

I'll now generate the configuration reference as requested, including the updated `REGIME_FILTER_TOLERANCE` parameter in the "Entry Controls" section.

### Configuration Reference

| Name | Type | Default | Description | When to tune |
| :--- | :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | `str` | "The Remastered Bot" | Project identifier for logs/metadata. | Change for organizational purposes. |
| `DB_USER` | `str` | *Required* | PostgreSQL username. | Always provided in environment secrets. |
| `DB_PASSWORD` | `str` | *Required* | PostgreSQL password. | Always provided in environment secrets. |
| `DB_HOST` | `str` | "remastered_db" | Database host (Docker service name). | If running outside Docker or custom network. |
| `DB_PORT` | `int` | 5432 | Database connection port. | If using non-standard DB port. |
| `DB_NAME` | `str` | *Required* | Name of the database schema. | Always provided in environment secrets. |
| `GEMINI_API_KEY` | `str` | "" | Google Gemini API key. | Required for AI brain functionality. |
| `GEMINI_MODEL` | `str` | "gemini-2.5-flash" | AI model version to use. | If upgrading or testing different models. |
| `BRAIN_MODE` | `str` | "api" | Primary intelligence source (can be "api" or "local"). | When switching to/from local DeepSeek/Ollama. |
| `T212_API_KEY` | `str` | *Required* | Trading 212 API Key. | Generated in your T212 account. |
| `T212_SECRET_KEY` | `str` | *Required* | Trading 212 Secret Key. | Generated in your T212 account. |
| `T212_BASE_URL` | `str` | "https://demo..." | API endpoint URL (Live vs. Practice). | To switch between Demo and Live trading. |
| `TRADING_MODE` | `str` | "CFD" | Trading instrument type ("CFD" or "Invest"). | To adjust leverage and tax treatment. |
| `TELEGRAM_BOT_TOKEN`| `str` | *Required* | Telegram Bot API token. | For remote notification/monitoring. |
| `TELEGRAM_CHAT_ID` | `str` | *Required* | Target chat ID for bot messages. | To target specific users or channels. |
| `MARKET_HOLIDAYS` | `list`| *List of dates* | Dates where the bot pauses execution. | Update annually for correct trading days. |
| `COMPANY_MAP` | `dict` | *JSON object* | Mapping of tickers to context descriptions. | When adding/modifying the trading universe. |
| `ATR_TRAILING_MULTIPLIER` | `float` | 6.0 | Multiplier for the ATR-based stop loss. | If stop losses are too tight or too loose. |
| `ATR_TIME_DECAY_HOURS` | `float` | 6.0 | Threshold to exit stale/flat trades. | Increase for longer swings; decrease for day trades. |
| `REGIME_FILTER_ENABLED`| `bool` | True | Global "risk-on/off" switch for new buys. | If the bot should ignore broader market trends. |
| `REGIME_FILTER_TOLERANCE`| `float` | 0.005 | Percentage (0.5%) price can be below SMA50. | To allow for small noise near the SMA level. |
| `MAX_CONCURRENT_POSITIONS`| `int` | 8 | Limit on total open trades. | To manage capital spread and risk density. |
| `MAX_CAPITAL_DEPLOYED_PCT`| `float` | 0.80 | Max % of balance allowed in active risk. | To ensure a cash buffer is always maintained. |
| `MIN_BUY_CONVICTION` | `float` | 0.65 | Minimum AI confidence score to enter. | If the bot is taking too many low-quality trades. |
| `MAX_POSITION_PCT` | `float` | 0.08 | Max % of balance per individual trade. | To limit single-asset catastrophic risk. |
| `BRAIN_JSON_RETRY` | `bool` | True | Auto-retry AI if output parsing fails. | If experiencing frequent API formatting errors. |

---

### Configuration Category Overview

#### Database
Manages the persistent layer for position tracking, audit logs, and AI intelligence history. These settings ensure the FastAPI backend can reliably communicate with the PostgreSQL instance.

#### AI Brain
Defines the bot's decision-making core. It allows switching between hosted models (Gemini) and local LLMs (via Ollama) while controlling retry logic for high-reliability JSON parsing.

#### Trading 212
Handles authentication and connectivity to the broker. These settings determine whether the bot operates in the Sandbox/Practice environment or executes real trades in the Live environment.

#### Entry Controls
The "Gatekeeper" of the system. This group controls risk density (max positions), capital management (deployed percentage), and broad market sentiment (Regime Filter). 
- **REGIME_FILTER_TOLERANCE**: Provides a buffer for the 50-day SMA check, preventing "sawing" (rapid enabling/disabling) when the index price is oscillating directly on the moving average.

#### Exit Controls
Focuses on individual position maintenance. This includes the logic for partial sells (profit ladders) and general stop-loss calculations based on the instrument type and account leverage.

#### Guardian Matrix (Exit Risk)
The core of the "Transatlantic Snowball" risk engine. It uses Volatility (ATR) and Time (Decay) to manage exits. 
- **ATR Trailing**: Adjusts dynamic exits based on market volatility, protecting capital during reversals while giving trades "room to breathe" during low-volatility climbs.
- **Time Decay**: Prevents capital from being locked in stagnant assets that fail to reach profit targets within the expected timeframe.
