# Counterwatch Scraper - Claude Development Guide

## Project Overview

This is an Overwatch hero statistics scraper that extracts pick rates and win rates from the official Blizzard Overwatch statistics website. The scraper uses Selenium to navigate pages and parse text content to extract hero statistics across different platforms, regions, and roles.

## Project Structure

```
scrape/
├── scrape.py           # Main scraper implementation
├── quick.py            # Test script for debugging scraper functionality
├── config.json         # Production configuration
├── test_config.json    # Debug/test configuration
├── pyproject.toml      # Python project dependencies and metadata
├── uv.lock            # Lock file for uv package manager
├── data/              # Database storage
│   ├── stats.db       # Main statistics database (74k, ~216 records)
│   └── overwatch_stats.db  # Secondary database
└── logs/              # Application logs
    └── scraper.log    # Scraper execution logs
```

## Dependencies

**Core Dependencies:**
- `selenium>=4.35.0` - Web automation and scraping
- `webdriver-manager>=4.0.2` - Chrome WebDriver management

**Development Dependencies:**
- `pytest>=8.4.1` - Testing framework
- `ruff>=0.12.10` - Python linting and formatting

**Python Version:** >=3.13

## Configuration

### Main Config (`config.json`)
```json
{
  "base_url": "https://overwatch.blizzard.com/en-us/rates/",
  "timeout": 15,
  "retry_attempts": 3,
  "retry_delay": 5,
  "rate_limit_delay": [2, 5],
  "headless": true,
  "db_path": "data/stats.db",
  "user_agents": ["..."],
  "regions": ["Americas", "Europe", "Asia"],
  "platforms": ["PC", "Console"],
  "roles": ["All", "Tank", "Damage", "Support"],
  "log_level": "INFO"
}
```

### Debug Config (`test_config.json`)
- Sets `headless: false` for visible browser
- Enables `debug_mode: true`
- Reduced scope for testing

## How It Works

### 1. Web Scraping Flow
1. **Page Loading** - Navigates to Overwatch stats page with specific parameters
2. **Content Detection** - Waits for hero statistics content to load
3. **Text Parsing** - Extracts hero names and percentages from page text
4. **Data Storage** - Saves to SQLite database with proper schema

### 2. Data Extraction Strategy
Since the Overwatch site doesn't use standard HTML tables, the scraper:
- Parses raw page text line by line
- Matches hero names from a predefined list
- Uses regex to find percentage patterns near hero names
- Associates pick rates and win rates with heroes

### 3. Anti-Detection Measures
- Random user agent rotation
- Rate limiting between requests (2-5 second delays)
- Stealth browser options to avoid automation detection
- Retry mechanisms for failed requests

## Database Schema

```sql
CREATE TABLE hero_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero TEXT NOT NULL,
    pick_rate REAL,
    win_rate REAL,
    region TEXT NOT NULL,
    platform TEXT NOT NULL,
    role TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hero, region, platform, role, timestamp)
);
```

## Common Commands

### Running the Scraper
```bash
# Main scraper (all configurations)
python scrape.py

# Test scraper (limited scope)
python quick.py
```

### Development Tools
```bash
# Install dependencies
uv sync

# Run tests
pytest

# Lint code
ruff check .

# Format code
ruff format .
```

### Database Operations
```bash
# Check record count
sqlite3 data/stats.db "SELECT COUNT(*) FROM hero_stats;"

# View recent data
sqlite3 data/stats.db "SELECT hero, pick_rate, win_rate FROM hero_stats ORDER BY created_at DESC LIMIT 10;"

# Check configurations scraped
sqlite3 data/stats.db "SELECT DISTINCT region, platform, role FROM hero_stats;"
```

## Key Classes and Functions

### OverwatchScraper Class (`scrape.py:40`)
Main scraper class with these key methods:

- `__init__()` - Initialize with config, logging, and database
- `_create_driver()` - Set up Chrome WebDriver with stealth options
- `_wait_for_page_load()` - Wait for content to load with multiple strategies
- `_parse_hero_data_from_text()` - Extract hero stats from page text
- `scrape_all_configurations()` - Scrape all platform/region/role combinations
- `_save_stats()` - Save statistics to SQLite database

### HeroStats Dataclass (`scrape.py:28`)
Data structure for hero statistics:
```python
@dataclass
class HeroStats:
    hero: str
    pick_rate: Optional[float]
    win_rate: Optional[float]
    region: str
    platform: str
    role: str
    timestamp: str
```

## Debugging and Troubleshooting

### Debug Features
- Set `debug_mode: true` in config for network request monitoring
- Page source saved to `debug/` folder when loading fails
- Comprehensive logging to `logs/scraper.log`
- Visible browser mode (`headless: false`) for debugging

### Common Issues
1. **Page Load Failures** - Check timeout settings and network connection
2. **No Data Found** - Verify hero name list is current with game updates
3. **Database Errors** - Check file permissions and disk space

### Log Analysis
```bash
# View recent logs
tail -f logs/scraper.log

# Check for errors
grep ERROR logs/scraper.log

# Monitor scraping progress
grep "Extracted.*hero stats" logs/scraper.log
```

## Development Guidelines

### Adding New Heroes
Update the `hero_names` list in `_parse_hero_data_from_text()` (`scrape.py:300`) when new heroes are added to Overwatch.

### Modifying Scraping Logic
- Test changes with `quick.py` first
- Use debug mode to capture page sources
- Check logs for parsing issues
- Validate data in database after changes

### Performance Considerations
- Respect rate limits to avoid being blocked
- Use appropriate timeout values
- Monitor memory usage during long scraping sessions
- Consider database vacuum operations for large datasets

## Security Notes
- No credentials or sensitive data handling required
- Uses public Overwatch statistics API
- Implements respectful scraping practices
- No malicious code - purely defensive data collection tool