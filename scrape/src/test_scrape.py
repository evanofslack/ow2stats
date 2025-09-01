import pytest
from typing import List

from .scrape import OverwatchScraper
from .models import HeroStatsUpload


@pytest.fixture
def scraper() -> OverwatchScraper:
    """Provides a configured instance of the scraper for testing."""
    return OverwatchScraper()


def test_scrape_single_page(scraper: OverwatchScraper, mocker):
    """Tests scraping a single page of hero stats without uploading."""

    # Define a single set of parameters for the test
    platform = "PC"
    region = "Americas"
    gamemode = "Competitive"
    map_name = "All"
    tier = "All"

    # Run the scrape for a single page
    stats: List[HeroStatsUpload] = scraper._scrape_stats_page(
        platform, region, gamemode, map_name, tier
    )

    assert isinstance(stats, list)
    # The API should return at least one hero for this common configuration
    assert len(stats) > 0

    # Check the first hero stat object returned
    first_stat = stats[0]
    assert isinstance(first_stat, HeroStatsUpload)
    assert first_stat.hero is not None and len(first_stat.hero) > 0
    assert isinstance(first_stat.pick_rate, float) and first_stat.pick_rate > 0
    assert isinstance(first_stat.win_rate, float) and first_stat.win_rate > 0
    assert first_stat.platform == platform
    assert first_stat.region == region
    assert first_stat.gamemode == gamemode
    assert first_stat.map == map_name
