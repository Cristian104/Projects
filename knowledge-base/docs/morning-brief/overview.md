!!! info Project: Morning Brief
> The Morning Brief is an automated news pipeline designed to deliver condensed, AI-briefed news via Telegram, accessible through a dedicated Flask web application. It functions as an RSS collector, processing articles and storing them in an SQLite database for quick consumption.

## Overview

The `morning-brief` service orchestrates the collection, processing, and presentation of news articles. Its primary components include an RSS feed aggregator (not detailed in this document, but implied by the system), an AI for briefing (via Telegram integration, also implied), and a Flask web application that serves as a user-friendly interface for browsing collected articles.

!!! tip Accessing the Dashboard
> The Flask web app is served on **port `8009`** and is typically exposed via the domain `news.mybrain.world`.

## Architecture & Data Storage

The application leverages a lightweight SQLite database (`news.db`) to persist fetched articles. The path to this database is configurable via the `NEWS_DB` environment variable.

!!! note Database Location
> By default, if `NEWS_DB` is not set, the application will look for `news.db` in the `/data/` directory, reflecting its containerized deployment context.
>
> ```bash
> # Example environment variable setting in a docker-compose.yml or .env file
> NEWS_DB=/app/data/news.db
> ```

## Web Application (`morning-brief/app.py`)

The core of the Morning Brief's user interface is a Flask application (`app.py`) that presents articles in a dark-themed news reader.

### Key Features

-   **Article Display**: Shows article titles, links, summaries, sources, and fetch times.
-   **Source Filtering**: Allows users to filter articles by specific news sources.
-   **Time-based Filtering**: Filters articles by how recently they were fetched (default 24 hours, up to 168 hours).
-   **API Endpoint**: Provides a JSON API for articles, enabling programmatic access.
-   **HTML Cleaning**: Automatically cleans HTML tags from article summaries for clean display.

### Core Functions

-   `_db()`: Establishes a connection to the SQLite database, returning `sqlite3.Row` objects for easy dictionary-like access to columns.
-   `_clean_html(text: str, maxlen: int = 220) -> str`: A utility function to strip HTML tags from text and truncate it to a specified `maxlen`, appending an ellipsis.
-   `_source_slug(name: str) -> str`: Generates a URL-friendly slug from a source name.

### Routes

#### `GET /` - Main News Dashboard

This is the primary user interface. It renders `index.html` with articles and filtering options.

-   **Parameters**:
    -   `source`: (Optional) Filter by a specific news source. E.g., `?source=BBC`. Default is `all`.
    -   `hours`: (Optional) Filter by articles fetched within the last `N` hours. E.g., `?hours=48`. Default is `24`. Max `168`.

-   **Example URL**: `http://localhost:8009/?source=The-Verge&hours=12`

#### `GET /api/articles` - JSON API Endpoint

Provides a JSON representation of articles, suitable for consumption by other applications or scripts.

-   **Parameters**:
    -   `source`: (Optional) Filter by a specific news source. Default is `all`.
    -   `hours`: (Optional) Filter by articles fetched within the last `N` hours. Default is `24`. Max `168`.

-   **Example API Call**:
    ```bash
    curl "http://localhost:8009/api/articles?source=Reuters&hours=6" | json_pp
    ```

## Local Development & Deployment

The `app.py` script includes a standard Flask development server setup:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8009, debug=False)
```

!!! warning Production vs. Development
> While `app.run()` is convenient for development, it is not recommended for production environments. For production, deploy using a WSGI server like Gunicorn or uWSGI behind a reverse proxy (e.g., Nginx). The `morning-brief/Dockerfile` and `morning-brief/docker-compose.yml` likely detail its production deployment setup.

## Related

-   Morning Brief Overview
-   Morning Brief in Obsidian
-   Nginx Proxy Configuration
-   AI Brain Logic
-   Bot Architecture
---