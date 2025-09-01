CREATE TABLE hero_stats (
    id SERIAL PRIMARY KEY,
    hero_id VARCHAR NOT NULL,
    pick_rate REAL,
    win_rate REAL,
    region VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    gamemode VARCHAR NOT NULL,
    map VARCHAR NOT NULL,
    tier TEXT NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (hero_id, region, platform, gamemode, map, tier, inserted_at)
);

-- Create indexes for common queries
CREATE INDEX idx_hero_stats_hero_id ON hero_stats (hero_id);
CREATE INDEX idx_hero_stats_region ON hero_stats (region);
CREATE INDEX idx_hero_stats_platform ON hero_stats (platform);
CREATE INDEX idx_hero_stats_gamemode ON hero_stats (gamemode);
CREATE INDEX idx_hero_stats_tier ON hero_stats (tier);
CREATE INDEX idx_hero_stats_inserted_at ON hero_stats (inserted_at DESC);
CREATE INDEX idx_hero_stats_lookup ON hero_stats (hero_id, region, platform, gamemode, map, tier, inserted_at);
