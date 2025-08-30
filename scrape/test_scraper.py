import pytest
from typing import List
from scrape.scrape import OverwatchScraper
from scrape.models import HeroStats
from scrape.client import BackendClient

@pytest.fixture
def scraper() -> OverwatchScraper:
    """Provides a configured instance of the scraper for testing."""
    # The scraper will load its config from config.json and env vars
    # For tests, we can override config by setting env vars if needed
    return OverwatchScraper()

def test_scrape_single_page(scraper: OverwatchScraper, mocker):
    """Tests scraping a single page of hero stats without uploading."""
    # We only want to test the scraping logic, so we mock the upload function
    mocker.patch.object(scraper.client, 'upload_stats', return_value=None)

    # Define a single set of parameters for the test
    platform = "PC"
    region = "Americas"
    role = "Tank"
    gamemode = "Competitive"
    map_name = "All"

    # Run the scrape for a single page
    stats: List[HeroStats] = scraper._scrape_stats_page(
        platform, region, role, gamemode, map_name
    )

    # Assertions
    assert isinstance(stats, list)
    # The API should return at least one hero for this common configuration
    assert len(stats) > 0
    
    # Check the first hero stat object returned
    first_stat = stats[0]
    assert isinstance(first_stat, HeroStats)
    assert first_stat.hero is not None and len(first_stat.hero) > 0
    assert isinstance(first_stat.pick_rate, float) and first_stat.pick_rate > 0
    assert isinstance(first_stat.win_rate, float) and first_stat.win_rate > 0
    assert first_stat.platform == platform
    assert first_stat.region == region
    assert first_stat.role == role
    assert first_stat.gamemode == gamemode
    assert first_stat.map == map_name
    assert first_stat.timestamp is not None

    # Ensure the mocked upload_stats was not called, as it's outside the tested method
    scraper.client.upload_stats.assert_not_called()
