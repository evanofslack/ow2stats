use axum::{http::StatusCode, response::Json, routing::get, Router};
use serde_json::{json, Value};
use tracing::instrument;

use crate::error::AppError;
use crate::AppState;

pub fn create_router() -> Router<AppState> {
    Router::new()
        .route("/ping", get(ping))
        .route("/health", get(health_check))
        .route("/ready", get(ready_check))
}

#[instrument]
async fn ping() -> StatusCode {
    StatusCode::NO_CONTENT
}

#[instrument]
async fn health_check() -> Result<Json<Value>, AppError> {
    Ok(Json(json!({
        "status": "healthy",
        "service": "ow2stats-backend",
        "timestamp": chrono::Utc::now()
    })))
}

#[instrument]
async fn ready_check() -> Result<Json<Value>, AppError> {
    Ok(Json(json!({
        "status": "ready",
        "service": "ow2stats-backend",
        "timestamp": chrono::Utc::now()
    })))
}
