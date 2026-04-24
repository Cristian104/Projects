from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "The Remastered Bot"

    # Database
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "remastered_db"
    DB_PORT: int = 5432
    DB_NAME: str

    # AI Brain
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    BRAIN_MODE: str = "api"   # "api" — Gemini; overridden by DB at runtime

    # Trading 212 Credentials
    T212_API_KEY: str
    T212_BASE_URL: str = "https://demo.trading212.com/api/v0"

    # Modes & Telegram
    TRADING_MODE: str = "CFD"
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def LEVERAGE(self) -> float:
        return 5.0 if self.TRADING_MODE == "CFD" else 1.0

    @property
    def DYNAMIC_STOP_LOSS(self) -> float:
        return 0.08 / self.LEVERAGE

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MARKET_HOLIDAYS: list = [
        "2026-01-01", "2026-01-19", "2026-02-16",
        "2026-04-03", "2026-05-25", "2026-06-19",
        "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25"
    ]
    COMPANY_MAP: dict = {
        "SAP.DE": "SAP SE stock news",
        "SIE.DE": "Siemens AG financial news",
        "NVDA": "NVIDIA Corporation stock news",
        "TSLA": "Tesla Inc stock news",
        "PLTR": "Palantir Technologies news"
    }

    # ── Guardian exit matrix ───────────────────────────────────────────────────
    ATR_PERIOD: int = 10                  # Kaufman 2013: optimal for 1-5d equity holds
    ATR_TRAILING_MULTIPLIER: float = 3.0  # Chandelier Exit (LeBeau): highest_price - N×ATR
    ATR_TIME_DECAY_HOURS: float = 4.0     # exit flat/underwater positions after N hours
    HARD_STOP_PCT: float = 0.025          # -2.5% hard stop from entry (Van Tharp)
    BREAKEVEN_ACTIVATION_R: float = 1.5   # raise stop to breakeven after 1.5R profit
    TIER1_TARGET_R: float = 2.0           # first partial exit at +2R
    TIER2_TARGET_R: float = 3.0           # second partial exit at +3R
    TIER1_SELL_PCT: float = 0.50          # sell 50% at Tier 1
    TIER2_SELL_PCT: float = 0.50          # sell remaining 50% at Tier 2

    # ── Regime & volatility filters ───────────────────────────────────────────
    REGIME_FILTER_ENABLED: bool = True    # gate entries on broad market trend
    REGIME_SMA_PERIOD: int = 50
    REGIME_FILTER_TOLERANCE: float = 0.15 # allow entries up to 15% below SMA (widened from 8%)
    VIX_PAUSE_THRESHOLD: float = 30.0
    VSTOXX_PAUSE_THRESHOLD: float = 30.0

    # ── 4-state regime classifier (Phase 3) ───────────────────────────────────
    REGIME_CLASSIFIER_ENABLED: bool = True
    # position_size_multipliers per state: trending_up / ranging / volatile / trending_down
    REGIME_MULTIPLIER_TRENDING_UP: float = 1.0
    REGIME_MULTIPLIER_RANGING: float = 0.6
    REGIME_MULTIPLIER_VOLATILE: float = 0.5
    REGIME_MULTIPLIER_TRENDING_DOWN: float = 0.0  # block entries in confirmed downtrend

    # ── Entry controls ────────────────────────────────────────────────────────
    MIN_BUY_CONVICTION: float = 0.50      # lowered from 0.65 — AI conviction floor was too strict
    MAX_POSITION_PCT: float = 0.08        # fallback cap (overridden by vol-scaled caps below)
    MAX_POSITION_PCT_HIGH_VOL: float = 0.05   # Phase 4: cap for ATR/price > 2.5%
    MAX_POSITION_PCT_LOW_VOL: float = 0.12    # Phase 4: cap for ATR/price <= 2.5%
    RISK_PER_TRADE_PCT: float = 0.015         # Phase 4: risk 1.5% of capital per trade
    MAX_CONCURRENT_POSITIONS: int = 10
    MAX_POSITIONS_PER_SECTOR: int = 2
    MAX_CAPITAL_DEPLOYED_PCT: float = 0.65
    ADX_THRESHOLD: float = 25.0
    ADX_ENABLED: bool = False             # disabled — technical signal gate replaces this
    LIQUIDITY_FLOOR_EU: float = 500_000
    LIQUIDITY_FLOOR_US: float = 1_000_000

    # ── Technical signal gate (Phase 2) ───────────────────────────────────────
    # SENTIMENT_ROLE: "gate" = old behaviour (hard gate), "confirmatory" = adjusts conviction only
    SENTIMENT_ROLE: str = "confirmatory"
    SENTIMENT_GATE_THRESHOLD: int = 55    # used when SENTIMENT_ROLE == "gate"
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9

    # ── Session time filters ──────────────────────────────────────────────────
    AVOID_MONDAY_OPEN_MINUTES: int = 90
    AVOID_FRIDAY_CLOSE_HOUR: int = 16

    # ── Brain reliability ─────────────────────────────────────────────────────
    BRAIN_JSON_RETRY: bool = True

settings = Settings()
