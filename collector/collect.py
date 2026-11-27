"""
Price collector.

Problems in the original scraper that this fixes:

* It wrote 'amazon.in' and 'flipkart.com' into the database while the
  prediction layer filtered on 'Amazon' and 'Flipkart'. Nothing ever matched,
  so the "current market price" shown in the dashboard was silently the
  model's own output. Labels are now canonicalised on write.
* A failed price parse was stored as a literal 10000.0 (and ratings as NULL),
  which then entered the training data as though it were a real observation.
  Readings that fail validation are now rejected and counted, not stored.
* Every page was fetched with no delay, no retry and no user agent, so runs
  were both impolite and unreliable.
* Raw HTML for every fetch was kept forever, which is what grew the committed
  database to 54 MB. Raw HTML is now optional and off by default.

`--source live` scrapes the product pages listed in collector/targets.json
(see collector/live.py). `--source sample` replays the bundled synthetic CSV
so the pipeline can be demonstrated end to end without scraping anything.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import get_settings  # noqa: E402
from backend.app.db import Database  # noqa: E402
from ml.features import normalise_model, normalise_source  # noqa: E402

# A listing outside this band is a parsing failure, not a bargain.
MIN_PLAUSIBLE_PRICE = 10_000
MAX_PLAUSIBLE_PRICE = 400_000


@dataclass
class Reading:
    model: str
    source: str
    price: float
    rating: float | None
    review_count: int | None
    url: str | None
    observed_at: str


def validate(reading: Reading) -> tuple[bool, str]:
    """Reject anything that would poison the training set."""
    if reading.price is None:
        return False, "price missing"
    if not MIN_PLAUSIBLE_PRICE <= reading.price <= MAX_PLAUSIBLE_PRICE:
        return False, f"price {reading.price} outside plausible band"
    if reading.rating is not None and not 0 <= reading.rating <= 5:
        return False, f"rating {reading.rating} out of range"
    if reading.model in ("", "Unknown"):
        return False, "model not recognised"
    if reading.source in ("", "Unknown"):
        return False, "source not recognised"
    return True, ""


def fetch(url: str, settings, attempts: int = 3) -> str | None:
    """Fetch a page with backoff and a declared user agent."""
    headers = {
        "User-Agent": settings.scrape_user_agent,
        "Accept-Language": "en-IN,en;q=0.9",
    }
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                return response.text
            if response.status_code in (429, 503):
                # Backing off on throttling is the difference between a
                # collector that keeps working and one that gets blocked.
                wait = settings.scrape_delay_seconds * (2**attempt)
                print(f"  throttled ({response.status_code}), waiting {wait:.0f}s")
                time.sleep(wait)
                continue
            print(f"  HTTP {response.status_code} for {url}")
            return None
        except requests.RequestException as error:
            print(f"  attempt {attempt} failed: {error}")
            time.sleep(settings.scrape_delay_seconds * attempt)
    return None


def readings_from_sample(path: Path, limit: int | None = None) -> list[Reading]:
    """Replay a CSV as though it had just been collected."""
    frame = pd.read_csv(path)
    if limit:
        frame = frame.tail(limit)

    readings = []
    for _, row in frame.iterrows():
        readings.append(
            Reading(
                model=normalise_model(row.get("Model")),
                source=normalise_source(row.get("Source")),
                price=float(row.get("Price", 0) or 0),
                rating=(
                    float(row["Rating"]) if pd.notna(row.get("Rating")) else None
                ),
                review_count=None,
                url=row.get("URL"),
                observed_at=str(row.get("Scraped_At")),
            )
        )
    return readings


def store(db: Database, readings: list[Reading]) -> dict:
    """Validate, then insert. Returns a summary rather than printing counts."""
    summary = {"accepted": 0, "duplicates": 0, "rejected": 0, "reasons": {}}

    for reading in readings:
        ok, reason = validate(reading)
        if not ok:
            summary["rejected"] += 1
            summary["reasons"][reason] = summary["reasons"].get(reason, 0) + 1
            continue

        inserted = db.record_observation(
            {
                "model": reading.model,
                "source": reading.source,
                "price": reading.price,
                "rating": reading.rating,
                "review_count": reading.review_count,
                "review_text": None,
                "url": reading.url,
                "observed_at": reading.observed_at,
            }
        )
        if inserted:
            summary["accepted"] += 1
        else:
            summary["duplicates"] += 1

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect competitor prices.")
    parser.add_argument(
        "--source",
        choices=["sample", "live"],
        default="sample",
        help="'sample' replays the bundled synthetic CSV; 'live' scrapes the "
        "product pages in collector/targets.json.",
    )
    parser.add_argument("--file", help="CSV path when --source sample.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--targets", help="Alternative targets JSON for --source live.")
    parser.add_argument(
        "--push-to",
        help="Send live readings to a deployed API (needs COLLECTOR_TOKEN) "
        "instead of the local database.",
    )
    args = parser.parse_args()

    settings = get_settings()
    db = Database(settings.sqlite_path)
    db.initialise()

    if args.source == "live":
        import json
        import os

        from collector.live import collect_once, load_targets

        targets = load_targets(args.targets) if args.targets else None
        summary = collect_once(
            db,
            settings,
            trigger="cli",
            targets=targets,
            push_to=args.push_to,
            push_token=os.getenv("COLLECTOR_TOKEN"),
        )
        for result in summary.get("results", []):
            price = f"Rs {result['price']:,.0f}" if result["price"] else "-"
            print(
                f"{result['status']:<12} {result['model']:<10} {result['source']:<9} "
                f"{price:>12}  {result['message']}"
            )
        print(json.dumps({k: v for k, v in summary.items() if k != "results"}))
        # Non-zero exit when nothing was stored, so a scheduled job shows red.
        raise SystemExit(0 if summary.get("stored") else 1)

    path = Path(
        args.file
        or Path(__file__).resolve().parent.parent / "data" / "competitor_prices_synthetic.csv"
    )
    if not path.exists():
        raise SystemExit(f"Sample file not found: {path}")
    print(f"Replaying {path}")
    summary = store(db, readings_from_sample(path, args.limit))
    print(
        f"accepted={summary['accepted']} duplicates={summary['duplicates']} "
        f"rejected={summary['rejected']}"
    )
    for reason, count in summary["reasons"].items():
        print(f"  rejected {count}x: {reason}")


if __name__ == "__main__":
    main()
