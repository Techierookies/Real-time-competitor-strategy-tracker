"""
Application entrypoint.

Differences from the previous `main.py` that matter operationally:

* Model loading and database setup happen in a lifespan handler rather than at
  import time. Previously `initialize_all()` ran during module import, which
  meant a missing artifact or an unreachable Gemini endpoint crashed the
  process before it could serve a health check, and the container would be
  restarted forever with no useful signal.
* CORS origins come from configuration instead of a hardcoded localhost URL,
  so a deployed frontend can actually reach the API.
* Routes are grouped into routers instead of accumulating in one 400-line
  module with commented-out blocks between live endpoints.
* Unhandled exceptions return a generic message and are logged, rather than
  returning `str(e)` to the caller, which leaked file paths and SQL.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Make the repository root importable so `ml` resolves when the API is started
# from inside the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import asyncio  # noqa: E402

from .config import get_settings  # noqa: E402
from .db import Database  # noqa: E402
from .routers import alerts, assistant, auth, catalog, collection, forecast, health  # noqa: E402
from .services import live  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)
logger = logging.getLogger("tracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    problems = settings.validate_for_production()
    if problems:
        for problem in problems:
            logger.error("Configuration problem: %s", problem)
        raise RuntimeError(
            "Refusing to start in production with an unsafe configuration."
        )

    db = Database(settings.sqlite_path)
    db.initialise()
    logger.info("Database ready at %s", settings.sqlite_path)

    artifacts = Path(settings.artifact_dir) / "feature_spec.joblib"
    if artifacts.exists():
        logger.info("Model artifacts found at %s", settings.artifact_dir)
    else:
        # A warning, not a crash. The API still serves auth, catalogue and
        # health; only the forecasting routes return 503 until training runs.
        logger.warning(
            "No model artifacts at %s. Forecast endpoints will return 503 "
            "until `python -m ml.train` has been run.",
            settings.artifact_dir,
        )

    scheduler = None
    if settings.collect_interval_minutes or settings.retrain_interval_hours:
        scheduler = asyncio.create_task(live.scheduler_loop(db, settings))
        logger.info(
            "Live scheduler on: collect every %s min, retrain every %s h",
            settings.collect_interval_minutes, settings.retrain_interval_hours,
        )

    yield

    if scheduler:
        scheduler.cancel()
    logger.info("Shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=(
            "Forecasts competitor listing prices for consumer electronics "
            "across retailers, and recommends a listing price from the "
            "forecast, a margin floor and a stated demand elasticity."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    for router in (
        health.router,
        auth.router,
        forecast.router,
        collection.router,
        catalog.router,
        alerts.router,
        assistant.router,
    ):
        app.include_router(router)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error."},
        )

    @app.get("/", tags=["system"])
    def root() -> dict:
        return {
            "name": settings.api_title,
            "version": settings.api_version,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
