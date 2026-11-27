"""Price-change alerts and the data-collection trigger."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from ..config import Settings, get_settings
from ..db import Database
from ..deps import get_db
from ..schemas import ObservationIn
from ..security import require_admin

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    limit: int = Query(default=50, ge=1, le=200),
    unacknowledged_only: bool = Query(default=False),
    db: Database = Depends(get_db),
) -> dict:
    where = "WHERE acknowledged = 0" if unacknowledged_only else ""
    with db.connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, model, source, event_type, severity, old_price,
                   new_price, change_pct, message, acknowledged, created_at
            FROM alerts {where}
            ORDER BY created_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {"alerts": [dict(row) for row in rows]}


@router.post("/{alert_id}/acknowledge", dependencies=[Depends(require_admin)])
def acknowledge(alert_id: int, db: Database = Depends(get_db)) -> dict:
    with db.connect() as connection:
        connection.execute(
            "UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,)
        )
    return {"message": "Alert acknowledged."}


@router.post("/scan", dependencies=[Depends(require_admin)])
def scan_for_changes(
    background: BackgroundTasks,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Compare the two most recent observations per series and raise alerts.

    The previous implementation did this inside the mail-sending script and
    compared rows across retailers, so an Amazon price was routinely diffed
    against a Flipkart one. Grouping by (model, source) is what makes the
    comparison mean anything.
    """
    from ..services.alerting import scan_and_record, send_alert_email

    created = scan_and_record(db)
    if created and settings.smtp_user and settings.alert_recipient_list:
        background.add_task(send_alert_email, created, settings)

    return {
        "alerts_created": len(created),
        "email_queued": bool(
            created and settings.smtp_user and settings.alert_recipient_list
        ),
        "alerts": created,
    }


@router.post("/observations", dependencies=[Depends(require_admin)])
def record_observation(
    payload: ObservationIn, db: Database = Depends(get_db)
) -> dict:
    """Ingest a single price reading.

    Exposed so a collector running anywhere (a cron box, a GitHub Action, a
    laptop) can push data in without needing direct database access.
    """
    from datetime import datetime, timezone

    from ml.features import normalise_model, normalise_source

    inserted = db.record_observation(
        {
            "model": normalise_model(payload.model),
            "source": normalise_source(payload.source),
            "price": payload.price,
            "rating": payload.rating,
            "review_count": payload.review_count,
            "review_text": payload.review_text,
            "url": payload.url,
            "observed_at": payload.observed_at
            or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
    return {"recorded": inserted, "duplicate": not inserted}
