"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from ..config import Settings, get_settings
from ..db import Database
from ..deps import get_db

router = APIRouter(tags=["system"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    """Liveness. Cheap, and never touches the database or the models."""
    return {
        "status": "ok",
        "version": settings.api_version,
        "environment": settings.environment,
    }


@router.get("/ready")
def ready(
    response: Response,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Readiness. Every platform health check needs this to gate traffic."""
    checks: dict[str, object] = {}

    try:
        with db.connect() as connection:
            connection.execute("SELECT 1").fetchone()
        checks["database"] = "ok"
    except Exception as error:
        checks["database"] = f"failed: {error}"

    try:
        from pathlib import Path

        spec = Path(settings.artifact_dir) / "feature_spec.joblib"
        checks["model_artifacts"] = "ok" if spec.exists() else "missing"
    except Exception as error:
        checks["model_artifacts"] = f"failed: {error}"

    healthy = all(value == "ok" for value in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"ready": healthy, "checks": checks}
