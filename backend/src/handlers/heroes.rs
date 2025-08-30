use axum::{
    extract::{Path, State, Json},
    http::StatusCode,
    response::Json as JsonResponse,
};
use serde_json::{json, Value};
use tracing::{info, instrument};

use crate::{
    database::models::{CreateHeroStats, HeroStats},
    error::AppError,
    AppState,
};

#[instrument(skip(state))]
pub async fn get_hero(
    State(state): State<AppState>,
    Path(id): Path<i32>,
) -> Result<JsonResponse<HeroStats>, AppError> {
    info!("Getting hero with id: {}", id);

    let hero = sqlx::query_as::<_, HeroStats>("SELECT * FROM hero_stats WHERE id = $1")
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
    info!("Creating hero: {}", hero_data.hero);

    let hero = sqlx::query_as::<_, HeroStats>(
        r#"
        INSERT INTO hero_stats (hero, pick_rate, win_rate, region, platform, role, gamemode, map, tier, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING *
        "#,
    )
    .bind(&hero_data.hero)
    .bind(hero_data.pick_rate)
    .bind(hero_data.win_rate)
    .bind(&hero_data.region)
    .bind(&hero_data.platform)
    .bind(&hero_data.role)
    .bind(&hero_data.gamemode)
    .bind(&hero_data.map)
    .bind(&hero_data.tier)
    .bind(hero_data.timestamp)
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
            INSERT INTO hero_stats (hero, pick_rate, win_rate, region, platform, role, gamemode, map, tier, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (hero, region, platform, role, gamemode, map, tier, timestamp) 
            DO UPDATE SET 
                pick_rate = EXCLUDED.pick_rate,
                win_rate = EXCLUDED.win_rate
            "#,
        )
        .bind(&hero_data.hero)
        .bind(hero_data.pick_rate)
        .bind(hero_data.win_rate)
        .bind(&hero_data.region)
        .bind(&hero_data.platform)
        .bind(&hero_data.role)
        .bind(&hero_data.gamemode)
        .bind(&hero_data.map)
        .bind(&hero_data.tier)
        .bind(hero_data.timestamp)
        .execute(&mut *transaction)
        .await;

        match result {
            Ok(_) => created_count += 1,
            Err(e) => {
                errors.push(json!({
                    "index": index,
                    "hero": hero_data.hero,
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
