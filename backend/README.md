# OW2Stats Backend API

A Rust-based REST API server for managing Overwatch 2 hero statistics data.

## Backend Service

This service provides a REST API for the Overwatch hero statistics data.

- **Functionality**: It accepts hero statistics data, stores it in a PostgreSQL database, and serves it via a JSON API.
- **Endpoints**: Provides CRUD operations for hero stats and a batch upload endpoint for the scraper. A `/health` endpoint is available for monitoring.
- **Build & Deploy**: The service can be built and run locally using `cargo run`. For deployment, a `Dockerfile` and `docker-compose.yml` are provided to run the service and the database in containers.

## Features

- **Fast & Async**: Built with Axum and Tokio for high-performance async operations
- **PostgreSQL**: Robust database with proper indexing and constraints
- **Structured Logging**: Comprehensive tracing with structured logs
- **CRUD Operations**: Full Create, Read, Update, Delete support for hero statistics
- **Batch Upload**: Efficient bulk data upload for scraper integration
- **Error Handling**: Comprehensive error handling with meaningful responses

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Hero Statistics
- `GET /api/heroes` - List hero statistics with filtering
- `GET /api/heroes/{id}` - Get specific hero statistic
- `POST /api/heroes` - Create new hero statistic
- `PUT /api/heroes/{id}` - Update hero statistic
- `DELETE /api/heroes/{id}` - Delete hero statistic
- `POST /api/heroes/batch` - Batch upload hero statistics

### Query Parameters for `/api/heroes`
- `hero` - Filter by hero name
- `region` - Filter by region (Americas, Europe, Asia)
- `platform` - Filter by platform (PC, Console)
- `role` - Filter by role (Tank, Damage, Support)
- `gamemode` - Filter by game mode (Quick Play, Competitive)
- `map` - Filter by map name
- `limit` - Number of results (default: 100)
- `offset` - Pagination offset (default: 0)

## Quick Start

### Prerequisites
- Rust 1.75+
- PostgreSQL 15+
- Docker (optional)

### Development Setup

1. **Start PostgreSQL**:
   ```bash
   docker-compose up postgres -d
   ```

2. **Set environment variables**:
   ```bash
   export OW2STATS_DATABASE_URL="postgresql://ow2stats:ow2stats_password@localhost:5432/ow2stats"
   export OW2STATS_PORT=3000
   export OW2STATS_LOG_LEVEL=info
   ```

3. **Install sqlx-cli**:
   ```bash
   cargo install sqlx-cli
   ```

4. **Run migrations**:
   ```bash
   sqlx migrate run
   ```

5. **Start the server**:
   ```bash
   cargo run
   ```

### Docker Setup

Run the entire stack with Docker:
```bash
docker-compose up -d
```

## Configuration

Configuration can be provided via:
- `config.toml` file
- Environment variables prefixed with `OW2STATS_`

### Available Settings
- `database_url` - PostgreSQL connection string
- `port` - Server port (default: 3000)
- `log_level` - Logging level (default: info)

## Database Schema

```sql
CREATE TABLE hero_stats (
    id SERIAL PRIMARY KEY,
    hero VARCHAR NOT NULL,
    pick_rate REAL,
    win_rate REAL,
    region VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    gamemode VARCHAR NOT NULL,
    map VARCHAR NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hero, region, platform, role, gamemode, map, timestamp)
);
```

## Integration with Scraper

The Python scraper can upload data via the batch endpoint:

```bash
curl -X POST http://localhost:3000/api/heroes/batch \
  -H "Content-Type: application/json" \
  -d '[
    {
      "hero": "Tracer",
      "pick_rate": 15.2,
      "win_rate": 49.8,
      "region": "Americas",
      "platform": "PC",
      "role": "Damage",
      "gamemode": "Quick Play",
      "map": "All",
      "timestamp": "2024-08-29T17:00:00Z"
    }
  ]'
```

## Development

### Running Tests
```bash
cargo test
```

### Database Operations
```bash
# Create new migration
sqlx migrate add migration_name

# Run migrations
sqlx migrate run

# Revert last migration
sqlx migrate revert
```

### Logging
Set `RUST_LOG` environment variable for detailed logging:
```bash
RUST_LOG=debug cargo run
```