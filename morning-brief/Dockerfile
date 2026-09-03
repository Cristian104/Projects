FROM python:3.12-slim

WORKDIR /app

# Install system build dependencies and git for dynamic versioning
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt1-dev git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8009

ENTRYPOINT ["./entrypoint.sh"]
