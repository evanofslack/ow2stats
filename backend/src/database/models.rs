use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct HeroStats {
    pub id: i32,
    pub hero_id: String,
    pub pick_rate: Option<f32>,
    pub win_rate: Option<f32>,
    pub region: String,
    pub platform: String,
    pub gamemode: String,
    pub map: String,
    pub tier: String,
    pub inserted_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateHeroStats {
    pub hero_id: String,
    pub pick_rate: Option<f32>,
    pub win_rate: Option<f32>,
    pub region: String,
    pub platform: String,
    pub gamemode: String,
    pub map: String,
    pub tier: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateHeroStats {
    pub hero_id: Option<String>,
    pub pick_rate: Option<f32>,
    pub win_rate: Option<f32>,
    pub region: Option<String>,
    pub platform: Option<String>,
    pub gamemode: Option<String>,
    pub map: Option<String>,
    pub tier: Option<String>,
    pub timestamp: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HeroStatsQuery {
    pub hero_id: Option<String>,
    pub region: Option<String>,
    pub platform: Option<String>,
    pub gamemode: Option<String>,
    pub map: Option<String>,
    pub tier: Option<String>,
    pub limit: Option<i32>,
    pub offset: Option<i32>,
}

impl Default for HeroStatsQuery {
    fn default() -> Self {
        Self {
            hero_id: None,
            region: None,
            platform: None,
            gamemode: None,
            map: None,
            tier: None,
            limit: Some(100),
            offset: Some(0),
        }
    }
}
