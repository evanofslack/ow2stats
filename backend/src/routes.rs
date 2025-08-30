use axum::{routing::{post, get}, Router};

use crate::{handlers::heroes, AppState};

pub fn api_routes() -> Router<AppState> {
    Router::new()
        .route("/heroes", post(heroes::create_hero))
        .route(
            "/heroes/:id",
            get(heroes::get_hero).delete(heroes::delete_hero),
        )
        .route("/heroes/batch", post(heroes::batch_upload))
}