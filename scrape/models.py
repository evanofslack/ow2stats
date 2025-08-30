from typing import Optional
from dataclasses import dataclass

@dataclass
class HeroStats:
    """Data class for hero statistics."""

    hero: str
    pick_rate: Optional[float]
    win_rate: Optional[float]
    region: str
    platform: str
    role: str
    gamemode: str
    map: str
    timestamp: str
