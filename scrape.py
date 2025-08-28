#!/usr/bin/env python3
"""
Overwatch Statistics Scraper
Production-ready scraper for hero statistics with logging and error handling.
"""

import logging
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import random
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


@dataclass
class HeroStats:
    """Data class for hero statistics."""

    hero: str
    pick_rate: Optional[float]
    win_rate: Optional[float]
    region: str
    platform: str
    role: str
    timestamp: str


class OverwatchScraper:
    """Production-ready Overwatch statistics scraper."""

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.db_path = Path(self.config.get("db_path", "overwatch_stats.db"))
        self._setup_database()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        default_config = {
            "base_url": "https://overwatch.blizzard.com/en-us/rates/",
            "timeout": 15,
            "retry_attempts": 3,
            "retry_delay": 5,
            "rate_limit_delay": (2, 5),
            "headless": True,
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ],
            "regions": ["Americas", "Europe", "Asia"],
            "platforms": ["PC", "Console"],
            "roles": ["All", "Tank", "Damage", "Support"],
        }

        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")

        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging."""
        logger = logging.getLogger("overwatch_scraper")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # File handler
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "scraper.log")
            file_handler.setLevel(logging.DEBUG)

            # Formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

        return logger

    def _setup_database(self) -> None:
        """Initialize SQLite database with proper schema."""
        self.logger.info(f"Setting up database at {self.db_path}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hero_stats (
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
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hero_stats_lookup 
                ON hero_stats(hero, region, platform, timestamp)
            """)

            conn.commit()

    def _create_driver(self) -> webdriver.Chrome:
        """Create Chrome WebDriver with production settings."""
        options = Options()

        if self.config.get("headless", True):
            options.add_argument("--headless")

        # Security and performance options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Enable performance logging to capture network requests
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Set logging preferences for network monitoring
        if self.config.get("debug_mode", False):
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # Random user agent
        user_agent = random.choice(self.config["user_agents"])
        options.add_argument(f"--user-agent={user_agent}")

        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Set longer page load timeout
            driver.set_page_load_timeout(self.config.get("page_load_timeout", 30))

            return driver
        except Exception as e:
            self.logger.error(f"Failed to create WebDriver: {e}")
            raise

    def _monitor_network_requests(self, driver: webdriver.Chrome) -> None:
        """Monitor network requests to find API endpoints."""
        if not self.config.get("debug_mode", False):
            return

        try:
            logs = driver.get_log("performance")
            api_endpoints = []

            for log in logs:
                message = json.loads(log["message"])
                if message["message"]["method"] == "Network.responseReceived":
                    url = message["message"]["params"]["response"]["url"]
                    if any(
                        keyword in url.lower()
                        for keyword in ["api", "stats", "heroes", "data", "json"]
                    ):
                        api_endpoints.append(url)

            if api_endpoints:
                self.logger.info(f"Found potential API endpoints: {api_endpoints}")

        except Exception as e:
            self.logger.debug(f"Could not monitor network requests: {e}")

    def _build_url(self, platform: str, region: str, role: str) -> str:
        """Build URL with parameters."""
        params = {
            "input": platform,
            "map": "all-maps",
            "region": region,
            "role": role,
            "rq": "0",
            "tier": "All",
        }

        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config['base_url']}?{param_string}"

    def _parse_percentage(self, value: str) -> Optional[float]:
        """Parse percentage string to float."""
        if not value or value == "--" or value.strip() == "":
            return None

        try:
            # Remove % sign and convert
            clean_value = value.replace("%", "").strip()
            return float(clean_value)
        except (ValueError, AttributeError):
            self.logger.warning(f"Could not parse percentage: {value}")
            return None

    def _wait_for_page_load(self, driver: webdriver.Chrome) -> bool:
        """Wait for the page to fully load with multiple fallback strategies."""
        wait = WebDriverWait(driver, self.config["timeout"])

        # Strategy 1: Wait for hero statistics content to appear
        try:
            # Look for the page to contain hero names and percentages
            def content_loaded(driver):
                body_text = driver.find_element(By.TAG_NAME, "body").text
                # Check for both hero names and percentage symbols
                has_heroes = any(
                    hero in body_text
                    for hero in ["Genji", "Tracer", "Mercy", "Reinhardt", "Hanzo"]
                )
                has_percentages = "%" in body_text
                has_stats_header = "HERO STATISTICS" in body_text
                return has_heroes and has_percentages and has_stats_header

            wait.until(content_loaded)
            self.logger.debug("Page loaded - found heroes and percentages")
            return True
        except TimeoutException:
            pass

        # Strategy 2: Wait for specific UI elements
        ui_selectors = [
            "[role='main']",
            ".hero-stats",
            "[data-testid]",
            "[class*='hero']",
            "[class*='stat']",
            "main",
        ]

        for selector in ui_selectors:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                self.logger.debug(f"Found UI element: {selector}")
                time.sleep(2)  # Additional wait for content to populate
                return True
            except TimeoutException:
                continue

        # Strategy 3: Wait for page to stop loading and settle
        try:
            wait.until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(5)  # Wait for JS to render content
            return True
        except TimeoutException:
            pass

        return False

    def _find_data_rows(self, driver: webdriver.Chrome) -> List:
        """Find hero data using text parsing since no tables exist."""
        # Since there are no tables, we need to parse the page text directly
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            return self._parse_hero_data_from_text(body_text)
        except Exception as e:
            self.logger.debug(f"Error getting body text: {e}")
            return []

    def _parse_hero_data_from_text(self, page_text: str) -> List[Dict]:
        """Parse hero statistics from page text since it's not in table format."""
        hero_data = []

        # Common hero names to look for
        hero_names = [
            "Ana",
            "Ashe",
            "Baptiste",
            "Bastion",
            "Brigitte",
            "Cassidy",
            "D.Va",
            "Doomfist",
            "Echo",
            "Genji",
            "Hanzo",
            "Junkrat",
            "Kiriko",
            "Lifeweaver",
            "Lucio",
            "Mauga",
            "McCree",
            "Mei",
            "Mercy",
            "Moira",
            "Orisa",
            "Pharah",
            "Ramattra",
            "Reaper",
            "Reinhardt",
            "Roadhog",
            "Sigma",
            "Soldier: 76",
            "Sombra",
            "Symmetra",
            "Torbjorn",
            "Tracer",
            "Widowmaker",
            "Winston",
            "Wrecking Ball",
            "Zarya",
            "Zenyatta",
        ]

        lines = page_text.split("\n")

        # Look for patterns like "HeroName XX.X% YY.Y%"
        import re

        for i, line in enumerate(lines):
            line = line.strip()

            # Check if this line contains a hero name
            for hero in hero_names:
                if hero.upper() in line.upper():
                    # Look in this line and surrounding lines for percentages
                    search_lines = lines[max(0, i - 2) : i + 3]  # Check nearby lines
                    search_text = " ".join(search_lines)

                    # Find percentages in the search area
                    percentages = re.findall(r"(\d+\.?\d*)%", search_text)

                    if len(percentages) >= 2:
                        try:
                            pick_rate = float(percentages[0])
                            win_rate = float(percentages[1])

                            hero_data.append(
                                {
                                    "hero": hero,
                                    "pick_rate": f"{pick_rate}%",
                                    "win_rate": f"{win_rate}%",
                                }
                            )

                            self.logger.debug(
                                f"Found {hero}: {pick_rate}% pick, {win_rate}% win"
                            )
                            break  # Found this hero, move to next line
                        except (ValueError, IndexError):
                            continue

        return hero_data

    def _extract_hero_data(self, hero_dict: Dict) -> Optional[Dict]:
        """Extract hero data from dictionary format."""
        return hero_dict  # Already in the right format

    def _scrape_stats_page(
        self, platform: str, region: str, role: str
    ) -> List[HeroStats]:
        """Scrape statistics for a specific configuration."""
        url = self._build_url(platform, region, role)
        self.logger.info(f"Scraping {platform}/{region}/{role}: {url}")

        driver = None
        try:
            driver = self._create_driver()
            self.logger.debug("Loading page...")
            driver.get(url)

            # Wait for page to load
            if not self._wait_for_page_load(driver):
                self.logger.error(f"Page failed to load properly: {url}")

                # Debug: Save page source
                debug_dir = Path("debug")
                debug_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(
                    debug_dir
                    / f"page_source_{platform}_{region}_{role}_{timestamp}.html",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(driver.page_source)
                self.logger.info(f"Saved page source to debug/ folder")

                return []

            # Find data rows
            hero_data_list = self._find_data_rows(driver)

            if not hero_data_list:
                self.logger.warning(f"No data found for {platform}/{region}/{role}")

                # Debug: Log page structure
                self.logger.debug("Page title: " + driver.title)
                self.logger.debug("Page URL: " + driver.current_url)

                # Try to find any text that might indicate the page loaded
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if "Hero Statistics" in body_text:
                    self.logger.debug("Page contains 'Hero Statistics' text")
                if "pick rate" in body_text.lower():
                    self.logger.debug("Page contains pick rate references")

                return []

            stats = []
            timestamp = datetime.now().isoformat()

            for hero_data in hero_data_list:
                if not hero_data or not hero_data.get("hero"):
                    continue

                try:
                    stats.append(
                        HeroStats(
                            hero=hero_data["hero"],
                            pick_rate=self._parse_percentage(
                                hero_data.get("pick_rate", "")
                            ),
                            win_rate=self._parse_percentage(
                                hero_data.get("win_rate", "")
                            ),
                            region=region,
                            platform=platform,
                            role=role,
                            timestamp=timestamp,
                        )
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Error creating HeroStats for {hero_data}: {e}"
                    )
                    continue

            self.logger.info(
                f"Extracted {len(stats)} hero stats for {platform}/{region}/{role}"
            )
            return stats

        except TimeoutException:
            self.logger.error(f"Timeout waiting for page to load: {url}")
            return []
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return []
        finally:
            if driver:
                driver.quit()

    def _save_stats(self, stats_list: List[HeroStats]) -> None:
        """Save statistics to database."""
        if not stats_list:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for stats in stats_list:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO hero_stats 
                        (hero, pick_rate, win_rate, region, platform, role, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            stats.hero,
                            stats.pick_rate,
                            stats.win_rate,
                            stats.region,
                            stats.platform,
                            stats.role,
                            stats.timestamp,
                        ),
                    )
                except Exception as e:
                    self.logger.error(f"Error saving stats for {stats.hero}: {e}")

            conn.commit()
            self.logger.info(f"Saved {len(stats_list)} hero statistics to database")

    def scrape_all_configurations(self) -> None:
        """Scrape all platform/region/role combinations."""
        total_combinations = (
            len(self.config["platforms"])
            * len(self.config["regions"])
            * len(self.config["roles"])
        )
        self.logger.info(f"Starting scrape for {total_combinations} configurations")

        completed = 0
        failed = 0

        for platform in self.config["platforms"]:
            for region in self.config["regions"]:
                for role in self.config["roles"]:
                    for attempt in range(self.config["retry_attempts"]):
                        try:
                            stats = self._scrape_stats_page(platform, region, role)
                            self._save_stats(stats)
                            completed += 1
                            break

                        except Exception as e:
                            self.logger.warning(
                                f"Attempt {attempt + 1} failed for {platform}/{region}/{role}: {e}"
                            )
                            if attempt < self.config["retry_attempts"] - 1:
                                time.sleep(self.config["retry_delay"])
                            else:
                                failed += 1

                    # Rate limiting between requests
                    delay = random.uniform(*self.config["rate_limit_delay"])
                    time.sleep(delay)

        self.logger.info(f"Scraping completed. Success: {completed}, Failed: {failed}")

    def get_latest_stats(self, limit: int = 100) -> List[Dict]:
        """Get latest statistics from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM hero_stats 
                ORDER BY created_at DESC 
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]


def main():
    """Main execution function."""
    scraper = OverwatchScraper()

    try:
        scraper.logger.info("Starting Overwatch statistics scraping")
        scraper.scrape_all_configurations()

        # Show recent results
        recent_stats = scraper.get_latest_stats(10)
        scraper.logger.info(f"Recent stats count: {len(recent_stats)}")

    except KeyboardInterrupt:
        scraper.logger.info("Scraping interrupted by user")
    except Exception as e:
        scraper.logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
