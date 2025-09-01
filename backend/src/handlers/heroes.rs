use axum::{
    extract::{Json, Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    response::Json as JsonResponse,
    routing::{get, post},
    Router,
};
use serde_json::{json, Value};
use tracing::{info, instrument};

use crate::{
    database::models::{CreateHeroStats, HeroStats},
    error::AppError,
    AppState,
};
use chrono::{DateTime, Utc};
use serde::Deserialize;
use sqlx::{Postgres, QueryBuilder};
use std::fmt;

pub fn create_router() -> Router<AppState> {
    Router::new()
        .route("/api/v1/test", get(|| async { "api routes working" }))
        .route("/api/v1/heroes", get(get_heroes).post(create_hero))
        .route("/api/v1/hero/:id", get(get_hero).delete(delete_hero))
        .route("/api/v1/heroes/batch", post(batch_upload))
}

#[derive(Deserialize, Debug)]
pub struct HeroQueryParams {
    hero_id: Option<String>,
    region: Option<String>,
    platform: Option<String>,
    gamemode: Option<String>,
    map: Option<String>,
    tier: Option<String>,
    start_time: Option<DateTime<Utc>>,
    end_time: Option<DateTime<Utc>>,
    order_by: Option<OrderBy>,
    order: Option<Order>,
    _limit: Option<usize>,
}

#[derive(Deserialize, Debug)]
#[serde(rename_all = "snake_case")]
pub enum OrderBy {
    PickRate,
    WinRate,
    InsertedAt,
}

#[derive(Deserialize, Debug)]
#[serde(rename_all = "lowercase")]
pub enum Order {
    Asc,
    Desc,
}

impl fmt::Display for OrderBy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            OrderBy::PickRate => write!(f, "pick_rate"),
            OrderBy::WinRate => write!(f, "win_rate"),
            OrderBy::InsertedAt => write!(f, "inserted_at"),
        }
    }
}

impl fmt::Display for Order {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Order::Asc => write!(f, "ASC"),
            Order::Desc => write!(f, "DESC"),
        }
    }
}

#[instrument(skip(state))]
pub async fn get_heroes(
    State(state): State<AppState>,
    Query(params): Query<HeroQueryParams>,
) -> Result<impl IntoResponse, AppError> {
    let mut qb = QueryBuilder::<Postgres>::new("SELECT * FROM hero_stats");
    let mut has_where = false;

    if let Some(hero_id) = params.hero_id {
        if !has_where {
            qb.push(" WHERE ");
            has_where = true;
        } else {
            qb.push(" AND ");
        }
        qb.push("hero_id = ").push_bind(hero_id);
    }

    if let Some(region) = params.region {
        if !has_where {
            qb.push(" WHERE ");
            has_where = true;
        } else {
            qb.push(" AND ");
        }
        qb.push("region = ").push_bind(region);
    }

    if let Some(platform) = params.platform {
        if !has_where {
            qb.push(" WHERE ");
            has_where = true;
        } else {
            qb.push(" AND ");
        }
        qb.push("platform = ").push_bind(platform);
    }

    if let Some(gamemode) = params.gamemode {
        if !has_where {
            qb.push(" WHERE ");
            has_where = true;
        } else {
            qb.push(" AND ");
        }
        qb.push("gamemode = ").push_bind(gamemode);
    }

    if let Some(map) = params.map {
        if !has_where {
            qb.push(" WHERE ");
            has_where = true;
        } else {
            qb.push(" AND ");
        }
        qb.push("map = ").push_bind(map);
    }

    if let Some(tier) = params.tier {
        if !has_where {
            qb.push(" WHERE ");
            has_where = true;
        } else {
            qb.push(" AND ");
        }
        qb.push("tier = ").push_bind(tier);
    }

    if let Some(start_time) = params.start_time {
        if !has_where {
            qb.push(" WHERE ");
            has_where = true;
        } else {
            qb.push(" AND ");
        }
        qb.push("inserted_at >= ").push_bind(start_time);
    }

    if let Some(end_time) = params.end_time {
        if !has_where {
            qb.push(" WHERE ");
        } else {
            qb.push(" AND ");
        }
        qb.push("inserted_at < ").push_bind(end_time);
    }

    if let Some(order_by) = params.order_by {
        let order = params.order.unwrap_or(Order::Asc);
        qb.push(" ORDER BY ")
            .push(order_by.to_string())
            .push(" ")
            .push(order.to_string());
    }

    let heroes = qb
        .build_query_as::<HeroStats>()
        .fetch_all(state.db.pool())
        .await?;

    Ok(Json(heroes))
}

#[instrument(skip(state))]
pub async fn get_hero(
    State(state): State<AppState>,
    Path(id): Path<i32>,
) -> Result<JsonResponse<HeroStats>, AppError> {
    info!("Getting hero with id: {}", id);

    let hero = sqlx::query_as::<_, HeroStats>(
        "SELECT * FROM hero_stats WHERE id = $1 ORDER BY inserted_at LIMIT 1",
    )
    .bind(id)
    .fetch_optional(state.db.pool())
    .await?
    .ok_or_else(|| AppError::NotFound {
        resource: "Hero".to_string(),
    })?;

    Ok(JsonResponse(hero))
}

#[instrument(skip(state))]
pub async fn create_hero(
    State(state): State<AppState>,
    Json(hero_data): Json<CreateHeroStats>,
) -> Result<(StatusCode, JsonResponse<HeroStats>), AppError> {
    info!("Creating hero: {}", hero_data.hero_id);

    let hero = sqlx::query_as::<_, HeroStats>(
        r#"
        INSERT INTO hero_stats (hero_id, pick_rate, win_rate, region, platform, gamemode, map, tier, inserted_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
        RETURNING *
        "#,
    )
    .bind(&hero_data.hero_id)
    .bind(hero_data.pick_rate)
    .bind(hero_data.win_rate)
    .bind(&hero_data.region)
    .bind(&hero_data.platform)
    .bind(&hero_data.gamemode)
    .bind(&hero_data.map)
    .bind(&hero_data.tier)
    .fetch_one(state.db.pool())
    .await?;

    Ok((StatusCode::CREATED, JsonResponse(hero)))
}

#[instrument(skip(state))]
pub async fn delete_hero(
    State(state): State<AppState>,
    Path(id): Path<i32>,
) -> Result<StatusCode, AppError> {
    info!("Deleting hero with id: {}", id);

    let result = sqlx::query("DELETE FROM hero_stats WHERE id = $1")
        .bind(id)
        .execute(state.db.pool())
        .await?;

    if result.rows_affected() == 0 {
        return Err(AppError::NotFound {
            resource: "Hero".to_string(),
        });
    }

    Ok(StatusCode::NO_CONTENT)
}

#[instrument(skip(state))]
pub async fn batch_upload(
    State(state): State<AppState>,
    Json(heroes_data): Json<Vec<CreateHeroStats>>,
) -> Result<JsonResponse<Value>, AppError> {
    info!("Batch uploading {} heroes", heroes_data.len());

    if heroes_data.is_empty() {
        return Err(AppError::Validation {
            message: "No heroes provided".to_string(),
        });
    }

    let mut transaction = state.db.pool().begin().await?;
    let mut created_count = 0;
    let mut errors = Vec::new();

    for (index, hero_data) in heroes_data.iter().enumerate() {
        let result = sqlx::query(
            r#"
            INSERT INTO hero_stats (hero_id, pick_rate, win_rate, region, platform, gamemode, map, tier, inserted_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            ON CONFLICT (hero_id, region, platform, gamemode, map, tier, inserted_at) 
            DO UPDATE SET 
                pick_rate = EXCLUDED.pick_rate,
                win_rate = EXCLUDED.win_rate,
                updated_at = NOW()
            "#,
        )
        .bind(&hero_data.hero_id)
        .bind(hero_data.pick_rate)
        .bind(hero_data.win_rate)
        .bind(&hero_data.region)
        .bind(&hero_data.platform)
        .bind(&hero_data.gamemode)
        .bind(&hero_data.map)
        .bind(&hero_data.tier)
        .execute(&mut *transaction)
        .await;

        match result {
            Ok(_) => created_count += 1,
            Err(e) => {
                errors.push(json!({
                    "index": index,
                    "hero_id": hero_data.hero_id,
                    "error": e.to_string()
                }));
            }
        }
    }

    transaction.commit().await?;

    Ok(JsonResponse(json!({
        "message": "Batch upload completed",
        "total_submitted": heroes_data.len(),
        "successful": created_count,
        "errors": errors
    })))
}
