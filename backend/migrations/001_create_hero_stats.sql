CREATE TABLE hero_stats (
    id SERIAL PRIMARY KEY,
    hero VARCHAR NOT NULL,
    pick_rate REAL,
    win_rate REAL,
    region VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    gamemode VARCHAR NOT NULL,
    map VARCHAR NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hero, region, platform, role, gamemode, map, timestamp)
);

CREATE INDEX idx_hero_stats_hero ON hero_stats(hero);
CREATE INDEX idx_hero_stats_region ON hero_stats(region);
CREATE INDEX idx_hero_stats_platform ON hero_stats(platform);
CREATE INDEX idx_hero_stats_role ON hero_stats(role);
CREATE INDEX idx_hero_stats_gamemode ON hero_stats(gamemode);
CREATE INDEX idx_hero_stats_timestamp ON hero_stats(timestamp DESC);
CREATE INDEX idx_hero_stats_lookup ON hero_stats(hero, region, platform, gamemode, map, timestamp);
