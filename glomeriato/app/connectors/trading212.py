import os
import requests
import json
import time
from loguru import logger

class Trading212:
    _last_request_time: float = 0.0
    _min_interval: float = 0.5  # 500ms minimum between requests

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.base_url = os.getenv("T212_BASE_URL", "https://demo.trading212.com/api/v0").strip()

        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

        logger.info(f"🔌 T212 Connector V2.6: Authenticated (Key: {self.api_key[:8]}...)")
        self._load_mappings()

    def _rate_limit(self):
        """Ensures at least _min_interval seconds between consecutive API calls."""
        elapsed = time.time() - Trading212._last_request_time
        wait = self._min_interval - elapsed
        if wait > 0:
            time.sleep(wait)
        Trading212._last_request_time = time.time()

    def _load_mappings(self):
        mapping_path = "app/data/ticker_map.json"
        self.mappings = {}
        try:
            with open(mapping_path, "r") as f:
                self.mappings = json.load(f)
        except:
            logger.warning("⚠️ No ticker_map.json found.")

    def get_cash_balance(self, retries=3) -> float:
        self._rate_limit()
        endpoint = f"{self.base_url}/equity/account/cash"
        for attempt in range(retries):
            try:
                res = requests.get(endpoint, headers=self.headers, timeout=10)
                if res.status_code == 200:
                    return float(res.json().get('free', 0.0))
                elif res.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
            except: pass
        return 0.0

    def cancel_pending_orders(self):
        """Cancels orders that have been pending for more than 90 minutes (truly stale)."""
        from datetime import datetime, timezone
        self._rate_limit()
        endpoint = f"{self.base_url}/equity/orders"
        try:
            res = requests.get(endpoint, headers=self.headers, timeout=10)
            if res.status_code == 200:
                orders = res.json()
                now = datetime.now(timezone.utc)
                for order in orders:
                    if order.get('status') not in ['NEW', 'LOCAL', 'PENDING']:
                        continue
                    created_raw = order.get('dateCreated') or order.get('creationTime') or order.get('time')
                    if created_raw:
                        try:
                            created = datetime.fromisoformat(created_raw.replace('Z', '+00:00'))
                            age_minutes = (now - created).total_seconds() / 60
                            if age_minutes < 90:
                                logger.debug(f"⏳ Order for {order.get('ticker')} is {age_minutes:.0f}min old — keeping")
                                continue
                        except Exception:
                            pass
                    del_endpoint = f"{self.base_url}/equity/orders/{order['id']}"
                    requests.delete(del_endpoint, headers=self.headers, timeout=10)
                    logger.info(f"🗑️ Canceled stale pending order for {order.get('ticker')}")
        except Exception as e:
            logger.error(f"❌ Error clearing pending orders: {e}")

    def get_pending_orders(self):
        """Retrieves a list of pending orders from the broker."""
        self._rate_limit()
        endpoint = f"{self.base_url}/equity/orders"
        pending = []
        try:
            res = requests.get(endpoint, headers=self.headers, timeout=10)
            if res.status_code == 200:
                orders = res.json()
                for order in orders:
                    if order.get('status') in ['NEW', 'LOCAL', 'PENDING']:
                        pending.append(order)
        except Exception as e:
            logger.error(f"❌ Error fetching pending orders: {e}")
        return pending

    def get_owned_tickers(self):
        """Returns a list of instrument codes actually owned in the T212 portfolio."""
        self._rate_limit()
        endpoint = f"{self.base_url}/equity/portfolio"
        try:
            res = requests.get(endpoint, headers=self.headers, timeout=10)
            if res.status_code == 200:
                portfolio = res.json()
                return [pos.get('ticker') for pos in portfolio]
            return None
        except:
            return None

    def get_detailed_portfolio(self):
        """Returns the full list of open positions with detailed metrics."""
        self._rate_limit()
        endpoint = f"{self.base_url}/equity/portfolio"
        try:
            res = requests.get(endpoint, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching detailed portfolio: {e}")
            return []

    def get_position_quantity(self, yahoo_ticker: str) -> float | None:
        """Returns the actual quantity held in T212 for a given Yahoo ticker, or None if not found."""
        mapped = self.mappings.get(yahoo_ticker, f"{yahoo_ticker.replace('.', '_')}_EQ")
        portfolio = self.get_detailed_portfolio()
        for pos in portfolio:
            if pos.get('ticker') == mapped:
                return float(pos.get('quantity', 0))
        return None

    def place_order(self, ticker: str, quantity: float):
        self._rate_limit()
        mapped_ticker = self.mappings.get(ticker, f"{ticker.replace('.', '_')}_EQ")
        endpoint = f"{self.base_url}/equity/orders/market"
        
        if any(x in mapped_ticker for x in ["_WA", "_MC", "e_EQ"]):
            clean_qty = int(abs(quantity))
        else:
            clean_qty = round(abs(quantity), 2)
            
        final_qty = clean_qty if quantity > 0 else -clean_qty
        if final_qty == 0: return False

        payload = {"ticker": mapped_ticker, "quantity": final_qty, "extendedHours": True}
        try:
            res = requests.post(endpoint, headers=self.headers, json=payload, timeout=10)
            if res.status_code == 200:
                logger.success(f"💎 ORDER PLACED: {mapped_ticker} | Qty: {final_qty}")
                return True
            else:
                try:
                    err_type = res.json().get("type", "")
                except Exception:
                    err_type = ""
                if "extended-hours-trading-not-allowed" in err_type:
                    logger.warning(f"🕐 {mapped_ticker}: Market closed — order will execute at next open.")
                    return "MARKET_CLOSED"
                logger.error(f"❌ ORDER REJECTED {res.status_code}: {res.text}")
                return False
        except Exception as e:
            logger.error(f"❌ API Timeout: {e}")
            return False
