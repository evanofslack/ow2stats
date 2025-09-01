use axum::Router;
use std::net::SocketAddr;
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing::{debug, info, warn};

mod config;
mod database;
mod error;
mod handlers;

use config::Config;
use database::Database;

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

    let config = Config::load()?;
    debug!("Loaded config: {:?}", config);

    let db = Database::new(&config.database_url).await?;
    info!("Database connection established");

    db.migrate().await?;
    info!("Database migrations complete");

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
    handlers::heroes::create_router()
        .merge(handlers::status::create_router())
        .with_state(state)
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
}
