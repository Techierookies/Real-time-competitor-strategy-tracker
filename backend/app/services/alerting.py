"""Alert detection and notification."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from ..config import Settings
from ..db import Database

# Below this, a change is noise rather than a repricing signal.
MATERIAL_CHANGE = 0.01


def scan_and_record(db: Database) -> list[dict]:
    """Diff the latest two observations per (model, source) and store alerts."""
    created: list[dict] = []

    query = """
        SELECT model, source, price, observed_at
        FROM (
            SELECT model, source, price, observed_at,
                   ROW_NUMBER() OVER (
                       PARTITION BY model, source
                       ORDER BY observed_at DESC
                   ) AS rank
            FROM price_observations
        )
        WHERE rank <= 2
        ORDER BY model, source, observed_at DESC
    """

    with db.connect() as connection:
        rows = [dict(row) for row in connection.execute(query)]

    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["model"], row["source"]), []).append(row)

    for (model, source), pair in grouped.items():
        if len(pair) < 2:
            continue
        new_price, old_price = float(pair[0]["price"]), float(pair[1]["price"])
        if old_price <= 0:
            continue

        change = (new_price - old_price) / old_price
        if abs(change) < MATERIAL_CHANGE:
            continue

        if abs(change) > 0.40:
            event_type, severity = "suspected_scrape_error", "data_quality"
        elif change < 0:
            event_type = "price_drop"
            severity = "high" if change < -0.10 else "medium"
        else:
            event_type = "price_increase"
            severity = "high" if change > 0.10 else "medium"

        message = (
            f"{model} on {source}: Rs {old_price:,.0f} -> Rs {new_price:,.0f} "
            f"({change:+.1%})"
        )
        alert = {
            "model": model,
            "source": source,
            "event_type": event_type,
            "severity": severity,
            "old_price": old_price,
            "new_price": new_price,
            "change_pct": round(change * 100, 2),
            "message": message,
        }
        db.record_alert(alert)
        created.append(alert)

    return created


def send_alert_email(alerts: list[dict], settings: Settings) -> bool:
    """Send a digest of alerts.

    Credentials come from the environment. The previous version hardcoded a
    Gmail app password in the source file, which published working credentials
    to everyone who cloned the repository.
    """
    if not (settings.smtp_user and settings.smtp_password):
        return False
    recipients = settings.alert_recipient_list
    if not recipients:
        return False

    lines = "".join(f"<li>{alert['message']}</li>" for alert in alerts)
    body = (
        f"<h3>{len(alerts)} competitor price change(s) detected</h3>"
        f"<ul>{lines}</ul>"
    )

    message = EmailMessage()
    message["From"] = settings.smtp_user
    message["To"] = ", ".join(recipients)
    message["Subject"] = f"[Price Alert] {len(alerts)} change(s) detected"
    message.set_content("Enable HTML to view this digest.")
    message.add_alternative(body, subtype="html")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls(context=context)
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
        return True
    except Exception as error:
        # Notification is best-effort: a mail outage must not fail the request
        # that triggered the scan, and the alerts are already persisted.
        print(f"Alert email failed: {error}")
        return False
