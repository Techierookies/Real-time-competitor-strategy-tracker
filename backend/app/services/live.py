"""
Background jobs for live operation: scheduled collection and retraining.

The scheduler is a plain asyncio task started in the app's lifespan. Each job
runs in a worker thread so a slow retailer never blocks request handling. It
is intentionally simple: this deployment is a single SQLite-backed instance.
A multi-replica deployment should move these jobs to one dedicated worker (or
the GitHub Actions workflow) so two replicas do not scrape the same pages.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..db import Database
from .alerting import scan_and_record

logger = logging.getLogger("tracker.live")

state: dict = {
    "collect_interval_minutes": 0,
    "retrain_interval_hours": 0,
    "next_collection_at": None,
    "next_retrain_at": None,
    "last_retrain": None,
}
_retrain_lock = threading.Lock()


def run_collection(db: Database, settings, trigger: str) -> dict:
    """One collection pass followed by an alert scan over the new readings."""
    from collector.live import collect_once

    summary = collect_once(db, settings, trigger=trigger)
    if summary.get("status") != "skipped" and summary.get("stored"):
        summary["alerts_created"] = len(scan_and_record(db))
    logger.info(
        "collection %s: stored=%s rejected=%s blocked=%s errors=%s",
        summary.get("status"), summary.get("stored"), summary.get("rejected"),
        summary.get("blocked"), summary.get("errors"),
    )
    return summary


def live_history_days(db: Database) -> dict[str, int]:
    """Distinct days of live readings per series."""
    with db.connect() as connection:
        rows = connection.execute(
            """
            SELECT model || ' · ' || source AS series,
                   COUNT(DISTINCT date(observed_at)) AS days
            FROM price_observations
            GROUP BY model, source
            """
        ).fetchall()
    return {row["series"]: row["days"] for row in rows}


def run_retrain(db: Database, settings, bootstrap_csv: Path | None = None) -> dict:
    """Retrain the forecasters, on live data once there is enough of it.

    Until every tracked series has `min_training_days` of history, the models
    are trained on the synthetic bootstrap panel instead, and the model card
    says so. Training on three weeks of real data would produce models that
    look precise and are not.
    """
    if not _retrain_lock.acquire(blocking=False):
        return {"status": "skipped", "reason": "a retrain is already running"}

    try:
        from ml.features import clean_frame, load_frame
        from ml.train import train_from_frame

        history = live_history_days(db)
        enough = bool(history) and min(history.values()) >= settings.min_training_days
        if enough:
            frame = clean_frame(db.observations_frame())
            source, label = "live", "price_observations (live database)"
        else:
            csv = bootstrap_csv or Path(settings.artifact_dir).parent.parent / "data" / "competitor_prices_synthetic.csv"
            frame = load_frame(str(csv))
            source, label = "synthetic", str(csv)

        artifact_dir = Path(settings.artifact_dir)
        with tempfile.TemporaryDirectory() as scratch:
            report = train_from_frame(frame, out_dir=scratch, dataset_label=label, data_source=source)
            # Swap in the new artifacts only after training fully succeeded,
            # so a failed run never leaves the API serving half a model set.
            artifact_dir.mkdir(parents=True, exist_ok=True)
            for item in Path(scratch).iterdir():
                shutil.copy2(item, artifact_dir / item.name)

        from ..deps import _forecast_service
        _forecast_service.cache_clear()

        result = {
            "status": "ok",
            "data_source": source,
            "rows": report.get("raw_rows"),
            "live_history_days": history,
            "min_training_days": settings.min_training_days,
            "beats_baseline": {
                h: r["selection"]["beats_baseline"] for h, r in report["horizons"].items()
            },
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        state["last_retrain"] = result
        return result
    finally:
        _retrain_lock.release()


async def scheduler_loop(db: Database, settings) -> None:
    """Run collection and retraining on their intervals until cancelled."""
    collect_every = timedelta(minutes=settings.collect_interval_minutes)
    retrain_every = timedelta(hours=settings.retrain_interval_hours)
    now = datetime.now(timezone.utc)
    # First collection shortly after boot, so a fresh deploy shows data quickly.
    next_collect = now + timedelta(seconds=30) if collect_every else None
    next_retrain = now + retrain_every if retrain_every else None

    state["collect_interval_minutes"] = settings.collect_interval_minutes
    state["retrain_interval_hours"] = settings.retrain_interval_hours

    while True:
        state["next_collection_at"] = next_collect.isoformat(timespec="seconds") if next_collect else None
        state["next_retrain_at"] = next_retrain.isoformat(timespec="seconds") if next_retrain else None
        now = datetime.now(timezone.utc)
        try:
            if next_collect and now >= next_collect:
                await asyncio.to_thread(run_collection, db, settings, "scheduled")
                next_collect = datetime.now(timezone.utc) + collect_every
            if next_retrain and now >= next_retrain:
                await asyncio.to_thread(run_retrain, db, settings)
                next_retrain = datetime.now(timezone.utc) + retrain_every
        except Exception:  # keep the loop alive whatever one job does
            logger.exception("scheduled job failed")
        await asyncio.sleep(20)
