#!/usr/bin/env python3
"""
refresh_scraper.py

Compare the two most recent price entries PER (model, site) and send
an email summarizing any changes. This avoids cross-site comparisons.
"""

import sqlite3
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# ---------- CONFIG - update if needed ----------
DB_PATH = "competitor_tracker.db"
SENDER_EMAIL = "techierookies0105@gmail.com"
SENDER_PASSWORD = "dydmzgsxqtmvpdkb"   # use app password for Gmail
RECEIVER_EMAIL = "chaturiya06@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
# -----------------------------------------------

def fetch_latest_two_per_pair(db_path):
    """
    Return dict keyed by (model, site) -> list of up to 2 dicts (newest first).
    Each dict: {"price","rating","review_count","extracted_at"}.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT model, site, price, rating, review_count, extracted_at
        FROM dynamic_info
        WHERE model IS NOT NULL AND site IS NOT NULL
        ORDER BY model, site, datetime(extracted_at) DESC, id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    grouped = defaultdict(list)
    for model, site, price, rating, review_count, extracted_at in rows:
        key = (model, site)
        if len(grouped[key]) < 2:
            grouped[key].append({
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "extracted_at": extracted_at
            })
    return grouped

def build_alerts(grouped):
    """
    Given grouped[(model,site)] -> [newest, previous], produce alert lines.
    """
    alerts = []
    for (model, site), recs in grouped.items():
        if len(recs) < 2:
            continue  # need two rows to compare
        latest = recs[0]
        previous = recs[1]

        p_new = latest.get("price")
        p_old = previous.get("price")

        # Skip if price missing
        if p_new is None or p_old is None:
            continue

        if p_new != p_old:
            diff = p_new - p_old
            pct = (diff / p_old) * 100 if p_old else 0
            direction = "increased" if diff > 0 else "decreased"
            alerts.append(
                f"{model} @ {site}: Price {direction} from ₹{p_old:,.0f} → ₹{p_new:,.0f} "
                f"({'+' if diff>0 else ''}{diff:,.0f} | {pct:+.2f}%) "
                f"[latest: {latest.get('extracted_at')} | prev: {previous.get('extracted_at')}]"
            )
    return alerts

def send_email(subject, html_body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

        print("✅ Email sent successfully.")
        return True
    except Exception as e:
        print("❌ Failed to send email:", e)
        return False

def main():
    print(f"[{datetime.utcnow().isoformat()}] Starting refresh alert check...")
    if not os.path.exists(DB_PATH):
        print("DB not found at", DB_PATH)
        return

    grouped = fetch_latest_two_per_pair(DB_PATH)
    alerts = build_alerts(grouped)

    if not alerts:
        print("No price changes detected (per model+site). Nothing to email.")
        return

    # Build HTML email
    subject = f"[Price Alert] {len(alerts)} change(s) detected"
    html_body = "<h3>Price Change Alerts</h3><ul>"
    for a in alerts:
        html_body += f"<li>{a}</li>"
    html_body += f"</ul><p>Timestamp (UTC): {datetime.utcnow().isoformat()}</p>"

    print("Alerts to send:")
    for a in alerts:
        print(" -", a)

    send_email(subject, html_body)

if __name__ == "__main__":
    main()

