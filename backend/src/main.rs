use axum::{response::Json, routing::get, Router};
use serde_json::{json, Value};
use std::net::SocketAddr;
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing::{debug, info, instrument, warn};

mod config;
mod database;
mod error;
mod handlers;
mod routes;

use config::Config;
use database::Database;
use error::AppError;

#[derive(Clone)]
pub struct AppState {
    pub db: Database,
    pub config: Config,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();
    info!("Starting service");

    match dotenvy::dotenv() {
        Ok(path) => debug!("Loaded .env from: {:?}", path),
        Err(e) => warn!("No .env file found or error loading: {}", e),
    }

    debug!("Environment variables:");
    for (key, value) in std::env::vars() {
        if key.starts_with("OW2STATS_") {
            debug!("  {}: {}", key, value);
        }
    }

    debug!("Loading config");
    let config = Config::load()?;
    info!("Loaded config: {:?}", config);

    let db = Database::new(&config.database_url).await?;
    info!("Database connection established successfully");

    db.migrate().await?;
    info!("Database migrations completed successfully");

    let state = AppState {
        db,
        config: config.clone(),
    };

    let app = create_router(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], config.port));
    info!("Server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
    info!("Server ready to accept connections");
    axum::serve(listener, app).await?;

    Ok(())
}

fn create_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health_check))
        .nest("/api", routes::api_routes())
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

#[instrument]
async fn health_check() -> Result<Json<Value>, AppError> {
    Ok(Json(json!({
        "status": "healthy",
        "service": "ow2stats-backend",
        "timestamp": chrono::Utc::now()
    })))
}
