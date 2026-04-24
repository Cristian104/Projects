# Sentinel — Market Scanner

**File:** `app/trading/sentinel.py`

Sentinel is the high-speed mathematical screening engine. It filters 90+ tickers down to the top 10 high-probability candidates before any AI is invoked — keeping the expensive inference stage lean.

## Role in the Pipeline

```
90+ tickers → [Hard Filters] → [Urgency Score] → Top 10 → Brain
                                [Mean Reversion] → Reversion list → Brain
```

## Hard Filters

Every ticker must pass all filters or it's discarded immediately:

| Filter | Threshold | Rationale |
|--------|-----------|-----------|
| Dollar Volume | ≥ $500,000/day | Ensures liquidity — no slippage risk |
| Price | $2.00 – $1,500.00 | Excludes penny stocks and unreachable assets |
| Market Cap | ≥ $100M | Avoids micro-cap manipulation |
| Annualized Volatility | ≤ 150% | Discards untradeable "meme" stocks |
| Data Lookback | ≥ 20 days | Minimum for SMA and StdDev calculations |

**Volatility formula:**
$$\sigma_{ann} = \sqrt{\frac{1}{n}\sum_{i=1}^{n} \left(\ln\frac{P_i}{P_{i-1}}\right)^2} \times \sqrt{252}$$

## Urgency Score (Momentum Breakouts)

Identifies imminent breakouts by combining volume-weighted momentum with volatility expansion:

$$Score = VW\_Momentum \times Vol\_Expansion$$

**Components:**

| Component | Formula |
|-----------|---------|
| Log Return | $\ln(Close_t / Close_{t-1})$ |
| Volume Ratio | $Volume / SMA(Volume, 20)$ |
| VW Momentum | $SMA(LogRet \times VolRatio, 5)$ |
| Intraday Vol | $(High - Low) / Open$ |
| Vol Expansion | $IntradayVol / \sigma_{ann}$ |

**Interpretation:** High score = price moving with above-average volume and expanding intraday range relative to historical norms = imminent breakout.

## Mean Reversion Triggers

Identifies "capitulation" setups — oversold stocks likely to snap back:

1. **Price Deviation:** Current price ≤ Lower Bollinger Band (SMA₂₀ − 2σ)
2. **Volume Exhaustion:** Last 5-minute candle volume > 1.5× average 5m volume for the day

Both conditions must be true simultaneously.

## Output Structure

```python
{
    "urgency": [
        {"ticker": "AAPL", "score": 0.45, "df": pd.DataFrame},
        # ... up to 10 items, sorted descending by score
    ],
    "reversion": ["TSLA", "MSFT", ...]  # Uncapped list
}
```

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `lookback` | 20 | SMA / StdDev window |
| Volume exhaustion multiplier | 1.5 | 5m spike threshold |
| Urgency limit | 10 | Max momentum candidates returned |
| Volatility cap | 150% | Hard filter ceiling |

## Data Sources

- **Daily data (1 month):** `yfinance` — for technicals, SMA, volatility
- **Intraday data (5m, 1 day):** `yfinance` — for volume exhaustion check
