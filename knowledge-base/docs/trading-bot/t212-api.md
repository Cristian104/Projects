# Trading 212 API Integration

This document outlines the technical details and financial logic of the Trading 212 (Invest) API integration within the Glomeriato trading bot.

## Overview
The bot interacts with Trading 212 via their official REST API. The integration is encapsulated in the `Trading212` class (`bot/app/connectors/trading212.py`) and used by the main strategy logic for order execution, portfolio synchronization, and balance tracking.

## Authentication
Authentication is handled via Basic Auth using an API Key and Secret Key.

**Environment Variables (`bot/.env`):**
- `T212_API_KEY`: Your Trading 212 API key.
- `T212_SECRET_KEY`: Your Trading 212 secret key.
- `T212_BASE_URL`: (Optional) Defaults to `https://demo.trading212.com/api/v0`. Change to the live endpoint for production.

## Financial Logic & FX Fees

### The 0.15% FX Rule
Trading 212 charges a **0.15% FX conversion fee** on trades involving currencies different from the account's base currency. Glomeriato accounts for this fee in all its calculations to prevent over-allocation and ensure accurate PnL tracking.

- **Buy Orders**: When calculating the quantity to buy, the bot divides the allocated capital by `1.0015` (e.g., `qty = (spendable / 1.0015) / price`).
- **Sell Orders**: When logging transactions, the bot deducts `0.15%` from the total proceeds.

### Quantity Calculations & Rounding
The bot applies specific rounding rules based on the stock exchange to comply with broker requirements:
- **Warsaw (.WA) & Madrid (.MC)**: Quantities are cast to `int`. 
- **Warsaw (.WA) limit**: A safety cap of 60 shares is applied to Warsaw trades.
- **Others (US/EU)**: Quantities are rounded to **2 decimal places**.

## Market Hours (Warsaw Time)
The bot operates on a dynamic schedule based on European and US market hours, with built-in buffers:

| Market | Open (CET/CEST) | Close (CET/CEST) |
| :--- | :--- | :--- |
| **Europe** | 08:48 (8.8h) | 17:42 (17.7h) |
| **USA** | 14:30 (14.5h) | 22:30 (22.5h) |

- **Deep Sleep**: On weekends, the bot enters a complete sleep state.
- **Low Power Mode**: During weekday off-hours, the bot performs a minimal scan (3 random stocks) once per hour to maintain temporal memory.

## Technical Details

### Rate Limiting
To avoid `429 Too Many Requests` errors, the connector implements:
- **Min Interval**: A minimum of **500ms** between consecutive API calls.
- **Backoff**: Automatic exponential backoff for 429 responses (retries up to 3 times).

### Ticker Mapping
Yahoo Finance tickers used for scanning are mapped to Trading 212 instrument codes using `app/data/ticker_map.json`.
- **Default Logic**: If no mapping is found, it replaces dots with underscores and appends `_EQ` (e.g., `AAPL` -> `AAPL_EQ`, `ASML.AS` -> `ASML_AS_EQ`).

### Order Execution
- **Extended Hours**: Market orders are placed with `extendedHours: True` enabled.
- **Pending Orders**: The bot automatically cancels "stale" pending orders that are older than **90 minutes** during the synchronization phase.

## API Endpoints Used

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/equity/account/cash` | `GET` | Fetch free equity/balance. |
| `/equity/portfolio` | `GET` | Retrieve active positions and quantities. |
| `/equity/orders` | `GET` | List all open orders. |
| `/equity/orders/market` | `POST` | Execute a market buy/sell order. |
| `/equity/orders/{id}` | `DELETE` | Cancel a specific pending order. |

## Synchronization (`sync_reality`)
The bot runs a synchronization routine at the start of every 30-minute cycle:
1. **Ghost Purge**: If a position exists in the DB but not on the broker, it is marked as closed (`SYNC_PURGE`).
2. **Position Restore**: If a position exists on the broker but not in the DB, the bot fetches technical data and "adopts" the position into the database.
3. **Stale Order Cleanup**: Cancels pending orders older than 90 minutes.
