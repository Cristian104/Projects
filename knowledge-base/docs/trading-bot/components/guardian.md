# Guardian — Risk Engine

**File:** `app/trading/guardian.py`

Guardian is the sole exit authority. No other component can close or partially sell a position. It runs every 5 minutes (between full cycles) via a standalone pass, evaluating all open positions against the Exit Matrix.

## Position Sizing

Before entering a trade, Guardian calculates how much capital to deploy:

$$\text{Position Size (PLN)} = \frac{\text{Total Capital} \times 0.02 \times \text{Conviction}}{ATR \times Multiplier}$$

| Factor | Value | Meaning |
|--------|-------|---------|
| Max portfolio risk | 2% | Maximum capital at risk per trade |
| Conviction | 0.0–1.0 | From QuantBrain — scales position up/down |
| ATR | Calculated | Current volatility — higher ATR = smaller position |
| Concentration cap | 15% | Hard maximum: no single position > 15% of portfolio |

**Effect:** High conviction on low-volatility = larger position. High conviction on high-volatility = smaller, safer position.

## ATR Calculation

Standard Average True Range with N=12 period:

$$TR = \max[(H - L),\ |H - C_{prev}|,\ |L - C_{prev}|]$$
$$ATR = \text{RollingMean}(TR,\ 12)$$

**Initial Risk (R):** `Entry ATR × Multiplier` — defined at entry, used as the unit for profit tiers.

## Exit Matrix

Evaluated in strict priority order every 5 minutes:

| Priority | Rule | Trigger | Action |
|----------|------|---------|--------|
| 1 | **Trailing Stop** | `current_price ≤ highest_price − (current_ATR × multiplier)` | `SELL_ALL` |
| 2 | **Time Decay** | `hours_held ≥ threshold` AND `current_price < entry_price` | `SELL_ALL` |
| 3 | **Tier 1 Profit** | `current_price ≥ entry_price + 1R` AND `tier == 0` | `SELL_PARTIAL_30%` |
| 4 | **Tier 2 Profit** | `current_price ≥ entry_price + 2R` AND `tier == 1` | `SELL_PARTIAL_30%` |
| 5 | **Moonshot** | None of the above | `HOLD` (remaining 40%) |

!!! note "The Moonshot"
    After two partial sells, 40% of the position remains. It rides the trend indefinitely until the Trailing Stop fires.

## Example Scenarios

| Scenario | Movement | Action |
|----------|---------|--------|
| Flash crash | Price drops 5%, crosses ATR stop | `SELL_ALL` — Trailing Stop |
| Slow bleed | -1% below entry for 48h | `SELL_ALL` — Time Decay |
| Breakout | Price hits Entry + 1R | `SELL_PARTIAL_30%` — Tier 1 |
| Moonshot | Hits Tier 1 → Tier 2 → keeps running | `SELL_30%` → `SELL_30%` → `HOLD` 40% |

## Database Fields

**Read each cycle:**

| Field | Description |
|-------|-------------|
| `entry_price` | Execution price from T212 |
| `highest_price` | Peak price since entry (updated live) |
| `entry_atr` | ATR at time of BUY signal |
| `tier` | Current profit ladder level (0, 1, 2) |
| `timestamp` | Entry time — used to calculate `hours_held` |

**Written on exit:**

| Field | Update |
|-------|--------|
| `tier` | Incremented on partial sells |
| `status` | Set to `CLOSED` on full exit |

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ATR_TRAILING_MULTIPLIER` | 3.0 | Trailing stop sensitivity |
| `ATR_TIME_DECAY_HOURS` | 48 | Max hours to hold an underwater position |
| `MAX_PORTFOLIO_RISK` | 0.02 | % of capital at risk per trade |
| `CONCENTRATION_CAP` | 0.15 | Max single position as % of portfolio |
| `ATR_PERIOD` | 12 | Lookback for ATR calculation |
