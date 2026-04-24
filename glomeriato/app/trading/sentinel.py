import yfinance as yf
import pandas as pd
import numpy as np
from loguru import logger
from app.core.config import settings


class Sentinel:
    def __init__(self):
        self.lookback = 20

    def _fetch_data(self, ticker: str):
        """
        Fetches multi-timeframe market data with 404 and delisting protection.
        Returns: (df_daily, df_5m, info)
        """
        try:
            t_obj = yf.Ticker(ticker)

            # 1. Daily Data for Technicals and Urgency
            df_d = t_obj.history(period="3mo", interval="1d")
            if df_d.empty:
                logger.warning(f"⚠️ {ticker} returned no daily data. Possible delisting.")
                return None, None, None

            if not df_d.empty and isinstance(df_d.columns, pd.MultiIndex):
                df_d.columns = df_d.columns.get_level_values(0)

            # 2. Intraday Data (5m) for Mean Reversion Volume Exhaustion
            df_5m = t_obj.history(period="1d", interval="5m")
            if df_5m is not None and not df_5m.empty and isinstance(df_5m.columns, pd.MultiIndex):
                df_5m.columns = df_5m.columns.get_level_values(0)

            # 3. Basic Info for Hard Filters
            info = {}
            try:
                info = t_obj.info
            except:
                pass

            return df_d, df_5m, info
        except Exception as e:
            if "404" in str(e) or "No data found" in str(e):
                logger.error(f"🚫 Sentinel: {ticker} appears delisted or invalid. Skipping.")
            else:
                logger.error(f"❌ Sentinel error on {ticker}: {e}")
            return None, None, None

    def apply_hard_filters(self, df_daily: pd.DataFrame, info: dict, region: str = "USA") -> bool:
        """Discard low-liquidity or extreme-volatility outliers."""
        if df_daily is None or df_daily.empty or len(df_daily) < self.lookback:
            return False

        current_close = df_daily['Close'].iloc[-1]
        current_vol = df_daily['Volume'].iloc[-1]

        # 1. Liquidity Filter — region-specific floors (Karpoff 1987)
        #    EU markets trade thinner; US floor is higher for execution quality
        liquidity_floor = (settings.LIQUIDITY_FLOOR_EU if region == "EUROPE"
                           else settings.LIQUIDITY_FLOOR_US)
        if (current_close * current_vol) < liquidity_floor:
            return False

        # 2. Price Filter: Avoid penny stocks and ultra-expensive stocks
        if not (2.0 <= current_close <= 1500.0):
            return False

        # 3. Market Cap Filter: Avoid micro-caps
        if info:
            mcap = info.get('marketCap', 1_000_000_000)
            if mcap < 100_000_000:
                return False

        # 4. Volatility Ceiling: Avoid >150% Annualized Volatility
        log_returns = np.log(df_daily['Close'] / df_daily['Close'].shift(1))
        ann_vol = np.sqrt((log_returns ** 2).mean()) * np.sqrt(252)
        if ann_vol > 1.5:
            return False

        return True

    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average Directional Index (ADX) using Wilder's method.
        ADX > 25 indicates a trending market — required for momentum entries.
        Returns 0.0 if insufficient data.
        """
        if df is None or len(df) < period + 1:
            return 0.0
        try:
            high = df['High']
            low = df['Low']
            close = df['Close']

            # True Range
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)

            # +DM and -DM
            up_move = high.diff()
            down_move = -low.diff()
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

            # Wilder smoothed ATR, +DI, -DI
            atr_s = pd.Series(tr).ewm(alpha=1 / period, adjust=False).mean()
            plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1 / period, adjust=False).mean() / (atr_s + 1e-9)
            minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1 / period, adjust=False).mean() / (atr_s + 1e-9)

            # DX and ADX
            dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
            adx = dx.ewm(alpha=1 / period, adjust=False).mean()
            return float(adx.iloc[-1])
        except Exception as e:
            logger.debug(f"ADX calculation error: {e}")
            return 0.0

    def calculate_urgency(self, df_daily: pd.DataFrame) -> float:
        """
        Urgency = (Volume-Weighted Momentum) × (Volatility Expansion).
        High urgency suggests an imminent breakout.
        """
        if df_daily is None or df_daily.empty or len(df_daily) < self.lookback:
            return 0.0

        df = df_daily.copy()
        df['LogRet'] = np.log(df['Close'] / df['Close'].shift(1))
        df['ATV'] = df['Volume'].rolling(window=self.lookback).mean()
        df['ATV'] = df['ATV'].replace(0, np.nan)
        df['Vol_Ratio'] = df['Volume'] / df['ATV']

        vw_mom = (df['LogRet'] * df['Vol_Ratio']).rolling(window=5).mean().iloc[-1]

        iv = (df['High'].iloc[-1] - df['Low'].iloc[-1]) / df['Open'].iloc[-1]
        log_returns = np.log(df['Close'] / df['Close'].shift(1))
        ann_vol = np.sqrt((log_returns ** 2).mean()) * np.sqrt(252)
        ve = iv / ann_vol if ann_vol > 0.01 else 0

        score = vw_mom * ve
        return float(score) if not np.isnan(score) else 0.0

    def check_mean_reversion(self, df_daily: pd.DataFrame, df_5m: pd.DataFrame) -> bool:
        """
        Finds stocks deviated >2 StdDev from 20-day average with volume exhaustion.
        """
        if df_daily is None or df_daily.empty or len(df_daily) < self.lookback:
            return False

        sma_20 = df_daily['Close'].rolling(window=20).mean().iloc[-1]
        std_20 = df_daily['Close'].rolling(window=20).std().iloc[-1]
        lower_band = sma_20 - (2 * std_20)
        current_price = df_daily['Close'].iloc[-1]

        extreme_deviation = current_price <= lower_band

        volume_exhaustion = True
        if df_5m is not None and not df_5m.empty:
            avg_5m_vol = df_5m['Volume'].mean()
            last_5m_vol = df_5m['Volume'].iloc[-1]
            volume_exhaustion = last_5m_vol > (1.5 * avg_5m_vol)

        return extreme_deviation and volume_exhaustion

    def screen_universe(self, tickers: list, region: str = "USA") -> dict:
        """
        Main Sentinel entrance. Filters the universe and returns:
        - urgency: top 10 momentum candidates by score (ADX-filtered)
        - reversion: mean-reversion triggers
        """
        logger.info(f"🛡️ Sentinel scanning {len(tickers)} tickers [{region}]...")
        candidates = {'urgency': [], 'reversion': []}

        for tkr in tickers:
            df_d, df_5m, info = self._fetch_data(tkr)

            if not self.apply_hard_filters(df_d, info, region=region):
                continue

            # ADX gate — only process trending stocks for momentum entries
            # (Wilder 1978: ADX > 25 = trending market; research: +5-10% win rate improvement)
            if settings.ADX_ENABLED:
                adx = self.calculate_adx(df_d)
                if adx < settings.ADX_THRESHOLD and adx > 0:
                    logger.debug(f"📊 {tkr}: ADX {adx:.1f} < {settings.ADX_THRESHOLD} — ranging market, skipping momentum entry.")
                    # Still allow mean reversion check (reversion works in ranging markets)
                    if self.check_mean_reversion(df_d, df_5m):
                        candidates['reversion'].append(tkr)
                        logger.success(f"🚨 MEAN REVERSION TRIGGERED: {tkr} (ADX {adx:.1f})")
                    continue

            # Priority 1: Mean Reversion (Deep value/Bounce plays)
            if self.check_mean_reversion(df_d, df_5m):
                candidates['reversion'].append(tkr)
                logger.success(f"🚨 MEAN REVERSION TRIGGERED: {tkr}")

            # Priority 2: Momentum Breakout (Urgency)
            urgency_score = self.calculate_urgency(df_d)
            if urgency_score > 0:
                candidates['urgency'].append({'ticker': tkr, 'score': urgency_score, 'df': df_d})

        candidates['urgency'] = sorted(candidates['urgency'], key=lambda x: x['score'], reverse=True)[:10]
        return candidates

    def calculate_technical_signal(self, df: pd.DataFrame, entry_type: str = "URGENCY") -> dict:
        """
        Phase 2: Primary entry gate based on price action.
        Returns a structured signal dict with composite confidence score.

        For URGENCY (momentum): needs MACD bullish cross + RSI 50-75 + price > SMA20
        For REVERSION: needs RSI < 35 (oversold confirmation)

        confidence: 0.0–1.0 composite of how many indicators agree.
        Falls open (NEUTRAL, confidence 0.5) if data is insufficient.
        """
        result = {"signal": "NEUTRAL", "rsi": 50.0, "macd_bullish": False,
                  "above_sma20": False, "confidence": 0.5}
        try:
            if df is None or len(df) < 30:
                return result

            close = df['Close']

            # RSI(14)
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain.iloc[-1] / (loss.iloc[-1] + 1e-9)
            rsi = float(100 - (100 / (1 + rs)))
            result["rsi"] = round(rsi, 1)

            # MACD crossover — bullish when MACD line crosses above signal in last 3 bars
            ema_fast = close.ewm(span=settings.MACD_FAST, adjust=False).mean()
            ema_slow = close.ewm(span=settings.MACD_SLOW, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=settings.MACD_SIGNAL, adjust=False).mean()
            # Bullish: MACD crossed above signal within last 3 bars
            macd_bullish = bool(
                macd_line.iloc[-1] > signal_line.iloc[-1] and
                macd_line.iloc[-3] <= signal_line.iloc[-3]
            )
            result["macd_bullish"] = macd_bullish

            # Price vs SMA20
            sma20 = float(close.rolling(20).mean().iloc[-1])
            above_sma20 = float(close.iloc[-1]) > sma20
            result["above_sma20"] = above_sma20

            if entry_type == "REVERSION":
                if rsi < 35:
                    votes = 1
                    if not above_sma20:   # reversion: being below SMA is expected
                        votes += 1
                    result["signal"] = "BUY"
                    result["confidence"] = min(0.5 + votes * 0.2, 0.9)
                else:
                    result["signal"] = "AVOID"
                    result["confidence"] = 0.2
            else:  # URGENCY / INFO
                votes = 0
                if 50 <= rsi <= 75:   votes += 1   # momentum confirmed, not extended
                if macd_bullish:      votes += 1   # trend momentum
                if above_sma20:       votes += 1   # price structure bullish

                if votes >= 2:
                    result["signal"] = "BUY"
                    result["confidence"] = 0.5 + (votes / 3) * 0.4  # 0.63–0.83
                elif votes == 1:
                    result["signal"] = "NEUTRAL"
                    result["confidence"] = 0.4
                else:
                    result["signal"] = "AVOID"
                    result["confidence"] = 0.2

        except Exception as e:
            logger.debug(f"Technical signal calculation error: {e}")

        return result

    def get_current_price(self, ticker: str):
        df, _, _ = self._fetch_data(ticker)
        return float(df['Close'].iloc[-1]) if df is not None else 0.0
