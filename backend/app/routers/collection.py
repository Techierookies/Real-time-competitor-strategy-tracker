"""Live data: current prices, collection status, manual runs and ingestion."""

from __future__ import annotations

import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..config import Settings, get_settings
from ..db import Database
from ..deps import get_db
from ..schemas import ObservationIn
from ..security import require_admin
from ..services import live

router = APIRouter(prefix="/api", tags=["live data"])


class IngestRequest(BaseModel):
    observations: list[ObservationIn] = Field(min_length=1, max_length=200)


@router.get("/prices/latest")
def latest_prices(db: Database = Depends(get_db)) -> dict:
    """The newest reading for every tracked series, with its last change."""
    return {"prices": db.latest_prices()}


@router.get("/prices/history/{model}/{source}")
def price_history(
    model: str,
    source: str,
    days: int = Query(default=90, ge=1, le=730),
    db: Database = Depends(get_db),
) -> dict:
    """Daily median price for one series, for charting."""
    from ml.features import clean_frame, normalise_model, normalise_source, to_daily_panel

    model, source = normalise_model(model), normalise_source(source)
    frame = db.series_history(model, source, limit=5000)
    if frame.empty:
        raise HTTPException(status_code=404, detail=f"No readings for {model} on {source}.")
    panel = to_daily_panel(clean_frame(frame)).tail(days)
    return {
        "model": model,
        "source": source,
        "points": [
            {"date": str(row.Scraped_At.date()), "price": round(float(row.Price), 2),
             "observed": int(row.observations)}
            for row in panel.itertuples()
        ],
    }


@router.get("/collect/status")
def collection_status(db: Database = Depends(get_db)) -> dict:
    """What the collector did recently, product by product."""
    runs = db.recent_runs(limit=10)
    latest = runs[0] if runs else None
    return {
        "scheduler": {
            "collect_interval_minutes": live.state["collect_interval_minutes"],
            "next_collection_at": live.state["next_collection_at"],
            "retrain_interval_hours": live.state["retrain_interval_hours"],
            "next_retrain_at": live.state["next_retrain_at"],
            "last_retrain": live.state["last_retrain"],
        },
        "live_history_days": live.live_history_days(db),
        "latest_run": latest,
        "latest_run_results": db.run_results(latest["id"]) if latest else [],
        "recent_runs": runs,
    }


@router.post("/collect/run", dependencies=[Depends(require_admin)])
def trigger_collection(
    background: BackgroundTasks,
    wait: bool = Query(default=False, description="Run inline and return the summary."),
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Start a collection pass now."""
    if wait:
        return live.run_collection(db, settings, "manual")
    background.add_task(live.run_collection, db, settings, "manual")
    return {"status": "started", "check": "/api/collect/status"}


@router.post("/model/retrain", dependencies=[Depends(require_admin)])
def trigger_retrain(
    background: BackgroundTasks,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Retrain the forecasters; switches to live data once there is enough."""
    background.add_task(live.run_retrain, db, settings)
    return {"status": "started", "check": "/api/model-card"}


@router.post("/collect/ingest")
def ingest(
    payload: IngestRequest,
    x_collector_token: str | None = Header(default=None),
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Accept readings from an external collector, such as GitHub Actions.

    Authenticated with a shared secret rather than a user login, so a
    scheduled job can push data without storing an admin password. Disabled
    entirely when COLLECTOR_TOKEN is not set.
    """
    if not settings.collector_token:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ingestion is not enabled.")
    if not x_collector_token or not hmac.compare_digest(x_collector_token, settings.collector_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid collector token.")

    from ml.features import normalise_model, normalise_source

    stored = duplicates = 0
    for item in payload.observations:
        inserted = db.record_observation(
            {
                "model": normalise_model(item.model),
                "source": normalise_source(item.source),
                "price": item.price,
                "rating": item.rating,
                "review_count": item.review_count,
                "review_text": item.review_text,
                "url": item.url,
                "observed_at": item.observed_at
                or datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )
        stored += int(inserted)
        duplicates += int(not inserted)
    from ..services.alerting import scan_and_record

    alerts = scan_and_record(db) if stored else []
    return {"stored": stored, "duplicates": duplicates, "alerts_created": len(alerts)}


@router.get("/reviews/{model}")
def reviews(
    model: str,
    limit: int = Query(default=30, ge=1, le=200),
    db: Database = Depends(get_db),
) -> dict:
    """Most recent stored review snippets for one handset, across retailers."""
    from ml.features import normalise_model

    model = normalise_model(model)
    with db.connect() as connection:
        rows = connection.execute(
            """
            SELECT source, rating, review_text AS review, observed_at
            FROM price_observations
            WHERE model = ? AND review_text IS NOT NULL AND review_text != ''
            ORDER BY observed_at DESC LIMIT ?
            """,
            (model, limit),
        ).fetchall()
    return {"model": model, "reviews": [dict(row) for row in rows]}
