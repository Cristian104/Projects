FROM python:3.12-slim

WORKDIR /app

# 1. Install system tools (Added postgresql-client for backups)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    util-linux \
    tzdata \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 3. Copy project files
COPY pyproject.toml poetry.lock* ./

# 4. Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# 5. Copy the code
COPY . .

# 6. Ensure scripts are executable
RUN chmod +x scripts/backup_manager.sh

# 7. Run! (ALWAYS LAST)
CMD ["python", "-m", "app.trading.strategy"]
