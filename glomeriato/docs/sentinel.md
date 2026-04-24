I have analyzed the `Sentinel` scanner module. Below is the technical documentation for the module, detailing its logic, filters, and mathematical formulas.

***

# Technical Documentation: Sentinel Scanner Module (`app/trading/sentinel.py`)

## 1. Overview
The **Sentinel** is the high-speed technical screening engine of the Glomeriato V2.1 bot. Its primary role is to filter the broad market universe into a concentrated list of high-probability candidates. It identifies two distinct types of opportunities: **Momentum Breakouts** (via Urgency Score) and **Mean Reversion** (via Volatility Exhaustion).

---

## 2. Screening Pipeline
The `screen_universe` method executes the following sequential pipeline for every ticker in the target list:

1.  **Data Acquisition**: Fetches 1 month of Daily data and 1 day of 5-minute Intraday data using `yfinance`.
2.  **Hard Filters**: Discards assets that fail basic liquidity, price, or stability requirements.
3.  **Mean Reversion Check**: Identifies stocks that are significantly oversold with specific volume signatures.
4.  **Urgency Calculation**: Calculates a momentum-volatility score for breakout potential.
5.  **Ranking & Selection**: Ranks candidates by Urgency and returns the top 10 along with all mean-reversion triggers.

---

## 3. Hard Filters & Thresholds
Sentinel discards outliers to ensure the bot only trades liquid and "sane" assets.

| Filter | Threshold | Logic / Rationale |
| :--- | :--- | :--- |
| **Liquidity** | $\ge 500,000$ | Daily Turnover (Close Price $\times$ Volume) in USD/PLN. |
| **Price** | $2.0 \to 1500.0$ | Protects against penny stocks and ultra-high-priced retail-inaccessible stocks. |
| **Market Cap** | $\ge 100,000,000$ | Avoids micro-cap manipulation (Defaults to 1B if data is missing). |
| **Volatility Ceiling** | $\le 150\%$ | Annualized Volatility. Discards "meme" stocks with extreme erratic returns. |
| **Lookback** | 20 Days | Minimum required data points for SMA and Standard Deviation. |

---

## 4. Urgency Score Calculation
The Urgency Score is a proprietary metric designed to identify imminent breakouts by combining volume-weighted momentum with volatility expansion.

### Formula:
$$Score = VW\_Momentum \times Vol\_Expansion$$

**Components:**
1.  **Volume-Weighted Momentum ($VW\_Mom$):**
    *   $\text{LogRet} = \ln(Close_t / Close_{t-1})$
    *   $\text{Vol\_Ratio} = \frac{Volume}{SMA(Volume, 20)}$
    *   $VW\_Mom = SMA(\text{LogRet} \times \text{Vol\_Ratio}, 5)$
2.  **Volatility Expansion ($VE$):**
    *   $IV (\text{Intraday Vol}) = \frac{High - Low}{Open}$
    *   $Ann\_Vol = \sqrt{mean(LogRet^2)} \times \sqrt{252}$
    *   $VE = \frac{IV}{Ann\_Vol}$

**Interpretation:** A positive score indicates price is moving in the direction of the trend with increasing relative volume and expanding intraday ranges relative to historical norms.

---

## 5. Mean Reversion Triggers
This logic identifies "oversold bounces" by looking for price extremes coupled with high-intensity selling exhaustion.

**Two-Step Validation:**
1.  **Price Deviation**: The current price must be at or below the **Lower Bollinger Band** (20-day SMA - 2 Standard Deviations).
2.  **Volume Exhaustion**: Using 5-minute data, the last 5m candle volume must be $> 1.5 \times$ the average 5m volume for the day. This signals a potential "capitulation" spike that often precedes a reversal.

---

## 6. Ranking and Data Output
### Top 10 Selection
*   **Ranking**: Candidates are sorted by `score` in descending order.
*   **Tie-Breaking**: The sorting algorithm is *stable*. In the event of identical urgency scores, the original order of the `tickers` input list is preserved (typically alphabetical or by priority in `targets.json`).
*   **Selection**: Only the top 10 highest-scoring "Urgency" candidates are passed to the next stage.

### Return Data Structure
The `screen_universe` method returns a `dict` to `strategy.py`:
```python
{
    "urgency": [
        {"ticker": "AAPL", "score": 0.45, "df": pd.DataFrame}, 
        ... # Max 10 items
    ],
    "reversion": ["TSLA", "MSFT", ...] # Uncapped list of tickers
}
```

---

## 7. Configuration Parameters
The following hard-coded parameters define the Sentinel's behavior:

*   `lookback`: **20** (Standard window for SMA and Volatility).
*   `Volume Exhaustion Multiplier`: **1.5** (For 5m data spikes).
*   `Urgency Limit`: **10** (Maximum momentum candidates per scan).
*   `Annualized Volatility Limit`: **1.5** (150% cap).
