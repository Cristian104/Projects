# =============================================================================
# Glomeriato — FastAPI Dashboard Server
# Replaces the Streamlit dashboard (app/dashboard.py).
# Same port (8501), same data sources, superior rendering.
# =============================================================================

from __future__ import annotations

import base64
import csv
import hmac
import hashlib
import io
import os
import re
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg2
import psycopg2.pool
from fastapi import FastAPI, Form, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

# ─── Paths & constants ────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
LOG_PATH  = Path("/app/app.log")
TZ_WARSAW = ZoneInfo("Europe/Warsaw")

COOKIE_NAME  = "dash_session"
AUTH_MAX_AGE = 8 * 3600   # 8 hours in seconds

# ─── App wiring ───────────────────────────────────────────────────────────────
app = FastAPI(title="Glomeriato Terminal", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ─── Config (env-var based, same as dashboard.py) ─────────────────────────────
_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "glomeriato")
_DB_HOST  = os.getenv("DB_HOST", "remastered_db")
_DB_NAME  = os.getenv("DB_NAME", "remastered_core")
_DB_USER  = os.getenv("DB_USER", "admin")
_DB_PASS  = os.getenv("DB_PASSWORD", "remastered_secure_pass")
_T212_KEY = os.getenv("T212_API_KEY", "").strip()
_T212_SEC = os.getenv("T212_SECRET_KEY", "").strip()

# ─── Cookie auth (stdlib HMAC — no extra deps) ────────────────────────────────

def _make_token() -> str:
    ts  = str(int(time.time())).encode()
    sig = hmac.new(_PASSWORD.encode(), ts, hashlib.sha256).hexdigest()
    raw = ts.decode() + ":" + sig
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _verify_token(token: str) -> bool:
    try:
        raw     = base64.urlsafe_b64decode(token.encode()).decode()
        ts_str, sig = raw.split(":", 1)
        age = time.time() - int(ts_str)
        if age < 0 or age > AUTH_MAX_AGE:
            return False
        expected = hmac.new(_PASSWORD.encode(), ts_str.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False


def _is_auth(request: Request) -> bool:
    token = request.cookies.get(COOKIE_NAME)
    return bool(token and _verify_token(token))


# ─── DB pool ──────────────────────────────────────────────────────────────────
_pool: psycopg2.pool.SimpleConnectionPool | None = None


def _get_pool() -> psycopg2.pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            1, 5,
            host=_DB_HOST, database=_DB_NAME,
            user=_DB_USER, password=_DB_PASS,
        )
    return _pool


def _db_query(sql: str, params=None) -> list[dict]:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        pool.putconn(conn)


def _serialize(rows: list[dict]) -> list[dict]:
    """Convert Decimal/datetime objects so JSONResponse can handle them."""
    import decimal
    out = []
    for r in rows:
        row = {}
        for k, v in r.items():
            if isinstance(v, datetime):
                row[k] = v.isoformat()
            elif isinstance(v, decimal.Decimal):
                row[k] = float(v)
            else:
                row[k] = v
        out.append(row)
    return out


# ─── T212 connector (best-effort, never crashes the server) ───────────────────
_t212 = None


def _t212_client():
    global _t212
    if _t212 is None and _T212_KEY:
        try:
            from app.connectors.trading212 import Trading212
            _t212 = Trading212(_T212_KEY, _T212_SEC)
        except Exception as exc:
            logger.warning(f"T212 connector init failed: {exc}")
    return _t212


# ─── Market / time helpers ────────────────────────────────────────────────────
_EU_OPEN  = (8,  50)
_EU_CLOSE = (17, 42)
_US_OPEN  = (14, 30)
_US_CLOSE = (22, 30)


def _market_status() -> dict:
    now = datetime.now(TZ_WARSAW)
    t   = now.hour * 60 + now.minute
    eu  = (_EU_OPEN[0]  * 60 + _EU_OPEN[1])  <= t <= (_EU_CLOSE[0] * 60 + _EU_CLOSE[1])
    us  = (_US_OPEN[0]  * 60 + _US_OPEN[1])  <= t <= (_US_CLOSE[0] * 60 + _US_CLOSE[1])
    if eu and us:
        label, css = "EU + US LIVE", "market-both"
    elif eu:
        label, css = "EU LIVE", "market-eu"
    elif us:
        label, css = "US LIVE", "market-us"
    else:
        label, css = "MARKETS CLOSED", "market-closed"
    return {"market": label, "css": css, "clock": now.strftime("%H:%M:%S")}


def _next_cycle_secs() -> int:
    now = datetime.now(TZ_WARSAW)
    if now.minute < 30:
        nxt = now.replace(second=0, microsecond=0, minute=30)
    else:
        nxt = (now.replace(second=0, microsecond=0, minute=0) + timedelta(hours=1))
    return max(0, int((nxt - now).total_seconds()))


# ─── Log reader / colorizer ───────────────────────────────────────────────────
def _read_log_lines(n: int = 150) -> list[str]:
    if not LOG_PATH.exists():
        return ["<span class='log-info'>No log file found at /app/app.log</span>"]
    try:
        with LOG_PATH.open("r", errors="replace") as fh:
            raw_lines = deque(fh, maxlen=n)
    except OSError:
        return ["<span class='log-info'>Unable to read log file.</span>"]

    result = []
    for line in raw_lines:
        line = line.rstrip()
        upper = line.upper()
        esc   = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if "ERROR" in upper or "CRITICAL" in upper:
            css = "log-error"
        elif "WARNING" in upper or "WARN" in upper:
            css = "log-warning"
        elif "SUCCESS" in upper:
            css = "log-success"
        else:
            css = "log-info"
        result.append(f'<span class="{css}">{esc}</span>')
    return result


# ─── Auth guard helpers ────────────────────────────────────────────────────────
def _auth_redirect() -> RedirectResponse:
    return RedirectResponse("/login", status_code=302)


def _api_guard(request: Request) -> JSONResponse | None:
    if not _is_auth(request):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return None


# =============================================================================
# HTML Routes
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not _is_auth(request):
        return _auth_redirect()
    return templates.TemplateResponse(request=request, name="dashboard.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _is_auth(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password == _PASSWORD:
        token = _make_token()
        resp  = RedirectResponse("/", status_code=302)
        resp.set_cookie(
            COOKIE_NAME, token,
            max_age=AUTH_MAX_AGE, httponly=True, samesite="lax",
        )
        return resp
    return templates.TemplateResponse(
        request=request, name="login.html",
        context={"error": "Invalid password"},
        status_code=401,
    )


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp


# =============================================================================
# JSON API
# =============================================================================

@app.get("/api/status")
async def api_status(request: Request):
    if (e := _api_guard(request)):
        return e
    return JSONResponse(_market_status())


@app.get("/api/kpi")
async def api_kpi(request: Request):
    if (e := _api_guard(request)):
        return e
    try:
        rows = _db_query("SELECT entry_price, quantity FROM active_positions")
    except Exception:
        rows = []

    cash = 0.0
    try:
        t = _t212_client()
        if t:
            cash = t.get_cash_balance()
    except Exception:
        pass

    return JSONResponse({
        "cash":             round(float(cash), 2),
        "positions_count":  len(rows),
        "pnl":              0.0,   # live P&L comes from /api/portfolio (T212 ppl field)
        "next_cycle_secs":  _next_cycle_secs(),
    })


@app.get("/api/positions")
async def api_positions(request: Request):
    if (e := _api_guard(request)):
        return e
    try:
        rows = _db_query(
            "SELECT id, ticker, entry_price, highest_price, entry_atr, quantity, "
            "tier, entry_conviction, timestamp "
            "FROM active_positions ORDER BY timestamp DESC"
        )
        return JSONResponse(_serialize(rows))
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/portfolio")
async def api_portfolio(request: Request):
    if (e := _api_guard(request)):
        return e
    try:
        t = _t212_client()
        if t:
            data = t.get_detailed_portfolio()
            return JSONResponse(data if isinstance(data, list) else [])
        return JSONResponse([])
    except Exception as exc:
        logger.warning(f"Portfolio fetch failed: {exc}")
        return JSONResponse([])


@app.get("/api/logs")
async def api_logs(request: Request, filter: str = "all"):
    if (e := _api_guard(request)):
        return e
    try:
        rows = _db_query(
            "SELECT id, ticker, sentiment_score, analyst_reason, manager_order, "
            "manager_conviction, manager_reasoning, timestamp "
            "FROM intelligence_logs ORDER BY timestamp DESC LIMIT 200"
        )
        rows = _serialize(rows)
        if filter == "trades":
            rows = [r for r in rows if r.get("manager_order") not in ("HOLD", None, "")]
        elif filter == "high":
            rows = [r for r in rows if float(r.get("sentiment_score") or 0) >= 70]
        return JSONResponse(rows)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/summary")
async def api_summary(request: Request):
    if (e := _api_guard(request)):
        return e
    try:
        rows = _db_query(
            "SELECT summary, timestamp FROM market_summaries ORDER BY timestamp DESC LIMIT 1"
        )
        if rows:
            r = _serialize(rows)[0]
            return JSONResponse(r)
        return JSONResponse({"summary": None, "timestamp": None})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/console")
async def api_console(request: Request):
    if (e := _api_guard(request)):
        return e
    return JSONResponse({"lines": _read_log_lines(150)})


@app.get("/api/pending")
async def api_pending(request: Request):
    if (e := _api_guard(request)):
        return e
    try:
        t = _t212_client()
        if t:
            data = t.get_pending_orders()
            return JSONResponse(data if isinstance(data, list) else [])
        return JSONResponse([])
    except Exception:
        return JSONResponse([])


# =============================================================================
# CSV Exports
# =============================================================================

def _csv_stream(rows: list[dict], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow({k: ("" if v is None else str(v)) for k, v in r.items()})
    else:
        buf.write("no data\n")
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/export/intelligence")
async def export_intelligence(request: Request):
    if not _is_auth(request):
        return _auth_redirect()
    rows = _serialize(_db_query("SELECT * FROM intelligence_logs ORDER BY timestamp DESC"))
    return _csv_stream(rows, "intelligence_logs.csv")


@app.get("/export/transactions")
async def export_transactions(request: Request):
    if not _is_auth(request):
        return _auth_redirect()
    rows = _serialize(_db_query("SELECT * FROM transaction_history ORDER BY timestamp DESC"))
    return _csv_stream(rows, "transaction_history.csv")


@app.get("/export/positions")
async def export_positions(request: Request):
    if not _is_auth(request):
        return _auth_redirect()
    rows = _serialize(_db_query("SELECT * FROM active_positions ORDER BY timestamp DESC"))
    return _csv_stream(rows, "active_positions.csv")
