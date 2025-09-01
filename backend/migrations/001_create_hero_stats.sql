CREATE TYPE hero_class_enum AS ENUM ('support', 'damage', 'tank');

CREATE TYPE map_type_enum AS ENUM ('control', 'escort', 'flashpoint', 'hybrid', 'push', 'clash');

CREATE TABLE hero_stats (
    id SERIAL PRIMARY KEY,
    hero_id VARCHAR NOT NULL,
    hero_class hero_class_enum NOT NULL,
    pick_rate REAL,
    win_rate REAL,
    region VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    gamemode VARCHAR NOT NULL,
    map VARCHAR NOT NULL,
    map_type map_type_enum NOT NULL,
    tier TEXT NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (hero_id, region, platform, gamemode, map, tier, inserted_at)
);

CREATE INDEX idx_hero_stats_hero_id ON hero_stats (hero_id);
CREATE INDEX idx_hero_stats_hero_class ON hero_stats (hero_class);
CREATE INDEX idx_hero_stats_region ON hero_stats (region);
CREATE INDEX idx_hero_stats_platform ON hero_stats (platform);
CREATE INDEX idx_hero_stats_gamemode ON hero_stats (gamemode);
CREATE INDEX idx_hero_stats_map ON hero_stats (map);
CREATE INDEX idx_hero_stats_map_typ ON hero_stats (map_type);
CREATE INDEX idx_hero_stats_tier ON hero_stats (tier);
CREATE INDEX idx_hero_stats_inserted_at ON hero_stats (inserted_at DESC);
CREATE INDEX idx_hero_stats_lookup ON hero_stats (hero_id, hero_class, region, platform, gamemode, map, map_type, tier, inserted_at);
