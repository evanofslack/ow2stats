use axum::{
    response::Json,
    routing::{get},
    Router,
};
use serde_json::{json, Value};
use std::net::SocketAddr;
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing::{info, instrument};

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

    info!("Starting OW2Stats Backend API Server");

    dotenvy::dotenv().ok();
    let config = Config::load()?;
    info!("Loaded config: {:?}", config);
    info!("Configuration loaded successfully");

    let db = Database::new(&config.database_url).await?;
    info!("Database connection established");

    db.migrate().await?;
    info!("Database migrations completed");

    let state = AppState {
        db,
        config: config.clone(),
    };

    let app = create_router(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], config.port));
    info!("Server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await?;
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

