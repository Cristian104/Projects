import requests
from datetime import datetime
import pytz
from app.core.config import settings
from loguru import logger

class TelegramBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def _send(self, msg: str):
        try:
            requests.post(self.base_url, json={
                "chat_id": self.chat_id,
                "text": msg,
                "parse_mode": "HTML"
            }, timeout=5)
        except Exception as e:
            logger.error(f"⚠️ Telegram Error: {e}")

    def send_trade_alert(self, ticker, amount, shares, sentiment):
        """Sends a formatted trade alert."""
        msg = (
            f"🚀 <b>TRADE EXECUTED: {ticker}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💵 <b>Invested:</b> {amount:,.2f} PLN\n"
            f"📦 <b>Shares:</b> {shares:.4f}\n"
            f"🧠 <b>AI Sentiment:</b> {sentiment:.2f}\n"
            f"🤖 <i>Remastered Bot V2</i>"
        )
        self._send(msg)

    def send_message(self, text):
        self._send(text)

    def send_digest(self, events: list):
        """Sends a 2-hour compilation of trade events."""
        waw = pytz.timezone("Europe/Warsaw")
        now = datetime.now(waw).strftime("%H:%M")
        if not events:
            self._send(f"📊 <b>2h Update ({now})</b>\nNo trades this period — positions monitored.")
            return
        icon_map = {"BUY": "🟢", "SELL_ALL": "🔴", "SELL_PARTIAL_30": "🟡"}
        lines = [f"📊 <b>2h Trade Digest ({now})</b>", "━━━━━━━━━━━━━━━━━━━━━━"]
        for e in events:
            icon = icon_map.get(e["type"], "⚪")
            lines.append(f"{icon} <b>{e['ticker']}</b> — {e['type']} @ {e['price']:.2f} {e.get('note', '')}")
        self._send("\n".join(lines))

    def send_eod_summary(self, summary_text: str):
        """Sends the end-of-day AI-generated summary."""
        self._send(summary_text)
