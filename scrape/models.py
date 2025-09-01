from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class HeroCells:
    name: str
    pickrate: float
    winrate: float


@dataclass
class Hero:
    color: str
    name: str
    portrait: str
    role: str
    roleIcon: str


@dataclass
class HeroRate:
    id: str
    cells: HeroCells
    hero: Hero


@dataclass
class RoleExtrema:
    maxwr: float
    minwr: float
    maxpr: float
    minpr: float


@dataclass
class Extrema:
    all: RoleExtrema
    tank: RoleExtrema
    damage: RoleExtrema
    support: RoleExtrema


@dataclass
class Selected:
    input: str
    map: str
    region: str
    role: str
    rq: str
    tier: str


@dataclass
class OverwatchStats:
    rates: List[HeroRate]
    extrema: Extrema
    selected: Selected

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OverwatchStats":
        rates = [
            HeroRate(
                id=rate["id"],
                cells=HeroCells(**rate["cells"]),
                hero=Hero(**rate["hero"]),
            )
            for rate in data["rates"]
        ]

        extrema = Extrema(
            all=RoleExtrema(**data["extrema"]["all"]),
            tank=RoleExtrema(**data["extrema"]["tank"]),
            damage=RoleExtrema(**data["extrema"]["damage"]),
            support=RoleExtrema(**data["extrema"]["support"]),
        )

        selected = Selected(**data["selected"])

        return cls(rates=rates, extrema=extrema, selected=selected)

    @classmethod
    def from_json(cls, json_str: str) -> "OverwatchStats":
        return cls.from_dict(json.loads(json_str))


@dataclass
class HeroStatsUpload:
    """Data model to send to backend"""

    hero_id: str
    hero: str
    pick_rate: Optional[float]
    win_rate: Optional[float]
    region: str
    platform: str
    gamemode: str
    map: str
    tier: str
    timestamp: str
