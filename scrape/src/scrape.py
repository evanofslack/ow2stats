import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import random
import sys

import requests as rq
from tqdm import tqdm

from .models import OverwatchStats, HeroStatsUpload, HeroRate
from .client import BackendClient
from .config import config


class OverwatchScraper:
    def __init__(self):
        self.config = config
        self.logger = self._setup_logging()
        self.client = BackendClient(self.config.backend_url)
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)

    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging."""
        logger = logging.getLogger("overwatch_scraper")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "scraper.log")
            file_handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)

            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

        return logger

    def _build_url(
        self,
        platform: str,
        region: str,
        role: str,
        gamemode: str,
        map_name: str,
        tier: str,
    ) -> str:
        """Build API URL with parameters."""
        rq_value = "1" if gamemode.lower() == "competitive" else "0"
        map_param = (
            map_name.lower().replace(" ", "-") if map_name != "All" else "all-maps"
        )

        params = {
            "input": platform,
            "map": map_param,
            "region": region,
            "role": role,
            "rq": rq_value,
            "tier": tier,
        }

        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.base_url}?{param_string}"

    def _fetch_data(self, url: str) -> Optional[OverwatchStats]:
        try:
            self.logger.debug(f"Fetching from API: {url}")
            resp = rq.get(url, timeout=self.config.timeout)
            resp.raise_for_status()

            data = resp.json()
            self.logger.debug(f"API response, json={data}, status={resp.status_code}")

            if not isinstance(data, dict) or "selected" not in data:
                self.logger.error(f"Invalid API response structure: {url}")
                return None

            return OverwatchStats.from_dict(data)

        except rq.RequestException as e:
            self.logger.error(f"API request failed for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response from {url}: {e}")
            return None
        except (KeyError, TypeError) as e:
            self.logger.error(f"Failed to parse API response structure from {url}: {e}")
            return None

    def _transform_to_hero_stats(
        self,
        hero_rate: HeroRate,
        platform: str,
        region: str,
        gamemode: str,
        map_name: str,
        tier: str,
    ) -> HeroStatsUpload:
        """Transform Blizzard API data to HeroStats format."""
        return HeroStatsUpload(
            hero_id=hero_rate.id,
            pick_rate=hero_rate.cells.pickrate,
            win_rate=hero_rate.cells.winrate,
            region=region,
            platform=platform,
            gamemode=gamemode,
            map=map_name,
            tier=tier,
        )

    def _scrape_stats_page(
        self,
        platform: str,
        region: str,
        gamemode: str,
        map_name: str,
        tier: str,
    ) -> List[HeroStatsUpload]:
        """Scrape statistics for a specific configuration."""
        role = "all"
        url = self._build_url(platform, region, role, gamemode, map_name, tier)
        self.logger.info(
            f"Scraping stats, platform={platform}, region={region}, gamemode={gamemode}, map={map_name}, tier={tier}, role={role}, url={url}"
        )

        api_response = self._fetch_data(url)
        if not api_response:
            return []

        if not api_response.rates:
            self.logger.warning(f"No hero rate data returned for {url}")
            return []

        stats = []

        for rate in api_response.rates:
            hero_stats = self._transform_to_hero_stats(
                rate,
                platform,
                region,
                gamemode,
                map_name,
                tier,
            )
            stats.append(hero_stats)

        self.logger.info(f"Extracted {len(stats)} hero stats")
        return stats

    def _save_stats(self, stats_list: List[HeroStatsUpload]) -> None:
        """Save statistics to backend."""
        if not stats_list:
            return

        try:
            self.client.upload_stats(stats_list)
            self.logger.debug(f"Uploaded {len(stats_list)} stats to backend")
        except Exception as e:
            self.logger.error(f"Failed to upload stats: {e}")
            raise

    def scrape_all_configurations(self) -> None:
        """Scrape all platform/region/gamemode/map combinations."""
        configurations = []

        # Build all combinations
        for platform in self.config.platforms:
            for region in self.config.regions:
                for gamemode in self.config.gamemodes:
                    tiers_to_scrape = (
                        self.config.tiers if gamemode == "Competitive" else ["All"]
                    )
                    for tier in tiers_to_scrape:
                        for map_name in self.config.maps:
                            configurations.append(
                                {
                                    "platform": platform,
                                    "region": region,
                                    "gamemode": gamemode,
                                    "map_name": map_name,
                                    "tier": tier,
                                }
                            )

        self.logger.info(f"Starting scrape for {len(configurations)} configurations")

        completed = 0
        failed = 0

        for config_dict in tqdm(configurations, desc="Scraping configurations"):
            for attempt in range(self.config.retry_attempts):
                try:
                    stats = self._scrape_stats_page(**config_dict)
                    self._save_stats(stats)
                    completed += 1
                    break

                except Exception as e:
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed for {config_dict}: {e}"
                    )
                    if attempt < self.config.retry_attempts - 1:
                        time.sleep(self.config.retry_delay)
                    else:
                        failed += 1

            if hasattr(self.config, "rate_limit_delay"):
                delay = random.uniform(*self.config.rate_limit_delay)
                time.sleep(delay)

        self.logger.info(f"Scraping completed. Success: {completed}, Failed: {failed}")
