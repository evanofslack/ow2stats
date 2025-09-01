use sqlx::{postgres::PgPoolOptions, PgPool};
use tracing::{debug, info};

pub mod models;

#[derive(Clone)]
pub struct Database {
    pool: PgPool,
}

impl Database {
    pub async fn new(database_url: &str) -> anyhow::Result<Self> {
        info!("Connecting to database: {}", database_url);
        debug!("Database URL breakdown:");
        if let Ok(url) = url::Url::parse(database_url) {
            debug!("  Host: {:?}", url.host_str());
            debug!("  Port: {:?}", url.port());
            debug!("  Database: {}", url.path().trim_start_matches('/'));
            debug!("  Username: {:?}", url.username());
        }

        debug!("Creating connection pool with max_connections=10");
        let pool = PgPoolOptions::new()
            .max_connections(10)
            .connect(database_url)
            .await?;

        debug!("Database connection pool created successfully");
        Ok(Self { pool })
    }

    pub async fn migrate(&self) -> anyhow::Result<()> {
        info!("Running database migrations");

        let migrations_result = sqlx::migrate!("./migrations").run(&self.pool).await;
        match migrations_result {
            Ok(_) => {
                debug!("All migrations applied successfully");
                Ok(())
            }
            Err(e) => {
                debug!("Migration failed with error: {}", e);
                Err(e.into())
            }
        }
    }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }
}

