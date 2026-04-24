# GEMINI.md - Glomeriato V2.1 Instructional Context

## Project Overview
**Glomeriato V2.1 (The Transatlantic Snowball)** is an autonomous algorithmic trading bot designed specifically for **Trading 212 (Invest)**. It employs a sophisticated dual-agent AI architecture powered by **DeepSeek-R1** (via Ollama) to synthesize market sentiment with technical analysis.

### Core Architecture
- **Dual-Agent Brain (`app/intelligence/`)**: 
    - **Analyst (8b)**: Rapid sentiment triage of RSS news feeds.
    - **Manager (14b)**: Deep reasoning, technical cross-checking, and JSON order generation.
- **Risk Engine (`app/trading/guardian.py`)**: Implements an "Exit Matrix" featuring ATR-based trailing stops, profit ladders (partial sells), and time-decay liquidations.
- **Market Sentinel (`app/trading/sentinel.py`)**: High-speed technical scanner filtering for liquidity, volatility, and mean-reversion triggers.
- **Financial Audit Trail**: Precision tracking of the **0.15% T212 FX conversion fee** and comprehensive transaction logging for PnL accuracy.
- **Data Persistence**: PostgreSQL (`remastered_core`) for active positions, intelligence history, and financial audits.

### Key Technologies
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (asyncpg), Loguru.
- **AI**: Ollama (DeepSeek-R1:8b, DeepSeek-R1:14b).
- **Frontend**: Streamlit (Institutional Intelligence Dashboard).
- **DevOps**: Docker Compose (Profiles: `official`, `lab`), Bash-based deployment scripts.

---

## Building and Running

### Development Commands
- **Relaunch System**: `./relaunch.sh` (Handles directory setup, git staging on `onDev`, and starting official containers).
- **Fresh Start**: `./fresh_start.sh` (Truncates database tables and restarts containers).
- **Manual Launch (Official)**: `sudo docker compose --profile official up -d --build`
- **Manual Launch (Sandbox/Lab)**: `sudo docker compose --profile lab up -d --build`
- **View Logs**: `docker logs -f bot_official`
- **Dashboard**: `streamlit run app/dashboard.py` (Local development) or via container at `:8501`.

### Maintenance
- **Backups**: Managed by `scripts/backup_manager.sh`, creating numbered rotations in `./backups/`.
- **Universe Updates**: Tickers are managed in `app/data/targets.json`.

---

## Development Conventions

### 1. Workflow
- Always develop on the `onDev` branch.
- Use the **Research -> Strategy -> Execution** lifecycle for all changes.
- Ensure all financial calculations account for the **0.15% FX fee** logic established in `Trading212.place_order`.

### 2. Code Style & Standards
- **Logging**: Use `loguru` for all system events.
- **Typing**: Use Pydantic models for configuration and strict type hinting where possible.
- **Database**: All position-tracking changes must be reflected in `app/core/memory.py` (the DBManager).
- **AI Integration**: Maintain the temperature at `0.1` for AI calls to ensure logical consistency and prevent hallucinations.

### 3. Risk Management First
- The **Guardian** module is the source of truth for exits. Do not bypass the ATR-based stop-loss logic.
- The **Sentinel** must validate liquidity (Volume * Price > 500k) before any asset is passed to the AI brain.

---

## Directory Overview
- `app/connectors`: Broker (T212) and API integrations.
- `app/core`: Configuration, Database Schema, and Memory management.
- `app/intelligence`: AI Brain logic and News Aggregation.
- `app/trading`: Strategy execution, Risk management (Guardian), and Scanning (Sentinel).
- `app/data`: JSON targets and ticker mappings.
- `scripts`: Maintenance and deployment automation.
- `data_lake`: Persistent storage for intelligence archives.
