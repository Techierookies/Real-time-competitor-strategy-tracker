"""Shared dependency providers."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status

from .config import Settings, get_settings
from .db import Database


@lru_cache
def _database(path: str) -> Database:
    return Database(path)


def get_db(settings: Settings = Depends(get_settings)) -> Database:
    return _database(str(settings.sqlite_path))


@lru_cache
def _forecast_service(artifact_dir: str):
    # Imported lazily so the API can still boot (and report an honest
    # "model unavailable") when the artifacts have not been trained yet.
    from ml.predict import ForecastService

    return ForecastService(artifact_dir)


def get_forecast_service(settings: Settings = Depends(get_settings)):
    try:
        return _forecast_service(settings.artifact_dir)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Forecast artifacts are not available. Run "
                "`python -m ml.train --data <csv>` to build them."
            ),
        ) from error
