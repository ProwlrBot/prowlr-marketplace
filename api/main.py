from __future__ import annotations

import json
import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.config import INDEX_PATH, DB_PATH, CORS_ORIGINS, RATE_LIMIT
from api.db import init_db
from api.search import SearchEngine
from api.routers import listings, categories, stats

limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])

def load_index(index_path: pathlib.Path) -> dict:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    return data

def create_app(
    index_path: pathlib.Path | None = None,
    db_path: pathlib.Path | None = None,
) -> FastAPI:
    idx_path = index_path or INDEX_PATH
    database_path = db_path or DB_PATH

    app = FastAPI(
        title="ProwlrBot Marketplace API",
        description="REST API for the ProwlrBot marketplace registry",
        version="1.0.0",
    )

    if idx_path and idx_path.exists():
        index_data = load_index(idx_path)
        app.state.listings = index_data.get("listings", [])
        app.state.index_meta = {
            "version": index_data.get("version", "1"),
            "total": index_data.get("total", 0),
            "categories": index_data.get("categories", {}),
        }
    else:
        app.state.listings = []
        app.state.index_meta = {"version": "1", "total": 0, "categories": {}}

    app.state.search_engine = SearchEngine(app.state.listings)
    app.state.db_path = database_path

    init_db(database_path)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(listings.router, prefix="/v1")
    app.include_router(categories.router, prefix="/v1")
    app.include_router(stats.router, prefix="/v1")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
