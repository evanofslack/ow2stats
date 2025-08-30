# OW2Stats Development Guide

## Project Overview

This project contains two main components:

-   **`scrape/`**: A Python-based scraper that extracts hero statistics from the official Overwatch website.
-   **`backend/`**: A Rust-based API server that stores and serves the scraped data.

## Data Flow

1.  **Scraping**: The Python scraper (`scrape.py`) navigates the Overwatch stats page, parses the data, and structures it into `HeroStats` objects.
2.  **API Upload**: The scraper's `BackendClient` sends the list of `HeroStats` as a JSON payload to the Rust backend API.
3.  **Data Storage**: The Rust backend receives the data, validates it, and stores it in a PostgreSQL database.
4.  **API Serving**: The backend provides a REST API to query the hero statistics.

## Project Structure

```
/ow2stats
├── backend/
│   ├── src/
│   └── Cargo.toml
└── scrape/
    ├── scrape.py
    ├── client.py
    ├── models.py
    ├── config.py
    ├── test_scraper.py
    └── pyproject.toml
```

## Scraper Configuration (`scrape/config.py`)

The scraper uses a typed configuration system built with Pydantic.

-   **`config.py`**: Defines the `Settings` model with all configuration options.
-   **`config.json`**: Provides default values, which can be overridden by environment variables (prefixed with `OW_`).

### Key Settings:
-   `backend_url`: The URL of the Rust backend API.
-   `timeout`: The timeout for web requests.
-   `headless`: Whether to run the browser in headless mode.

## Development Workflow

After making changes to the scraper or its dependencies, always run the linter and tests to ensure code quality and correctness.

### 1. Linting

Run the `ruff` linter to automatically fix common issues and ensure code style consistency.

```bash
# From the scrape/ directory
ruff check . --fix
```

### 2. Testing

Run the `pytest` test suite to verify that the scraper is functioning correctly. This is crucial to run after any significant changes.

```bash
# From the scrape/ directory
pytest
```

### 3. Syncing Dependencies

If you modify `pyproject.toml`, sync the virtual environment to install or update dependencies.

```bash
# From the scrape/ directory
uv sync
```

## Key Scraper Components

-   **`scrape.py`**: The main scraper logic, orchestrating the process.
-   **`client.py`**: The `BackendClient`, responsible for communicating with the Rust API.
-   **`models.py`**: Contains the `HeroStats` dataclass for type-safe data handling.
-   **`config.py`**: Typed configuration management.
-   **`test_scraper.py`**: Pytest tests for the scraper.

