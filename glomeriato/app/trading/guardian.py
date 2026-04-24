import pandas as pd
import numpy as np
from loguru import logger
from app.core.config import settings

class Guardian:
    def __init__(self):
        self.atr_period = settings.ATR_PERIOD          # 10 (Kaufman 2013)
        self.atr_multiplier = settings.ATR_TRAILING_MULTIPLIER  # 3.0 Chandelier Exit
        self.time_decay_hours = settings.ATR_TIME_DECAY_HOURS
        self.max_portfolio_risk = 0.02

    def calculate_atr(self, df: pd.DataFrame) -> float:
        """Calculates the Average True Range (ATR) over the configured N period."""
        if len(df) < self.atr_period:
            return 0.0

        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=self.atr_period).mean().iloc[-1]

    def calculate_position_size(self, conviction: float, capital: float, current_price: float,
                               atr: float, regime_multiplier: float = 1.0) -> float:
        """
        Phase 3+4: Volatility-scaled position sizing with regime multiplier.

        Uses ATR/price ratio to determine whether this is a high-vol or low-vol asset,
        then applies an appropriate cap. The regime_multiplier (0.0–1.0) from the regime
        classifier scales the final size down in choppy/trending-down markets.
        """
        if atr == 0 or current_price == 0:
            return 0.0

        risk_per_share = atr * self.atr_multiplier
        risk_budget = capital * settings.RISK_PER_TRADE_PCT * conviction
        shares = risk_budget / risk_per_share
        investment_value = shares * current_price

        # Phase 4: volatility-tiered cap — high-vol stocks get tighter limit
        relative_atr = atr / current_price
        if relative_atr > 0.025:
            dynamic_cap = capital * settings.MAX_POSITION_PCT_HIGH_VOL
        else:
            dynamic_cap = capital * settings.MAX_POSITION_PCT_LOW_VOL

        sized = min(investment_value, dynamic_cap)

        # Phase 3: scale down in unfavourable regimes
        return sized * regime_multiplier

    def evaluate_position(self, current_price: float, entry_price: float, highest_price: float,
                          entry_atr: float, current_atr: float, hours_held: float, tier: int) -> dict:
        """
        Executes the Exit Matrix — evaluated in priority order:
          0. Hard Stop Loss          — -2.5% from entry (caps catastrophic losses)
          1. Breakeven-Plus Stop     — after +1.5R, trail stop rises to entry + round-trip cost
          2. Chandelier Trailing Stop — highest_price − 3×ATR (LeBeau)
          3. Time-Decay Exit         — flat/underwater position after 4h → dead money exit
          4. Tier 1 Profit           — +2R → SELL 50%
          5. Tier 2 Profit           — +3R → SELL remaining 50%
          6. HOLD
        """
        initial_risk_r = entry_atr * self.atr_multiplier
        hard_stop_pct = settings.HARD_STOP_PCT              # 0.025
        breakeven_r    = settings.BREAKEVEN_ACTIVATION_R    # 1.5
        tier1_r        = settings.TIER1_TARGET_R            # 2.0
        tier2_r        = settings.TIER2_TARGET_R            # 3.0
        fx_round_trip  = 0.003                              # 0.15% × 2 sides

        # 0. Hard Stop Loss — absolute floor, no exceptions
        hard_stop_price = entry_price * (1 - hard_stop_pct)
        if current_price <= hard_stop_price:
            logger.warning(
                f"🚨 Guardian: Hard Stop hit. "
                f"Price {current_price:.4f} ≤ floor {hard_stop_price:.4f} "
                f"({hard_stop_pct*100:.1f}% below entry)"
            )
            return {"action": "SELL_ALL", "reason": f"Hard Stop -{hard_stop_pct*100:.1f}%", "new_tier": tier}

        # 1. Breakeven-Plus Stop — once we've hit 1.5R, the worst outcome becomes a tiny gain
        if initial_risk_r > 0:
            breakeven_trigger = entry_price + (breakeven_r * initial_risk_r)
            if highest_price >= breakeven_trigger:
                breakeven_floor = entry_price * (1 + fx_round_trip)
                if current_price <= breakeven_floor:
                    logger.info(
                        f"🔐 Guardian: Breakeven stop triggered. "
                        f"Price {current_price:.4f} fell below breakeven floor {breakeven_floor:.4f}"
                    )
                    return {"action": "SELL_ALL", "reason": "Breakeven Stop — Protecting Round-Trip Cost", "new_tier": tier}

        # 2. Chandelier Trailing Stop (Volatility-Adjusted)
        trailing_stop = highest_price - (current_atr * self.atr_multiplier)
        if current_price <= trailing_stop:
            logger.warning(
                f"🛡️ Guardian: Chandelier Stop hit. "
                f"Price {current_price:.4f} ≤ trail {trailing_stop:.4f} "
                f"(peak {highest_price:.4f} − {self.atr_multiplier}×ATR)"
            )
            return {"action": "SELL_ALL", "reason": "Chandelier Trailing Stop", "new_tier": tier}

        # 3. Time-Decay Exit (Dead Money Rule)
        # Exit if position is flat (gain < 0.5×ATR) OR underwater after the decay threshold
        if hours_held >= self.time_decay_hours:
            gain = current_price - entry_price
            flat_threshold = 0.5 * current_atr
            if gain < flat_threshold:
                logger.warning(
                    f"⏳ Guardian: Time-Decay exit. "
                    f"Gain {gain:.4f} < 0.5×ATR ({flat_threshold:.4f}) after {hours_held:.1f}h — dead money."
                )
                return {"action": "SELL_ALL", "reason": "Time-Decay — Dead Money", "new_tier": tier}

        # 4. Tier 1 Profit — sell 50% at +2R
        profit_target_1 = entry_price + (tier1_r * initial_risk_r)
        if current_price >= profit_target_1 and tier == 0:
            logger.success(
                f"💰 Guardian: Tier 1 (+{tier1_r}R) reached. Selling {settings.TIER1_SELL_PCT*100:.0f}% to lock profit."
            )
            return {"action": "SELL_PARTIAL", "reason": f"Tier 1 Profit +{tier1_r}R", "new_tier": 1,
                    "sell_pct": settings.TIER1_SELL_PCT}

        # 5. Tier 2 Profit — sell remaining 50% at +3R
        profit_target_2 = entry_price + (tier2_r * initial_risk_r)
        if current_price >= profit_target_2 and tier == 1:
            logger.success(
                f"💰 Guardian: Tier 2 (+{tier2_r}R) reached. Selling remaining {settings.TIER2_SELL_PCT*100:.0f}%."
            )
            return {"action": "SELL_PARTIAL", "reason": f"Tier 2 Profit +{tier2_r}R", "new_tier": 2,
                    "sell_pct": settings.TIER2_SELL_PCT}

        # 6. HOLD
        return {"action": "HOLD", "reason": "Within safe parameters", "new_tier": tier}
