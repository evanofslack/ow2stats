use axum::{
    routing::{get, post},
    Router,
};

use crate::{handlers::heroes, AppState};

pub fn api_routes() -> Router<AppState> {
    println!("api_routes() called");
    Router::new()
        .route("/test", get(|| async { "api routes working" }))
        .route("/heroes", get(heroes::get_heroes).post(heroes::create_hero))
        .route(
            "/hero/:id",
            get(heroes::get_hero).delete(heroes::delete_hero),
        )
        .route("/heroes/batch", post(heroes::batch_upload))
}
