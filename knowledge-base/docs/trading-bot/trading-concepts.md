# Trading Concepts Explained — Plain Language Guide

> You don't need to be a trader to understand how Glomeriato works.
> This guide explains every concept the bot uses in plain English, with real-world analogies.

---

## The Basics

### What is a stock / ticker?

A **stock** is a tiny ownership slice of a company. If Apple has 1 billion shares and you own 1, you own one-billionth of Apple — including a claim on future profits.

A **ticker** is just the shorthand nickname: `AAPL` = Apple, `NVDA` = Nvidia, `TSLA` = Tesla. The bot uses these codes to look up prices and place orders.

---

### What is momentum trading?

There are two main schools of thought in investing:

- **Value investing** — Buy things that are "on sale" because you believe they're worth more than the price. Like buying a coat at the end of winter because nobody wants it, waiting until next winter.
- **Momentum trading** — Buy things that are already moving up fast, betting they'll keep going. Like jumping on a moving train because it's accelerating.

Glomeriato is a **momentum bot**. It doesn't care if a stock is cheap or expensive. It cares if it's trending upward with strength right now.

---

## Risk & Volatility

### ATR — Average True Range

**What it is:** A number that measures how much a stock moves up and down on a typical day. High ATR = wild swings. Low ATR = calm, steady.

**Real-world analogy:** Think of it as the "splash zone" of a pool. A calm swimmer has a small splash zone (low ATR). A cannonball has a huge one (high ATR). You'd stand further back from the cannonballer.

**How the bot uses it:** The bot measures ATR to decide how far to place its safety nets (stop losses). It won't place a stop at 1% if the stock normally swings 3% a day — that would trigger every cycle. It scales dynamically.

---

### VIX — The Fear Index

**What it is:** VIX measures how scared professional investors are about the next 30 days. It's calculated from options prices. High VIX = high fear = markets expect big swings.

**Real-world analogy:** A **hurricane warning system**. VIX below 15 = flat calm sea. VIX at 25 = rough weather advisory. VIX at 40+ = category 4 hurricane. You wouldn't sail out in a hurricane.

**How the bot uses it:** If VIX (US) or VSTOXX (Europe) rises above 25, the bot stops placing any new trades until conditions calm down. Momentum strategies historically crash hardest during fear spikes.

---

### ADX — Trend Strength Meter

**What it is:** ADX (Average Directional Index) measures how strongly a stock is trending, on a scale from 0 to 100. It doesn't care which direction — just how strong.

- ADX < 20 = no real trend, choppy sideways movement
- ADX > 25 = clear trend (up or down)
- ADX > 40 = strong trend

**Real-world analogy:** A **speedometer**, not a compass. It tells you how fast the car is going, not where it's heading. The bot needs both speed (ADX > 25) and direction (price rising) before it buys.

**How the bot uses it:** The bot only buys momentum in stocks that have ADX > 25. If a stock is just bouncing sideways, the momentum signal is noise — ADX catches this.

---

### RSI — Relative Strength Index

**What it is:** RSI measures whether a stock is overbought (everyone already bought in, run is over) or oversold (everyone already sold, bounce likely). Scale 0–100.

- RSI < 30 = oversold (potential bounce)
- RSI 60–80 = strong momentum, not yet overheated ✅ bot's entry zone
- RSI > 80 = overbought (too late to the party)

**Real-world analogy:** A crowd queue. If only 20 people are in line (low RSI), the ride isn't popular yet. If 70 people are in line but it's moving fast (RSI 60–80), it's worth joining. If 95 people are in line (RSI 90), you'll wait forever and miss the next ride.

---

### 50-Day SMA — Regime Filter

**What it is:** The Simple Moving Average (SMA) of the last 50 trading days of price. It's a smoothed trend line.

**Real-world analogy:** **The tide level**. Day-to-day waves are noise (daily price moves). The tide (50d SMA) tells you whether the ocean is rising or falling overall. Surfers want a rising tide.

**How the bot uses it:** Before placing any trades in a region (EU or US), the bot checks whether the broad market index (SPY for US, STOXX50E for Europe) is above its 50-day average. If the market is in a downtrend, all new buy entries in that region are paused — riding momentum when the whole market is falling is swimming against the current.

---

## Exits & Safety Nets

### Hard Stop Loss

**What it is:** An absolute, non-negotiable exit price. If the stock drops 2.5% below where you bought it, sell immediately — no exceptions.

**Real-world analogy:** The **ejection seat**. You don't think about it, you just pull the cord when the plane is going down. It limits the worst-case loss on any single trade to 2.5%.

**How the bot uses it:** Checked first, every 5 minutes. If price ≤ entry × 97.5%, sell everything immediately.

---

### Chandelier Trailing Stop

**What it is:** A stop loss that hangs below the highest price the stock has ever reached since you bought it. As the stock climbs, the stop climbs with it — but it never moves down.

**Real-world analogy:** A **ratchet wrench**. You can tighten (the stop rises as price rises) but it won't loosen (the stop never drops back down). It locks in progress.

The "chandelier" name comes from the original description: imagine the stop as a chandelier hanging from the ceiling (the highest price). As the ceiling gets higher, the chandelier rises with it — but always hangs the same distance below.

The bot uses: `stop = highest_price_ever − 3 × ATR`. If price drops enough to hit it, sell.

---

### Breakeven-Plus Stop

**What it is:** After a trade has moved +1.5R in your favor, the hard stop is raised to your entry price plus the trading fees. Worst case: you break even, never lose.

**Real-world analogy:** **Free play** in a casino. Once you've won enough chips with the free credits, the casino lets you keep anything above your original stake. You can't go home empty-handed.

**How the bot uses it:** Once the position is up 1.5× its initial risk, the hard stop floor rises to entry + 0.3% (covering the round-trip FX fee). The trade is now "risk-free."

---

### Time-Decay Exit (Dead Money Rule)

**What it is:** If a position hasn't made meaningful progress after 4 hours, exit it.

**Real-world analogy:** **A boring party**. If you've been there for 4 hours and nothing fun has happened, you leave to find a better party. That capital could be deployed elsewhere.

**How the bot uses it:** If `hours_held ≥ 4` AND `gain < 0.5 × ATR` (barely moved), sell everything. Flat positions tie up cash that could be working harder.

---

## Measuring Success

### R-Multiples (1R, 2R, 3R)

**What it is:** A way to measure trade outcomes relative to what you risked. "R" = the amount you were willing to lose when you entered.

**Real-world analogy:** If you bet £10 on a horse, your R is £10.
- Win £10 → you made 1R
- Win £20 → you made 2R
- Lose £10 → you lost 1R

**How the bot uses it:**
- At +2R profit → sell 50% of the position (lock in gains)
- At +3R profit → sell the remaining 50%
- The remaining position always rides the chandelier trailing stop

---

### Win Rate vs Payoff Ratio — The Critical Math

**What the bot had before V2.2:** 63.2% win rate (wins more than it loses), but STILL losing money overall.

**Why?** Because the losses were bigger than the wins. With 1R/2R exits at 30% each, winners were tiny. With a 2.5% hard stop, losers were larger.

The math:
```
Expectancy = (Win Rate × Avg Win) − (Loss Rate × Avg Loss)
           = (0.632 × small) − (0.368 × bigger)
           = negative
```

**Real-world analogy:** Imagine a coin flip game where heads = you win £1, tails = you lose £2. You'd win 50% of flips but lose money overall. The bot had a similar problem — winning often but not winning enough per win.

**V2.2 fix:** Changed exits to +2R/+3R (bigger wins), which makes each win more meaningful relative to each loss.

---

### Conviction Score

**What it is:** The AI Manager's confidence level from 0 to 1 (or 0% to 100%). It reads the news and market context and decides: "How sure am I that this will go up?"

**Real-world analogy:** A **jury verdict scale**. After reviewing all evidence (news sentiment, price action, technical indicators, trade history), the Manager gives a score. The bot only acts if confidence ≥ 0.75 (75%).

---

### The 0.15% FX Fee

**What it is:** Every time you buy or sell a stock in a different currency, there's a 0.15% conversion fee. Round-trip (buy + sell) = 0.30%.

**Real-world impact:** The bot must make at least **0.30% profit per trade just to break even**. On a £1,000 position, that's £3 before the first penny of real profit.

This is why trade quality matters so much — every low-conviction trade that barely moves is actively losing money to fees.

---

### Sector Concentration Cap

**What it is:** The bot limits itself to a maximum of 2 open positions in any single industry sector (Technology, Healthcare, Energy, etc.).

**Real-world analogy:** **Don't put all eggs in one basket**. If the bot owned 8 tech stocks and the tech sector had a bad week (like a regulation announcement), all 8 positions would drop together. Sector cap prevents this.

---

## The Full Cycle — What Happens Every 30 Minutes

```
1. CHECK existing positions
   → Guardian evaluates each open position
   → Apply Hard Stop, Breakeven Stop, Trailing Stop, Time Decay, Profit Tiers
   → Exit anything that triggers

2. SCREEN the market
   → Check VIX — is fear too high? (Skip if VIX > 25)
   → Check broad index — is the market trending? (Skip if below 50d SMA)
   → Check time — Monday morning? Friday evening? (Skip)
   → Check capital — more than 65% deployed? (Skip)

3. SCAN 186 tickers
   → Sentinel filters: liquidity, price range, market cap, volatility
   → ADX gate: only trending stocks pass (ADX > 25)
   → Score by urgency (volume × momentum)
   → Top 10 go to the AI

4. THINK (AI Brain)
   → Analyst reads latest news → scores sentiment 0-100
   → Manager synthesizes news + charts + history → outputs BUY/SELL/HOLD + conviction 0-1

5. ACT
   → Conviction ≥ 0.75? Check sector cap. Calculate position size.
   → Place BUY order on Trading 212
   → Log everything to PostgreSQL

6. SLEEP
   → Wait 5 minutes → Guardian check only
   → Wait until next :00 or :30 → Full cycle again
```

---

## Realistic Expectations

| Metric | Target |
|---|---|
| Expected return per trade | +0.15% to +0.25% |
| Trades per day | 1–5 on active days |
| Annual return (realistic) | 15–25% |
| 1% daily return | Not realistic without leverage |

**Why 1% daily is not realistic:**
1% per day = 365% per year. Even the best hedge funds in history averaged 30-40% annually. A 1% daily bot would be the greatest financial instrument ever created. Realistic consistent returns are 15-30% annually — which is still exceptional compared to the stock market's ~10% average.

The real goal: **positive expectancy** — each trade, on average, makes money. Then let time and compounding do the work.
