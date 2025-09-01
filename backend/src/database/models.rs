use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct HeroStats {
    pub id: i32,
    pub hero_id: String,
    pub hero_class: HeroClass,
    pub pick_rate: Option<f32>,
    pub win_rate: Option<f32>,
    pub region: String,
    pub platform: String,
    pub gamemode: String,
    pub map: String,
    pub map_type: MapType,
    pub tier: String,
    pub inserted_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub struct CreateHeroStats {
    pub hero_id: String,
    pub hero_class: HeroClass,
    pub pick_rate: Option<f32>,
    pub win_rate: Option<f32>,
    pub region: String,
    pub platform: String,
    pub gamemode: String,
    pub map: String,
    pub map_type: MapType,
    pub tier: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateHeroStats {
    pub hero_id: Option<String>,
    pub hero_class: HeroClass,
    pub pick_rate: Option<f32>,
    pub win_rate: Option<f32>,
    pub region: Option<String>,
    pub platform: Option<String>,
    pub gamemode: Option<String>,
    pub map: Option<String>,
    pub map_type: MapType,
    pub tier: Option<String>,
    pub timestamp: Option<DateTime<Utc>>,
}

#[derive(sqlx::Type, Clone, Serialize, Deserialize, Debug)]
#[serde(rename_all = "lowercase")]
#[sqlx(type_name = "hero_class_enum", rename_all = "lowercase")]
pub enum HeroClass {
    Support,
    Damage,
    Tank,
}

#[derive(sqlx::Type, Clone, Serialize, Deserialize, Debug)]
#[serde(rename_all = "lowercase")]
#[sqlx(type_name = "map_type_enum", rename_all = "lowercase")]
pub enum MapType {
    Control,
    Escort,
    Flashpoint,
    Hybrid,
    Push,
    Clash,
}
