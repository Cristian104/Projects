Attempt 1 failed: You have exhausted your capacity on this model. Your quota will reset after 1s.. Retrying after 5879ms...
# Technical Documentation: Guardian Risk Engine (`app/trading/guardian.py`)

The **Guardian** module is the risk management core of the Glomeriato V2.1 system. It executes a multi-stage "Exit Matrix" designed to protect capital through volatility-adjusted stops and maximize returns via a tiered profit ladder.

---

## 1. Core Risk Parameters

| Parameter | Code Value | Description |
| :--- | :--- | :--- |
| **ATR Period** | `12` | The lookback window for volatility calculation (N=12). |
| **ATR Multiplier** | `settings.ATR_TRAILING_MULTIPLIER` | Scaling factor for the stop-loss buffer (e.g., 2.0 or 3.0). |
| **Max Portfolio Risk** | `0.02` (2%) | The maximum percentage of total portfolio value at risk per trade. |
| **Time-Decay Threshold** | `settings.ATR_TIME_DECAY_HOURS` | Maximum duration to hold an underperforming (underwater) position. |
| **Concentration Cap** | `0.15` (15%) | Hard limit on total portfolio allocation for a single ticker. |

---

## 2. ATR Calculation Methodology
The Guardian uses a standard **Average True Range (ATR)** with an $N=12$ period. 

1.  **True Range (TR)** is calculated as the maximum of:
    *   $\text{High} - \text{Low}$
    *   $|\text{High} - \text{Previous Close}|$
    *   $|\text{Low} - \text{Previous Close}|$
2.  **ATR** is the rolling mean of the TR over 12 periods.
3.  **Initial Risk ($R$)**: Defined at entry as $\text{Entry ATR} \times \text{Multiplier}$.

---

## 3. Exit Matrix: Numbered Decision Tree
The `evaluate_position` method is evaluated every time the `Sentinel` provides a price update. The logic follows this strict priority:

1.  **Volatility Trailing Stop**: 
    *   *Condition:* Is `current_price` $\le$ (`highest_price` - (`current_atr` $\times$ `multiplier`))?
    *   *Action:* **SELL_ALL**.
    *   *Rationale:* Protects gains by tightening the stop as price reaches new highs and adjusts to current volatility.

2.  **Time-Decay Exit ("Dead Money Rule")**:
    *   *Condition:* Is `hours_held` $\ge$ `time_decay_hours` **AND** `current_price` < `entry_price`?
    *   *Action:* **SELL_ALL**.
    *   *Rationale:* Liquidates positions that fail to show momentum within the expected AI sentiment window.

3.  **Profit Tier 1 (+1R)**:
    *   *Condition:* Is `current_price` $\ge$ (`entry_price` + $1R$) **AND** `tier` == 0?
    *   *Action:* **SELL_PARTIAL_30%**.
    *   *Update:* Set `new_tier` to 1.
    *   *Rationale:* Locks in profits once the move equals the initial risk taken.

4.  **Profit Tier 2 (+2R)**:
    *   *Condition:* Is `current_price` $\ge$ (`entry_price` + $2R$) **AND** `tier` == 1?
    *   *Action:* **SELL_PARTIAL_30%**.
    *   *Update:* Set `new_tier` to 2.
    *   *Rationale:* Aggressive profit taking on extended moves.

5.  **Moonshot Hold**:
    *   *Condition:* If no above criteria are met.
    *   *Action:* **HOLD**.
    *   *Rationale:* The remaining 40% of the position rides the trend until hit by the Trailing Stop.

---

## 4. Dynamic Position Sizing
Before entry, the Guardian determines the investment value in PLN:
$$Shares = \frac{Capital \times 0.02 \times Conviction}{ATR \times Multiplier}$$
*   **Conviction:** A 0.0 to 1.0 score from the 14b Manager agent.
*   **Safety Check:** The result is capped at 15% of available capital to prevent over-leverage.

---

## 5. Database Integration
The Guardian interacts with the `remastered_core` PostgreSQL database via the `DBManager`.

### Fields Read
*   `entry_price`: The execution price from Trading 212.
*   `highest_price`: The peak price observed since position entry.
*   `entry_atr`: The ATR value at the moment of the "BUY" signal.
*   `tier`: Current profit ladder status (0, 1, or 2).
*   `created_at`: Used to calculate `hours_held`.

### Fields Written (via Order Results)
*   `tier`: Incremented upon partial sells.
*   `status`: Updated to `CLOSED` upon Trailing Stop or Time Decay.

---

## 6. Example Scenarios

| Scenario | Market Movement | Guardian Action |
| :--- | :--- | :--- |
| **The Flash Crash** | Price drops 5% instantly, crossing the ATR-based trailing stop. | **SELL_ALL** (Reason: Trailing Stop Hit) |
| **The Slow Bleed** | Price remains 1% below entry for 48 hours (assuming 48h limit). | **SELL_ALL** (Reason: Time Decay Exhaustion) |
| **The Breakout** | Price hits Entry + 1R. | **SELL_PARTIAL_30%** (Reason: Tier 1 Profit) |
| **The Moonshot** | Price hits Tier 1, Tier 2, then trends up indefinitely. | **SELL_30%**, then **SELL_30%**, then **HOLD** 40% until a reversal hits the trailing stop. |
