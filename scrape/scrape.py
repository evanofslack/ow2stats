import logging
from .config import config
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .models import HeroStats
import random
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .client import BackendClient




class OverwatchScraper:
    """Production-ready Overwatch statistics scraper."""

    def __init__(self):
        self.config = config
        self.logger = self._setup_logging()
        self.client = BackendClient(self.config.backend_url)

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

    def _create_driver(self) -> webdriver.Chrome:
        """Create Chrome WebDriver with production settings."""
        options = Options()

        if self.config.headless:
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
        if self.config.debug_mode:
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # Random user agent
        user_agent = random.choice(self.config.user_agents)
        options.add_argument(f"--user-agent={user_agent}")

        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Set longer page load timeout
            driver.set_page_load_timeout(self.config.timeout)

            return driver
        except Exception as e:
            self.logger.error(f"Failed to create WebDriver: {e}")
            raise

    def _monitor_network_requests(self, driver: webdriver.Chrome) -> None:
        """Monitor network requests to find API endpoints."""
        if not self.config.debug_mode:
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

    def _build_url(
        self, platform: str, region: str, role: str, gamemode: str, map_name: str
    ) -> str:
        """Build URL with parameters."""
        # Map gamemode to rq parameter
        rq_value = "1" if gamemode.lower() == "competitive" else "0"

        # Format map name for URL (replace spaces with hyphens, lowercase)
        map_param = (
            map_name.lower().replace(" ", "-") if map_name != "All" else "all-maps"
        )

        params = {
            "input": platform,
            "map": map_param,
            "region": region,
            "role": role,
            "rq": rq_value,
            "tier": "All",
        }

        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.base_url}?{param_string}"

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
        wait = WebDriverWait(driver, self.config.timeout)

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

        # Updated hero names list including newer heroes
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
            "Freja",
            "Genji",
            "Hanzo",
            "Hazard",
            "Junkrat",
            "Illari",
            "Junker Queen",
            "Junkrat",
            "Juno",
            "Kiriko",
            "Lifeweaver",
            "Lucio",
            "Mauga",
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
            "Sojourn",
            "Soldier: 76",
            "Sombra",
            "Symmetra",
            "Torbjorn",
            "Tracer",
            "Venture",
            "Widowmaker",
            "Winston",
            "Wrecking Ball",
            "Wuyang",
            "Zarya",
            "Zenyatta",
        ]

        lines = page_text.split("\n")

        # Save raw page text for debugging if enabled
        if self.config.debug_mode:
            debug_dir = Path("debug")
            debug_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(
                debug_dir / f"page_text_{timestamp}.txt", "w", encoding="utf-8"
            ) as f:
                f.write(page_text)
            self.logger.debug(f"Saved raw page text to debug/page_text_{timestamp}.txt")

        # The page structure is:
        # HERO_NAME
        # PICK_RATE%
        # WIN_RATE%
        # (repeat for each hero)

        import re

        percentage_pattern = re.compile(r"^(\d+(?:\.\d+)?)%$")

        for i, line in enumerate(lines):
            line = line.strip()

            # Check if this line contains a hero name
            for hero in hero_names:
                if line.upper() == hero.upper():
                    # Found a hero name, look for percentages in the next 2 lines
                    try:
                        # Next line should be pick rate
                        if i + 1 < len(lines):
                            pick_line = lines[i + 1].strip()
                            pick_match = percentage_pattern.match(pick_line)

                        # Line after that should be win rate
                        if i + 2 < len(lines):
                            win_line = lines[i + 2].strip()
                            win_match = percentage_pattern.match(win_line)

                        if pick_match and win_match:
                            pick_rate = float(pick_match.group(1))
                            win_rate = float(win_match.group(1))

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
                            break  # Found this hero, don't check other hero names for this line

                    except (ValueError, IndexError, AttributeError):
                        continue

        self.logger.info(
            f"Found {len(hero_data)} heroes out of {len(hero_names)} possible heroes"
        )
        return hero_data

    def _extract_hero_data(self, hero_dict: Dict) -> Optional[Dict]:
        """Extract hero data from dictionary format."""
        return hero_dict  # Already in the right format

    def _scrape_stats_page(
        self, platform: str, region: str, role: str, gamemode: str, map_name: str
    ) -> List[HeroStats]:
        """Scrape statistics for a specific configuration."""
        url = self._build_url(platform, region, role, gamemode, map_name)
        self.logger.info(
            f"Scraping {platform}/{region}/{role}/{gamemode}/{map_name}: {url}"
        )

        driver = None
        try:
            driver = self._create_driver()
            self.logger.debug("Loading page...")
            driver.get(url)

            # Wait for page to load
            if not self._wait_for_page_load(driver):
                self.logger.error(f"Page failed to load properly: {url}")

                # Debug: Save page source
                if self.config.save_html:
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
                    self.logger.info("Saved page source to debug/ folder")

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
                            gamemode=gamemode,
                            map=map_name,
                            timestamp=timestamp,
                        )
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Error creating HeroStats for {hero_data}: {e}"
                    )
                    continue

            self.logger.info(
                f"Extracted {len(stats)} hero stats for {platform}/{region}/{role}/{gamemode}/{map_name}"
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
        """Save statistics to backend."""
        if not stats_list:
            return

        self.client.upload_stats(stats_list)

    def scrape_all_configurations(self) -> None:
        """Scrape all platform/region/role/gamemode/map combinations."""
        total_combinations = (
            len(self.config.platforms)
            * len(self.config.regions)
            * len(self.config.roles)
            * len(self.config.gamemodes)
            * len(self.config.maps)
        )
        self.logger.info(f"Starting scrape for {total_combinations} configurations")

        completed = 0
        failed = 0

        for platform in self.config.platforms:
            for region in self.config.regions:
                for role in self.config.roles:
                    for gamemode in self.config.gamemodes:
                        for map_name in self.config.maps:
                            for attempt in range(self.config.retry_attempts):
                                try:
                                    stats = self._scrape_stats_page(
                                        platform, region, role, gamemode, map_name
                                    )
                                    self._save_stats(stats)
                                    completed += 1
                                    break

                                except Exception as e:
                                    self.logger.warning(
                                        f"Attempt {attempt + 1} failed for {platform}/{region}/{role}/{gamemode}/{map_name}: {e}"
                                    )
                                    if attempt < self.config.retry_attempts - 1:
                                        time.sleep(self.config.retry_delay)
                                    else:
                                        failed += 1

                            # Rate limiting between requests
                            delay = random.uniform(*self.config.rate_limit_delay)
                            self.logger.debug(f"Sleeping for {delay}...")
                            time.sleep(delay)

        self.logger.info(f"Scraping completed. Success: {completed}, Failed: {failed}")


def main():
    """Main execution function."""
    scraper = OverwatchScraper()
    try:
        scraper.logger.info("Starting Overwatch statistics scraping")
        scraper.scrape_all_configurations()
    except KeyboardInterrupt:
        scraper.logger.info("Scraping interrupted by user")
    except Exception as e:
        scraper.logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
