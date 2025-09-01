from typing import List, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for the scraper."""

    model_config = SettingsConfigDict(
        json_file="config.json",
        json_file_encoding="utf-8",
        case_sensitive=False,
        # Environment variables will be prefixed with `OW_`
        # e.g., `OW_BACKEND_URL=http://api.example.com`
        env_prefix="OW_",
    )

    base_url: str = "https://overwatch.blizzard.com/en-us/rates/data/"
    backend_url: str = "http://localhost:3000"
    timeout: int = 10
    retry_attempts: int = 3
    retry_delay: int = 2
    rate_limit_delay: Tuple[int, int] = (2, 5)
    headless: bool = True
    log_level: str = "INFO"
    debug_mode: bool = False
    save_html: bool = False
    user_agents: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]
    regions: List[str] = ["Americas", "Europe", "Asia"]
    platforms: List[str] = ["PC", "Console"]
    gamemodes: List[str] = ["Quick Play", "Competitive"]
    maps: List[str] = [
        "All",
        "Antarctic Peninsula",
        "Busan",
        "Ilios",
        "Lijiang Tower",
        "Nepal",
        "Oasis",
        "Samoa",
        "Circuit Royal",
        "Dorado",
        "Havana",
        "Junkertown",
        "Rialto",
        "Route 66",
        "Shambali Monastery",
        "Watchpoint: Gibraltar",
        "Aatlis",
        "New Junk City",
        "Suravasa",
        "Blizzard World",
        "Eichenwalde",
        "Hollywood",
        "King's Row",
        "Midtown",
        "Numbani",
        "Paraíso",
        "Colosseo",
        "Esperança",
        "New Queen Street",
        "Runasapi",
        "Hanaoka",
        "Temple of Anubis",
    ]
    tiers: List[str] = [
        "All",
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Diamond",
        "Master",
        "Grandmaster",
        "Champion",
    ]


def load_config() -> Settings:
    """Loads configuration from config.json and environment variables."""
    return Settings()


# Global config instance
config = load_config()
