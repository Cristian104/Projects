# Glomeriato V2.2 — Technical Reference

**Release Date:** 2026-03-09
**Architecture:** Dual-Agent AI (Analyst/Manager) + Risk Engine (Guardian) + Market Sentinel

---

## What Changed: V2.1 → V2.2

| Parameter | V2.1 | V2.2 | Why |
|---|---|---|---|
| `ATR_PERIOD` | 12 | **10** | Kaufman 2013: optimal for 1-5d equity holds |
| `ATR_TRAILING_MULTIPLIER` | 6.0 | **3.0** | LeBeau Chandelier Exit standard |
| `ATR_TIME_DECAY_HOURS` | 6.0 | **4.0** | Exit dead money faster |
| `HARD_STOP_PCT` | — | **2.5%** | New: absolute floor on losses |
| `BREAKEVEN_ACTIVATION_R` | — | **1.5R** | New: make winning trades risk-free |
| `TIER1_TARGET_R` | 1.0R | **2.0R** | Let winners run further before partial |
| `TIER2_TARGET_R` | 2.0R | **3.0R** | Second exit at 3R |
| `TIER1_SELL_PCT` | 30% | **50%** | Bigger meaningful exit at 2R |
| `TIER2_SELL_PCT` | 30% | **50%** | Full exit at 3R |
| `MIN_BUY_CONVICTION` | 0.65 | **0.75** | Higher signal quality bar |
| `MAX_CONCURRENT_POSITIONS` | 8 | **10** | Foltice & Langer 2015: 10-15 optimal |
| `MAX_CAPITAL_DEPLOYED_PCT` | 80% | **65%** | More room for new quality entries |
| `REGIME_FILTER_TOLERANCE` | 3% | **5%** | Slightly more permissive regime gate |
| `VIX_PAUSE_THRESHOLD` | — | **25.0** | New: pause entries in fear spikes |
| `VSTOXX_PAUSE_THRESHOLD` | — | **25.0** | New: EU volatility equivalent |
| `ADX_THRESHOLD` | — | **25.0** | New: only trade trending markets |
| `LIQUIDITY_FLOOR_US` | 500k | **1,000,000** | Better execution quality for US |
| `MAX_POSITIONS_PER_SECTOR` | — | **2** | New: sector concentration cap |
| `AVOID_MONDAY_OPEN_MINUTES` | — | **90** | New: skip Monday volatility washout |
| `AVOID_FRIDAY_CLOSE_HOUR` | — | **16** | New: skip Friday gap risk window |

---

## Guardian Exit Matrix

Evaluated in strict priority order every 5 minutes:

```
1. Hard Stop Loss          price ≤ entry × (1 - 0.025)          → SELL ALL
2. Breakeven-Plus Stop     highest_price ≥ entry + 1.5R          → stop rises to entry + 0.3%
                           AND current_price ≤ that floor        → SELL ALL
3. Chandelier Trailing Stop  price ≤ highest_price − 3×ATR       → SELL ALL
4. Time-Decay Exit         held ≥ 4h AND gain < 0.5×ATR          → SELL ALL
5. Tier 1 Profit           price ≥ entry + 2×ATR, tier=0         → SELL 50%
6. Tier 2 Profit           price ≥ entry + 3×ATR, tier=1         → SELL 50%
7. HOLD
```

The root cause of the V2.1 negative returns (-0.297% avg per trade): exits were at 1R/2R with 30% each, creating negative convexity — selling 60% of winners before meaningful profit while 100% downside remained exposed. Implied payoff ratio was 0.39 vs 0.58 needed to break even.

---

## Entry Gates (all must pass to place a BUY)

1. **Market hours** — EU 08:50–17:42, US 14:30–22:30 Warsaw
2. **Session filter** — No Monday first 90 min, no Friday after 16:00
3. **Regime filter** — SPY/STOXX50E above 50d SMA (−5% tolerance)
4. **VIX/VSTOXX gate** — Both indices must be below 25
5. **Capital gate** — Total deployed < 65% of balance
6. **Position cap** — Fewer than 10 open positions
7. **Sector cap** — Fewer than 2 open positions in same GICS sector
8. **Sentinel hard filters** — Liquidity, price range, market cap, volatility ceiling
9. **ADX gate** — ADX > 25 (trending market, not ranging)
10. **Technical screen** — RSI 60–80 + price > 20d SMA (momentum entries)
11. **Analyst score** — Gemini news sentiment ≥ 60/100
12. **Conviction** — Manager AI conviction ≥ 0.75

---

## Ticker Universe — 186 Tickers

| Region | Count | Examples |
|---|---|---|
| 🇺🇸 US | ~95 | AAPL, NVDA, TSLA, PLTR, CRWD, SNOW, COIN |
| 🇩🇪 DE | 24 | SAP.DE, SIE.DE, BMW.DE, BAYN.DE |
| 🇫🇷 PA | 19 | AIR.PA, MC.PA, BNP.PA, RMS.PA |
| 🇬🇧 L | 15 | BP.L, AZN.L, HSBA.L, SHEL.L |
| 🇪🇸 MC | 9 | SAN.MC, ITX.MC, TEF.MC |
| 🇳🇱 AS | 8 | ASML.AS, ADYEN.AS |
| 🇵🇱 WA | 7 | KGH.WA, PKN.WA, LPP.WA |

Per cycle: **186 → ~15 pass Sentinel → top 10 to AI → ~2-3 get BUY signal → 0-1 executed**

---

## Academic Sources

| Paper | Finding Used |
|---|---|
| Jegadeesh & Titman (1993) | Momentum factor construction |
| Daniel & Moskowitz (2016) | Momentum crash conditions, regime filters |
| Ang, Hodrick, Xing, Zhang (2006) | VIX > 25 = momentum reversal risk |
| Kaufman (2013) | ATR period 10 optimal for 1-5d holds |
| LeBeau (Chandelier Exit) | 3×ATR trailing stop from highest price |
| Wilder (1978) | ATR, RSI, ADX definitions and thresholds |
| Van Tharp | R-multiples, expectancy framework |
| Moskowitz & Grinblatt (1999) | Sector momentum, concentration risk |
| Foltice & Langer (2015) | 10-15 positions optimal for momentum |
| Birru (2016) | Monday open volatility washout |

---

## Realistic Performance Expectations

- **Before V2.2:** -0.297% avg return/trade (negative expectancy despite 63.2% win rate)
- **Target post-V2.2:** +0.15–0.25% avg return/trade
- **Realistic annual:** 15–25% (no leverage available on T212 Invest/DEMO)
- **1% daily target:** Not achievable without leverage — that's 365% annualized
