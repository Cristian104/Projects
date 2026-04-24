import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from loguru import logger

class DBManager:
    def __init__(self, host="remastered_db"):
        self.host = host
        self.db_name = os.getenv("DB_NAME", "remastered_core")
        self.user = os.getenv("DB_USER", "admin")
        self.password = os.getenv("DB_PASSWORD", "remastered_secure_pass")
        self._connect_with_retry()
        self._initialize_db()

    def get_connection(self):
        """Standard connection factory for PostgreSQL."""
        return psycopg2.connect(
            host=self.host,
            database=self.db_name,
            user=self.user,
            password=self.password
        )

    def _connect_with_retry(self):
        for i in range(5):
            try:
                conn = self.get_connection()
                conn.close()
                logger.success("🗄️ Database connected successfully!")
                return
            except Exception:
                time.sleep(2)
        logger.error("Failed to connect to the database.")

    def _initialize_db(self):
        """Initializes the V0.1 Dual-Table Architecture."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # 1. Active Positions (Current Reality)
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS active_positions (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(50),
                        entry_price NUMERIC,
                        highest_price NUMERIC,
                        entry_atr NUMERIC,
                        quantity NUMERIC,
                        tier INTEGER,
                        entry_conviction NUMERIC DEFAULT 0.5,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
                    
                    # 2. Intelligence Logs (AI reasoning backup)
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS intelligence_logs (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(50),
                        sentiment_score NUMERIC,
                        analyst_reason TEXT,
                        manager_order VARCHAR(50),
                        manager_conviction NUMERIC,
                        manager_reasoning TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

                    # 3. Transaction History (Financial Audit / V0.2 Data Source)
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS transaction_history (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(50),
                        action VARCHAR(20),
                        quantity NUMERIC,
                        price_executed NUMERIC,
                        fee_cost NUMERIC,
                        total_value_pln NUMERIC,
                        account_balance_after NUMERIC,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
                    
                    # 4. Market Summaries (Global AI Summary)
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS market_summaries (
                        id SERIAL PRIMARY KEY,
                        summary TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

                    # 5. Bot settings (key-value store for runtime configuration)
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS bot_settings (
                        key        VARCHAR(64) PRIMARY KEY,
                        value      TEXT        NOT NULL,
                        updated_at TIMESTAMP   DEFAULT NOW()
                    );
                    INSERT INTO bot_settings (key, value)
                    VALUES ('brain_mode', 'local')
                    ON CONFLICT (key) DO NOTHING;
                    """)

                    # 6. Consolidate duplicate active_positions rows (idempotent migration)
                    cur.execute("""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_name = 'active_positions'
                        ) AND (
                            SELECT COUNT(*) FROM (
                                SELECT ticker FROM active_positions GROUP BY ticker HAVING COUNT(*) > 1
                            ) dups
                        ) > 0 THEN
                            WITH consolidated AS (
                                SELECT
                                    ticker,
                                    SUM(quantity * entry_price) / SUM(quantity)              AS wavg_entry,
                                    SUM(quantity)                                             AS total_qty,
                                    MAX(highest_price)                                        AS max_highest,
                                    (array_agg(entry_atr       ORDER BY timestamp DESC))[1]  AS latest_atr,
                                    (array_agg(entry_conviction ORDER BY timestamp DESC))[1] AS latest_conv,
                                    MAX(tier)                                                 AS max_tier,
                                    MIN(timestamp)                                            AS earliest_ts
                                FROM active_positions
                                GROUP BY ticker HAVING COUNT(*) > 1
                            ),
                            deleted AS (
                                DELETE FROM active_positions
                                WHERE ticker IN (SELECT ticker FROM consolidated)
                            )
                            INSERT INTO active_positions
                                (ticker, entry_price, highest_price, entry_atr, quantity, tier, entry_conviction, timestamp)
                            SELECT ticker, wavg_entry, max_highest, latest_atr, total_qty, max_tier, latest_conv, earliest_ts
                            FROM consolidated;
                        END IF;
                    END $$;
                    """)

                    # 7. Unique constraint on ticker (idempotent)
                    cur.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_active_positions_ticker
                        ON active_positions (ticker);
                    """)

                conn.commit()
            logger.info("🗄️ Database tables verified (Dual-Table Ready).")
        except Exception as e:
            logger.error(f"DB Init Error: {e}")

    # --- 🧠 INTELLIGENCE METHODS ---

    def log_decision(self, ticker: str, score: float, reason: str, order: str, conv: float, manager_reason: str):
        """Logs AI logic for future dataset training."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO intelligence_logs (ticker, sentiment_score, analyst_reason, manager_order, manager_conviction, manager_reasoning)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """, (str(ticker), float(score), str(reason), str(order), float(conv), str(manager_reason)))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging decision: {e}")

    def save_market_summary(self, summary_text: str):
        """Saves the global AI cycle summary."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO market_summaries (summary) VALUES (%s);", (str(summary_text),))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving market summary: {e}")

    def get_ticker_history(self, ticker: str, limit: int = 3):
        """Retrieves recent AI thoughts for this ticker to provide 'Memory' to the Brain."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT sentiment_score, manager_order, manager_reasoning, timestamp 
                        FROM intelligence_logs 
                        WHERE ticker = %s 
                        ORDER BY timestamp DESC LIMIT %s;
                    """, (str(ticker), int(limit)))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching history for {ticker}: {e}")
            return []

    def get_recent_sales(self, ticker: str, hours: int = 4):
        """Helper for Cooldown Guard: Checks if a ticker was sold recently."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM intelligence_logs
                        WHERE ticker = %s AND manager_order = 'SELL'
                        AND timestamp > NOW() - INTERVAL '%s hours';
                    """, (ticker, int(hours)))
                    return cur.fetchone()
        except:
            return None

    def was_recently_sold(self, ticker: str, hours: int = 2) -> bool:
        """True if ticker had a SELL/SELL_PARTIAL in the last N hours.
        Prevents sync_reality from restoring positions still settling."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM transaction_history
                        WHERE ticker = %s
                          AND action IN ('SELL', 'SELL_PARTIAL')
                          AND timestamp > NOW() - INTERVAL '%s hours';
                    """, (str(ticker), int(hours)))
                    return cur.fetchone() is not None
        except:
            return False

    # --- 💰 TRANSACTION & FINANCIAL METHODS ---

    def log_transaction(self, ticker: str, action: str, qty: float, price: float, fee: float, balance: float):
        """Audit function to record exact execution costs and account impact."""
        try:
            total_val = float(qty) * float(price)
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO transaction_history (ticker, action, quantity, price_executed, fee_cost, total_value_pln, account_balance_after)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (ticker, action, float(qty), float(price), float(fee), total_val, float(balance)))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to log financial transaction for {ticker}: {e}")

    def open_position(self, ticker: str, entry_price: float, entry_atr: float, quantity: float, conviction: float = 0.5, timestamp=None):
        """Logs a position as active for the Guardian to track. UPSERT: adds to existing position (weighted avg entry)."""
        try:
            p, a, q, c = float(entry_price), float(entry_atr), float(quantity), float(conviction)
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    if timestamp:
                        # Sync-restore path: DO NOTHING if position already exists
                        cur.execute("""
                        INSERT INTO active_positions (ticker, entry_price, highest_price, entry_atr, quantity, tier, entry_conviction, timestamp)
                        VALUES (%s, %s, %s, %s, %s, 0, %s, %s)
                        ON CONFLICT (ticker) DO NOTHING;
                        """, (str(ticker), p, p, a, q, c, timestamp))
                    else:
                        # New BUY path: accumulate into existing row (weighted avg entry)
                        cur.execute("""
                        INSERT INTO active_positions (ticker, entry_price, highest_price, entry_atr, quantity, tier, entry_conviction)
                        VALUES (%s, %s, %s, %s, %s, 0, %s)
                        ON CONFLICT (ticker) DO UPDATE SET
                            quantity         = active_positions.quantity + EXCLUDED.quantity,
                            entry_price      = (active_positions.entry_price * active_positions.quantity
                                                + EXCLUDED.entry_price * EXCLUDED.quantity)
                                               / (active_positions.quantity + EXCLUDED.quantity),
                            entry_atr        = EXCLUDED.entry_atr,
                            entry_conviction = GREATEST(active_positions.entry_conviction, EXCLUDED.entry_conviction),
                            highest_price    = GREATEST(active_positions.highest_price, EXCLUDED.highest_price);
                        """, (str(ticker), p, p, a, q, c))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ DB Error logging position {ticker}: {e}")

    def close_position(self, ticker: str, current_price: float, reason: str):
        """Removes an active position (Archiving should happen via log_transaction before this)."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM active_positions WHERE ticker = %s;", (str(ticker),))
                conn.commit()
        except Exception: pass

    def get_transactions_today(self, date_str: str) -> list:
        """Returns all transactions from today for the EOD summary."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT ticker, action, quantity, price_executed AS price, fee_cost, timestamp
                        FROM transaction_history
                        WHERE DATE(timestamp) = %s
                        ORDER BY timestamp ASC;
                    """, (date_str,))
                    cols = [d[0] for d in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"❌ get_transactions_today failed: {e}")
            return []

    def get_active_positions(self):
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM active_positions;")
                    return cur.fetchall()
        except Exception: return []

    def update_highest_price(self, ticker: str, current_price: float):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE active_positions SET highest_price = %s WHERE ticker = %s;", (float(current_price), str(ticker)))
                conn.commit()
        except Exception: pass

    def update_position_after_partial_sell(self, ticker: str, new_qty: float, new_tier: int):
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE active_positions
                        SET quantity = %s, tier = %s
                        WHERE ticker = %s;
                    """, (float(new_qty), int(new_tier), str(ticker)))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ DB Error updating partial sell for {ticker}: {e}")

    # --- ⚙️ BOT SETTINGS METHODS ---

    def get_setting(self, key: str) -> str | None:
        """Fetch a runtime setting from bot_settings. Returns None if missing."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT value FROM bot_settings WHERE key = %s;", (str(key),))
                    row = cur.fetchone()
                    return row[0] if row else None
        except Exception as e:
            logger.error(f"❌ DB Error fetching setting '{key}': {e}")
            return None

    def set_setting(self, key: str, value: str) -> None:
        """Upsert a runtime setting in bot_settings."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO bot_settings (key, value, updated_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT (key) DO UPDATE
                            SET value = EXCLUDED.value, updated_at = NOW();
                    """, (str(key), str(value)))
                conn.commit()
        except Exception as e:
            logger.error(f"❌ DB Error setting '{key}': {e}")
