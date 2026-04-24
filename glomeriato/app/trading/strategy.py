import os
import time
import signal
import asyncio
import json
import pytz
import subprocess
import re
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from loguru import logger
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from app.core.config import settings

_running = True

load_dotenv()

# Configure Logger to write to file for Dashboard mirroring
logger.add("app.log", rotation="10 MB", retention="1 day", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

from app.trading.sentinel import Sentinel
from app.intelligence.brain import QuantBrain
from app.trading.guardian import Guardian
from app.intelligence.news_aggregator import NewsAggregator
from app.connectors.trading212 import Trading212
from app.connectors.telegram import TelegramBot
from app.core.memory import DBManager

console = Console()

def _shutdown_handler(signum, frame):
    global _running
    logger.warning(f"⚠️ Signal {signum} received — initiating graceful shutdown...")
    _running = False


class GlomeriatoV01:
    def __init__(self, mode="demo"):
        self.mode = mode
        self.t212 = Trading212(os.getenv("T212_API_KEY", "").strip())
        self.db = DBManager(host=os.getenv("DB_HOST", "remastered_db"))
        self.sentinel = Sentinel()
        self.brain = QuantBrain()
        self.guardian = Guardian()
        self.news = NewsAggregator()
        self.telegram = TelegramBot()
        self.cycle_logs = []
        self._notif_queue = []
        self._last_digest_hour = -1
        self._eod_sent_today = False

        signal.signal(signal.SIGTERM, _shutdown_handler)
        signal.signal(signal.SIGINT, _shutdown_handler)

        try:
            with open("app/data/targets.json", "r") as f:
                self.universe = json.load(f)
        except: self.universe = []

    def get_regional_tickers(self):
        waw_tz = pytz.timezone("Europe/Warsaw")
        now = datetime.now(waw_tz)
        time_float = now.hour + (now.minute / 60.0)

        is_monday_washout = (now.weekday() == 0 and
                             time_float < (8.8 + settings.AVOID_MONDAY_OPEN_MINUTES / 60.0))
        is_friday_close = (now.weekday() == 4 and
                           now.hour >= settings.AVOID_FRIDAY_CLOSE_HOUR)

        eu_active = 8.8 <= time_float <= 17.7
        us_active = 14.5 <= time_float <= 22.5
        is_weekend = now.weekday() >= 5

        if is_weekend or (not eu_active and not us_active):
            logger.info("💤 Markets closed — sleeping until open.")
            return [], []

        eu_pool, us_pool = [], []
        for t in self.universe:
            is_eu = any(t.endswith(s) for s in [".DE", ".PA", ".MC", ".AS", ".WA", ".L"])
            if is_eu and eu_active and not (is_monday_washout or is_friday_close):
                eu_pool.append(t)
            elif not is_eu and us_active and not is_friday_close:
                us_pool.append(t)

        return eu_pool, us_pool

    def _is_ticker_market_open(self, ticker: str) -> bool:
        """Returns True if the market for this ticker is currently open."""
        waw_tz = pytz.timezone("Europe/Warsaw")
        now = datetime.now(waw_tz)
        if now.weekday() >= 5:
            return False
        time_float = now.hour + (now.minute / 60.0)
        is_eu = any(ticker.endswith(s) for s in [".DE", ".PA", ".MC", ".AS", ".WA", ".L"])
        if is_eu:
            return 8.8 <= time_float <= 17.7
        return 14.5 <= time_float <= 22.5

    def _get_volatility_index(self, region: str) -> float:
        """Fetch VIX (US) or VSTOXX (EU). Returns 0.0 on failure (fail open)."""
        ticker = "^VIX" if region == "USA" else "^VSTOXX"
        try:
            df = yf.Ticker(ticker).history(period="5d", interval="1d")
            if df is not None and not df.empty:
                return float(df['Close'].iloc[-1])
        except Exception as e:
            logger.debug(f"⚠️ Volatility index fetch failed for {ticker}: {e}")
        return 0.0  # fail open (don't block entries on fetch failure)

    def _is_volatility_regime_safe(self, region: str) -> bool:
        """
        Returns False when VIX/VSTOXX is above the pause threshold.
        Daniel & Moskowitz (2016): high-VIX regimes are where momentum crashes occur.
        Ang et al. (2006): VIX > 25 predicts momentum reversals.
        """
        threshold = (settings.VIX_PAUSE_THRESHOLD if region == "USA"
                     else settings.VSTOXX_PAUSE_THRESHOLD)
        vix = self._get_volatility_index(region)
        if vix == 0.0:
            return True  # fail open
        if vix > threshold:
            logger.warning(f"⚡ {region}: Volatility index {vix:.1f} > {threshold} — pausing new entries.")
            return False
        logger.info(f"✅ {region}: Volatility index {vix:.1f} (safe, threshold {threshold})")
        return True

    def _classify_regime(self, region: str) -> dict:
        """
        Phase 3: 4-state market regime classifier using RSI + ATR + MACD on the broad index.
        Returns a dict with state label and position_size_multiplier.

        States:
          trending_up   (1.0x) — RSI > 55, MACD bullish: full position sizing
          ranging       (0.6x) — mixed signals: reduced sizing
          volatile      (0.5x) — ATR elevated >1.5x average: caution
          trending_down (0.0x) — RSI < 40, MACD bearish: block new entries

        Fails open (trending_up, 1.0x) if data is unavailable.
        """
        index_ticker = "SPY" if region == "USA" else "^STOXX50E"
        fail_open = {"state": "trending_up", "label": "✅ Trending Up (fail-open)",
                     "multiplier": settings.REGIME_MULTIPLIER_TRENDING_UP}
        try:
            df = yf.Ticker(index_ticker).history(period="6mo", interval="1d")
            if df is None or df.empty or len(df) < 30:
                return fail_open

            close = df['Close']

            # RSI(14)
            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rsi = float(100 - (100 / (1 + gain.iloc[-1] / (loss.iloc[-1] + 1e-9))))

            # MACD direction
            ema_fast = close.ewm(span=12, adjust=False).mean()
            ema_slow = close.ewm(span=26, adjust=False).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_bullish = bool(macd.iloc[-1] > macd_signal.iloc[-1])

            # ATR elevation (current vs 20d average)
            high_low = df['High'] - df['Low']
            high_close = (df['High'] - close.shift()).abs()
            low_close = (df['Low'] - close.shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr_now = float(tr.rolling(10).mean().iloc[-1])
            atr_avg = float(tr.rolling(20).mean().iloc[-1])
            atr_elevated = atr_now > (atr_avg * 1.5) if atr_avg > 0 else False

            # Classify
            if rsi < 40 and not macd_bullish:
                state = "trending_down"
                multiplier = settings.REGIME_MULTIPLIER_TRENDING_DOWN
                label = f"📉 Trending Down (RSI {rsi:.0f}, MACD bearish)"
            elif atr_elevated:
                state = "volatile"
                multiplier = settings.REGIME_MULTIPLIER_VOLATILE
                label = f"⚡ Volatile (ATR {atr_now:.2f} vs avg {atr_avg:.2f})"
            elif rsi > 55 and macd_bullish:
                state = "trending_up"
                multiplier = settings.REGIME_MULTIPLIER_TRENDING_UP
                label = f"✅ Trending Up (RSI {rsi:.0f}, MACD bullish)"
            else:
                state = "ranging"
                multiplier = settings.REGIME_MULTIPLIER_RANGING
                label = f"↔️ Ranging (RSI {rsi:.0f})"

            logger.info(f"🧭 Regime [{region}]: {label} → size multiplier {multiplier:.1f}x")
            return {"state": state, "label": label, "multiplier": multiplier}

        except Exception as e:
            logger.debug(f"Regime classifier error for {region}: {e}")
            return fail_open

    def _get_open_sector_counts(self) -> dict:
        """Count open positions by sector for the concentration cap."""
        active = self.db.get_active_positions()
        sector_counts = {}
        for pos in active:
            try:
                info = yf.Ticker(pos['ticker']).info
                sector = info.get('sector', 'Unknown')
            except Exception:
                sector = 'Unknown'
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        return sector_counts

    def run_guardian_pass(self) -> list:
        """Guardian-only exit check — runs every 5 minutes between full cycles."""
        active = self.db.get_active_positions()
        if not active:
            return []

        console.print(f"[bold yellow]🛡️ Guardian checking {len(active)} active positions...")
        exits = []

        for pos in active:
            ticker = pos['ticker']
            df, _, _ = self.sentinel._fetch_data(ticker)
            if df is None:
                continue
            price = float(df['Close'].iloc[-1])
            if price > float(pos['highest_price']):
                self.db.update_highest_price(ticker, price)

            decision = self.guardian.evaluate_position(
                current_price=price,
                entry_price=float(pos['entry_price']),
                highest_price=float(pos['highest_price']),
                entry_atr=float(pos['entry_atr']),
                current_atr=float(self.guardian.calculate_atr(df)),
                hours_held=(datetime.now(timezone.utc) - pos['timestamp'].replace(tzinfo=timezone.utc)).total_seconds() / 3600,
                tier=pos['tier']
            )

            action = decision['action']

            if action in ("SELL_ALL", "SELL_PARTIAL") and not self._is_ticker_market_open(ticker):
                logger.info(f"🕐 {ticker}: Exit signal ({action}) held — market closed. Will execute at open.")
                continue

            if action == "SELL_ALL":
                logger.warning(f"🚨 EXIT: {ticker} | {decision['reason']}")
                qty = float(pos['quantity'])
                order_placed = self.t212.place_order(ticker, -qty)
                if not order_placed:
                    broker_qty = self.t212.get_position_quantity(ticker)
                    if broker_qty is not None and broker_qty > 0 and abs(broker_qty - qty) > 0.001:
                        logger.warning(f"⚠️ {ticker}: Qty mismatch DB={qty:.4f} Broker={broker_qty:.4f}. Auto-correcting.")
                        self.db.update_position_after_partial_sell(ticker, broker_qty, pos['tier'])
                        qty = broker_qty
                        order_placed = self.t212.place_order(ticker, -qty)
                if order_placed:
                    balance_before = self.t212.get_cash_balance()
                    fee_rate, val = 0.0015, qty * price
                    self.db.log_transaction(ticker, "SELL", qty, price, val * fee_rate, balance_before + (val - (val * fee_rate)))
                    self.db.close_position(ticker, price, decision['reason'])
                    self.db.log_decision(
                        ticker, score=0, reason=f"Guardian exit: {decision['reason']}",
                        order="SELL_ALL", conv=0.0,
                        manager_reason=f"Exit: {decision['reason']} | price={price:.4f} entry={float(pos['entry_price']):.4f}"
                    )
                    exits.append({"ticker": ticker, "type": "TRADE_SELL_ALL", "score": 0,
                                  "reason": f"EXIT: Sold all {qty} @ {price}. {decision['reason']}"})
                    self._notif_queue.append({"type": "SELL_ALL", "ticker": ticker, "price": price, "note": decision['reason']})
                else:
                    logger.error(f"❌ {ticker}: SELL_ALL failed after auto-sync. Retrying next pass.")

            elif action == "SELL_PARTIAL":
                sell_pct = decision.get('sell_pct', 0.50)
                logger.warning(f"💰 PARTIAL EXIT: {ticker} | {decision['reason']} ({sell_pct*100:.0f}%)")
                full_qty = float(pos['quantity'])
                sell_qty = full_qty * sell_pct
                if self.t212.place_order(ticker, -sell_qty) is True:
                    balance_before = self.t212.get_cash_balance()
                    fee_rate, val = 0.0015, sell_qty * price
                    self.db.log_transaction(ticker, "SELL_PARTIAL", sell_qty, price, val * fee_rate, balance_before + (val - (val * fee_rate)))

                    mapped_ticker = self.t212.mappings.get(ticker, f"{ticker.replace('.', '_')}_EQ")
                    portfolio = self.t212.get_detailed_portfolio()
                    broker_pos = next((p for p in portfolio if p.get('ticker') == mapped_ticker), None)
                    actual_qty = float(broker_pos['quantity']) if broker_pos else 0.0

                    if actual_qty == 0:
                        logger.warning(f"⚠️ Reconciliation: broker shows 0 qty for {ticker} — closing position")
                        self.db.close_position(ticker, price, "RECONCILE_ZERO_QTY")
                    else:
                        self.db.update_position_after_partial_sell(ticker, actual_qty, decision['new_tier'])

                    self.db.log_decision(
                        ticker, score=0, reason=f"Guardian partial exit: tier {decision['new_tier']}",
                        order="SELL_PARTIAL", conv=0.0,
                        manager_reason=f"Partial exit tier {decision['new_tier']}: price={price:.4f} entry={float(pos['entry_price']):.4f}"
                    )
                    exits.append({"ticker": ticker, "type": "TRADE_SELL_PARTIAL", "score": 0,
                                  "reason": f"PARTIAL: Sold {sell_qty:.2f} @ {price}. {decision['reason']}"})
                    self._notif_queue.append({"type": "SELL_PARTIAL", "ticker": ticker, "price": price, "note": decision['reason']})

        return exits

    def sync_reality(self):
        """V2.1 Sync: Clears ghosts AND restores missing positions from broker."""
        if self.mode not in ["demo", "live"]: return
        logger.info("🧹 V2.1 Sync: Checking Broker vs Database...")

        self.t212.cancel_pending_orders()
        portfolio = self.t212.get_detailed_portfolio()

        if not portfolio:
            logger.warning("⚠️ Broker returned empty portfolio. Skipping sync to prevent accidental purge.")
            return

        owned_tickers = {p['ticker']: p for p in portfolio}
        active_db = self.db.get_active_positions()
        db_tickers = {pos['ticker']: pos for pos in active_db}
        rev_map = {v: k for k, v in self.t212.mappings.items()}

        for ticker_db, pos in db_tickers.items():
            mapped = self.t212.mappings.get(ticker_db, f"{ticker_db.replace('.', '_')}_EQ")
            if mapped not in owned_tickers:
                logger.warning(f"👻 Ghost Purge: {ticker_db}")
                self.db.close_position(ticker_db, 0.0, "SYNC_PURGE")

        for t212_ticker, data in owned_tickers.items():
            yahoo_ticker = rev_map.get(t212_ticker) or t212_ticker.replace("_EQ", "").replace("_", ".")
            if yahoo_ticker not in db_tickers:
                if self.db.was_recently_sold(yahoo_ticker, hours=2):
                    logger.info(f"⏭️ Skipping restore {yahoo_ticker} — sold recently, awaiting settlement")
                    continue
                logger.info(f"🔄 Restoring missing position: {yahoo_ticker}")
                df, _, _ = self.sentinel._fetch_data(yahoo_ticker)
                atr = self.guardian.calculate_atr(df) if df is not None else 0.0
                self.db.open_position(
                    ticker=yahoo_ticker,
                    entry_price=float(data.get('averagePrice', 0)),
                    entry_atr=atr,
                    quantity=float(data.get('quantity', 0)),
                    conviction=0.5
                )

    def process_region(self, ticker_pool, region_name, allocation_ratio):
        if not ticker_pool: return
        console.print(f"\n[bold cyan]🌍 {region_name} DESK: Screening Universe...")
        candidates = self.sentinel.screen_universe(ticker_pool, region=region_name)

        to_process = []
        for tkr in candidates['reversion']: to_process.append({"t": tkr, "type": "REVERSION"})
        for item in candidates['urgency']: to_process.append({"t": item['ticker'], "type": "URGENCY", "df": item['df']})
        if not to_process:
            for t in ticker_pool[:3]: to_process.append({"t": t, "type": "INFO"})

        # ── Phase 3: Regime classifier (replaces binary SMA gate) ─────────────
        regime = self._classify_regime(region_name) if settings.REGIME_CLASSIFIER_ENABLED else \
                 {"state": "trending_up", "multiplier": 1.0, "label": "classifier disabled"}
        if regime["state"] == "trending_down":
            logger.warning(f"🚫 GATE:REGIME [{region_name}] {regime['label']} — blocking all new entries.")
            return

        # ── VIX/VSTOXX gate (hard block at extreme fear) ──────────────────────
        if not self._is_volatility_regime_safe(region_name):
            vix_now = self._get_volatility_index(region_name)
            threshold = settings.VIX_PAUSE_THRESHOLD if region_name == "USA" else settings.VSTOXX_PAUSE_THRESHOLD
            logger.warning(f"🚫 GATE:VIX [{region_name}] Volatility {vix_now:.1f} > {threshold} — blocking entries.")
            return

        # ── Portfolio exposure gates ───────────────────────────────────────────
        balance_check = self.t212.get_cash_balance()
        if balance_check <= 10.0:
            logger.warning(f"🚫 GATE:BALANCE [{region_name}] Cash balance ${balance_check:.2f} too low.")
            return
        active_positions_check = self.db.get_active_positions()
        if len(active_positions_check) >= settings.MAX_CONCURRENT_POSITIONS:
            logger.warning(f"🚫 GATE:MAXPOS [{region_name}] {len(active_positions_check)}/{settings.MAX_CONCURRENT_POSITIONS} open — skipping entries.")
            return
        total_invested = sum(float(p['quantity']) * float(p['entry_price']) for p in active_positions_check)
        deployed_pct = (total_invested / balance_check * 100) if balance_check > 0 else 0
        if total_invested > balance_check * settings.MAX_CAPITAL_DEPLOYED_PCT:
            logger.warning(f"🚫 GATE:CAPITAL [{region_name}] {deployed_pct:.1f}% deployed > {settings.MAX_CAPITAL_DEPLOYED_PCT*100:.0f}% — skipping entries.")
            return

        logger.info(f"✅ [{region_name}] All region gates passed | balance=${balance_check:.2f} "
                    f"deployed={deployed_pct:.1f}% positions={len(active_positions_check)} "
                    f"regime={regime['state']}({regime['multiplier']:.1f}x) | {len(to_process)} candidates")

        sector_counts = self._get_open_sector_counts()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Analysing {region_name} candidates...", total=len(to_process))
            for item in to_process:
                ticker = item['t']
                entry_type = item.get('type', 'URGENCY')
                progress.update(task, description=f"[cyan]Scanning: {ticker}")

                # ── Cooldown check ─────────────────────────────────────────────
                if self.db.was_recently_sold(ticker, hours=4):
                    logger.info(f"⏭️  SKIP:COOLDOWN {ticker} — sold within 4h")
                    progress.advance(task)
                    continue

                # ── Phase 2: Technical signal is the PRIMARY gate ──────────────
                df = item.get('df') or self.sentinel._fetch_data(ticker)[0]
                if df is None or df.empty:
                    logger.info(f"⏭️  SKIP:NODATA {ticker} — could not fetch price data")
                    progress.advance(task)
                    continue

                tech = self.sentinel.calculate_technical_signal(df, entry_type)
                if tech["signal"] == "AVOID":
                    logger.info(f"📉 SKIP:TECH {ticker} [{entry_type}] RSI={tech['rsi']} "
                                f"macd_bull={tech['macd_bullish']} above_sma20={tech['above_sma20']} "
                                f"conf={tech['confidence']:.2f}")
                    self.cycle_logs.append({"ticker": ticker, "type": entry_type, "score": 0,
                                            "reason": f"TECH_AVOID RSI={tech['rsi']} conf={tech['confidence']:.2f}"})
                    progress.advance(task)
                    continue

                # ── Sentiment: confirmatory or gate (controlled by SENTIMENT_ROLE) ──
                news = asyncio.run(self.news.fetch_latest(ticker))
                report = self.brain.triage_sentiment(ticker, news)
                self.db.log_decision(ticker, report['score'], report['reason'],
                                     f"SCAN_{entry_type}", 0.0,
                                     f"V3.0 {region_name} | tech={tech['signal']} rsi={tech['rsi']} conf={tech['confidence']:.2f}")

                if settings.SENTIMENT_ROLE == "gate":
                    # Legacy: hard sentiment gate
                    if report['score'] < settings.SENTIMENT_GATE_THRESHOLD:
                        logger.info(f"📉 SKIP:SENTIMENT_GATE {ticker} — score {report['score']} < {settings.SENTIMENT_GATE_THRESHOLD} | {report['reason'][:80]}")
                        self.cycle_logs.append({"ticker": ticker, "type": entry_type,
                                                "score": report['score'], "reason": report['reason']})
                        progress.advance(task)
                        continue
                    conviction = 0.60
                else:
                    # Confirmatory: tech confidence is the base, sentiment adjusts ±0.1
                    conviction = 0.50 + tech['confidence'] * 0.35
                    if report['score'] >= 65:
                        conviction = min(conviction + 0.10, 0.95)
                    elif report['score'] < 40:
                        conviction = max(conviction - 0.10, 0.10)
                    logger.info(f"📊 {ticker} | sentiment={report['score']} tech_conf={tech['confidence']:.2f} "
                                f"→ conviction={conviction:.2f} | {report['reason'][:80]}")

                if conviction < settings.MIN_BUY_CONVICTION:
                    logger.info(f"📉 SKIP:CONVICTION {ticker} — {conviction:.2f} < floor {settings.MIN_BUY_CONVICTION}")
                    self.cycle_logs.append({"ticker": ticker, "type": entry_type,
                                            "score": report['score'], "reason": f"low conviction {conviction:.2f}"})
                    progress.advance(task)
                    continue

                # ── Sector concentration cap ───────────────────────────────────
                try:
                    sector = yf.Ticker(ticker).info.get('sector', 'Unknown')
                except Exception:
                    sector = 'Unknown'
                if sector_counts.get(sector, 0) >= settings.MAX_POSITIONS_PER_SECTOR:
                    logger.info(f"🏭 SKIP:SECTOR {ticker} — '{sector}' at max {settings.MAX_POSITIONS_PER_SECTOR}")
                    progress.advance(task)
                    continue

                # ── Phase 3+4: Size with regime multiplier + volatility scaling ─
                price = float(df['Close'].iloc[-1])
                atr = float(self.guardian.calculate_atr(df))
                balance_before = self.t212.get_cash_balance()
                fee_rate = 0.0015

                spendable = self.guardian.calculate_position_size(
                    conviction, balance_before, price, atr,
                    regime_multiplier=regime['multiplier']
                )
                qty = (spendable / (1 + fee_rate)) / price
                if ".WA" in ticker: qty = min(qty, 60)
                qty = int(qty) if ticker.endswith((".WA", ".MC")) else round(qty, 2)

                if qty <= 0:
                    logger.info(f"📉 SKIP:QTY {ticker} — calculated qty={qty} (spendable=${spendable:.2f})")
                    progress.advance(task)
                    continue

                # ── Place order ────────────────────────────────────────────────
                if self.t212.place_order(ticker, qty):
                    val = qty * price
                    self.db.log_transaction(ticker, "BUY", qty, price, val * fee_rate,
                                            balance_before - (val + val * fee_rate))
                    self.db.open_position(ticker, price, atr, qty, conviction)
                    sector_counts[sector] = sector_counts.get(sector, 0) + 1
                    reason = (f"BUY {qty}@{price:.2f} | tech={tech['signal']}({tech['confidence']:.2f}) "
                              f"sentiment={report['score']} conv={conviction:.2f} regime={regime['state']}")
                    self.cycle_logs.append({"ticker": ticker, "type": "TRADE_BUY",
                                            "score": report['score'], "reason": reason})
                    self._notif_queue.append({"type": "BUY", "ticker": ticker, "price": price,
                                              "note": f"conv={conviction:.2f} qty={qty} regime={regime['state']}"})
                    logger.success(f"💎 BUY EXECUTED: {ticker} | {reason}")
                else:
                    self.cycle_logs.append({"ticker": ticker, "type": entry_type,
                                            "score": report['score'], "reason": "order rejected by broker"})

                progress.advance(task)

    def run_cycle(self):
        console.rule(f"[bold blue]🚀 GLOMERIATO V2.2 CYCLE START: {datetime.now().strftime('%H:%M:%S')}")
        self.cycle_logs = []

        new_mode = self.db.get_setting("brain_mode") or "api"
        if new_mode != self.brain.brain_mode:
            logger.info(f"🔀 Brain mode switched: {self.brain.brain_mode} → {new_mode}")
            self.brain.brain_mode = new_mode

        self.sync_reality()
        self.cycle_logs.extend(self.run_guardian_pass())

        eu_pool, us_pool = self.get_regional_tickers()
        self.process_region(eu_pool, "EUROPE", 0.40)
        self.process_region(us_pool, "USA", 0.60)

        if self.cycle_logs:
            summary_table = Table(title="Cycle Action Summary", title_style="bold magenta", border_style="blue")
            summary_table.add_column("Ticker", style="cyan")
            summary_table.add_column("Type", style="white")
            summary_table.add_column("AI Score", justify="center")
            summary_table.add_column("Result/Reasoning", style="green")

            for log in self.cycle_logs:
                color = "green" if "TRADE" in log['type'] else "white"
                summary_table.add_row(log['ticker'], log['type'], str(log['score']), log['reason'], style=color)

            console.print("\n")
            console.print(summary_table)

            logger.info("📝 Generating transactional market summary...")
            summary = self.brain.generate_market_summary(self.cycle_logs)
            self.db.save_market_summary(summary)
        else:
            self.db.save_market_summary("### 💤 System Status: Idle\nMarket is closed or bot is in deep sleep cycle.")

        try:
            logger.info("💾 Triggering automated backup...")
            subprocess.run(["bash", "/app/scripts/backup_manager.sh"], check=True)
        except Exception as e: logger.error(f"❌ Backup failed: {e}")

    def send_digest(self):
        """Send 2-hour compilation of queued trade events and clear the queue."""
        self.telegram.send_digest(self._notif_queue)
        self._notif_queue.clear()
        logger.info(f"📬 2h digest sent.")

    def send_eod_summary(self):
        """Query today's activity and send an AI-generated EOD summary via Gemini Flash."""
        try:
            waw_tz = pytz.timezone("Europe/Warsaw")
            today = datetime.now(waw_tz).strftime("%Y-%m-%d")
            txns = self.db.get_transactions_today(today)
            active = self.db.get_active_positions()

            buys  = [t for t in txns if t["action"] == "BUY"]
            sells = [t for t in txns if t["action"] in ("SELL", "SELL_PARTIAL")]

            buy_lines  = "\n".join([f"  BUY  {t['ticker']} qty={t['quantity']:.2f} @ {t['price']:.2f}" for t in buys])  or "  None"
            sell_lines = "\n".join([f"  SELL {t['ticker']} qty={t['quantity']:.2f} @ {t['price']:.2f}" for t in sells]) or "  None"
            open_lines = "\n".join([f"  {p['ticker']} entry={float(p['entry_price']):.2f} tier={p['tier']}" for p in active]) or "  None"

            prompt = (
                f"You are the Glomeriato trading bot end-of-day analyst. Today is {today}.\n"
                f"Summarize this activity in 5-8 lines for a Telegram message. Be concise and use emojis.\n"
                f"Include: what happened, open positions status, and a brief outlook.\n\n"
                f"BUYS TODAY:\n{buy_lines}\n\n"
                f"SELLS TODAY:\n{sell_lines}\n\n"
                f"STILL OPEN:\n{open_lines}\n"
            )
            summary = self.brain._query_gemini(prompt)
            header = f"🌙 <b>End of Day — {today}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
            self.telegram.send_eod_summary(header + summary)
            logger.success("📬 EOD summary sent via Telegram.")
        except Exception as e:
            logger.error(f"❌ EOD summary failed: {e}")

    def wait_for_next_guardian_check(self):
        """Sleep until the next 5-minute boundary."""
        waw_tz = pytz.timezone("Europe/Warsaw")
        now = datetime.now(waw_tz)
        minutes_past_5 = now.minute % 5
        minutes_until = (5 - minutes_past_5) if minutes_past_5 > 0 else 5
        next_check = (now + timedelta(minutes=minutes_until)).replace(second=0, microsecond=0)

        minutes_past_30 = now.minute % 30
        minutes_until_full = (30 - minutes_past_30) if minutes_past_30 > 0 else 30
        next_full = (now + timedelta(minutes=minutes_until_full)).replace(second=0, microsecond=0)

        sleep_secs = max(5, (next_check - now).total_seconds())
        logger.info(f"⏳ Next Guardian check at {next_check.strftime('%H:%M')} | Next full cycle at {next_full.strftime('%H:%M')}")
        time.sleep(sleep_secs)


if __name__ == "__main__":
    bot = GlomeriatoV01(mode="demo")
    while _running:
        try:
            now_waw = datetime.now(pytz.timezone("Europe/Warsaw"))

            time_float = now_waw.hour + (now_waw.minute / 60.0)
            market_open = now_waw.weekday() < 5 and (8.8 <= time_float <= 22.5)
            if market_open and now_waw.hour % 2 == 0 and now_waw.minute < 1 and now_waw.hour != bot._last_digest_hour:
                bot._last_digest_hour = now_waw.hour
                bot.send_digest()

            if now_waw.hour == 22 and now_waw.minute == 30 and not bot._eod_sent_today:
                bot._eod_sent_today = True
                bot.send_eod_summary()

            if now_waw.hour == 0 and now_waw.minute < 5:
                bot._eod_sent_today = False

            if now_waw.minute % 30 < 1:
                bot.run_cycle()
            else:
                console.rule(f"[bold yellow]🛡️ GUARDIAN PASS: {now_waw.strftime('%H:%M:%S')}")
                guardian_exits = bot.run_guardian_pass()
                if guardian_exits:
                    exit_table = Table(title="Guardian Exit Summary", title_style="bold yellow", border_style="yellow")
                    exit_table.add_column("Ticker", style="cyan")
                    exit_table.add_column("Type", style="white")
                    exit_table.add_column("Result", style="red")
                    for log in guardian_exits:
                        exit_table.add_row(log['ticker'], log['type'], log['reason'])
                    console.print("\n")
                    console.print(exit_table)
        except Exception as e:
            logger.error(f"❌ Cycle Error: {e}")
        if _running:
            bot.wait_for_next_guardian_check()
    logger.info("🛑 Graceful shutdown complete.")
