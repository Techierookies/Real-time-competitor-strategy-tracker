"""
One live collection run: fetch every target, parse, validate, store, log.

A run never raises because one product failed. Each target gets its own result
row (ok, rejected, blocked, throttled, ...), and the run as a whole is logged,
so `/api/collect/status` can show exactly what happened on every run and a
stale selector or a block is visible within one cycle instead of weeks later
in the training data.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from ml.features import normalise_model, normalise_source

from .fetcher import PoliteFetcher
from .parsers import parse

DEFAULT_TARGETS = Path(__file__).resolve().parent / "targets.json"

MIN_PLAUSIBLE_PRICE = 10_000
MAX_PLAUSIBLE_PRICE = 400_000
# A single-run move larger than this is far more likely a parsing slip (wrong
# variant, EMI amount, exchange-offer price) than a real repricing. Festive
# sales move flagship prices by roughly 10-25%.
MAX_JUMP = 0.40

# Only one run at a time, whether triggered by the scheduler or the API.
_run_lock = threading.Lock()


@dataclass
class Target:
    model: str
    source: str
    url: str
    variant: str = ""
    expect: tuple[str, ...] = ()


def load_targets(path: Path | str | None = None) -> list[Target]:
    data = json.loads(Path(path or DEFAULT_TARGETS).read_text())
    targets = []
    for entry in data.get("targets", []):
        targets.append(
            Target(
                model=normalise_model(entry["model"]),
                source=normalise_source(entry["source"]),
                url=entry["url"],
                variant=entry.get("variant", ""),
                expect=tuple(entry.get("expect", [])),
            )
        )
    return targets


def validate(target: Target, listing, last_price: float | None) -> str | None:
    """Return a rejection reason, or None if the reading can be stored."""
    if listing.price is None:
        return "; ".join(listing.notes) or "no price found"
    if not MIN_PLAUSIBLE_PRICE <= listing.price <= MAX_PLAUSIBLE_PRICE:
        return f"price {listing.price:,.0f} outside plausible band"
    if listing.rating is not None and not 0 <= listing.rating <= 5:
        return f"rating {listing.rating} out of range"
    if listing.title and target.expect:
        title = listing.title.lower()
        missing = [word for word in target.expect if word.lower() not in title]
        if missing:
            return f"page title does not mention {missing}; URL may now point at another product"
    if last_price:
        jump = abs(listing.price - last_price) / last_price
        if jump > MAX_JUMP:
            return f"price moved {jump:.0%} since the last reading; held back as a likely parsing error"
    return None


def collect_once(
    db,
    settings,
    trigger: str = "manual",
    targets: list[Target] | None = None,
    push_to: str | None = None,
    push_token: str | None = None,
    fetcher: PoliteFetcher | None = None,
) -> dict:
    """Run one collection pass. Returns the run summary.

    With `push_to`, readings are sent to a deployed API instead of the local
    database. That is how the GitHub Actions workflow feeds a hosted instance.
    """
    if not _run_lock.acquire(blocking=False):
        return {"status": "skipped", "reason": "a collection run is already in progress"}

    try:
        targets = targets or load_targets(getattr(settings, "targets_file", None))
        fetcher = fetcher or PoliteFetcher(
            user_agent=settings.scrape_user_agent,
            min_delay_seconds=settings.scrape_delay_seconds,
            respect_robots=settings.respect_robots,
        )
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        run_id = db.start_collection_run(trigger, len(targets)) if db else None

        results = []
        for target in targets:
            result = {
                "model": target.model, "source": target.source, "url": target.url,
                "status": None, "http_status": None, "price": None,
                "method": None, "message": "",
            }
            fetched = fetcher.fetch(target.url)
            result["http_status"] = fetched.http_status

            if fetched.status != "ok":
                result["status"], result["message"] = fetched.status, fetched.message
                results.append(result)
                continue

            listing = parse(target.source, fetched.html)
            if listing.blocked:
                fetcher.mark_blocked(target.url)
                result["status"], result["message"] = "blocked", "bot challenge page; backing off until next run"
                results.append(result)
                continue

            last = db.latest_price(target.model, target.source) if db else None
            reason = validate(target, listing, last["price"] if last else None)
            result["method"] = listing.method
            result["price"] = listing.price
            if reason:
                result["status"], result["message"] = "rejected", reason
                results.append(result)
                continue

            observation = {
                "model": target.model,
                "source": target.source,
                "price": listing.price,
                "rating": listing.rating,
                "review_count": listing.review_count,
                "review_text": None,
                "url": target.url,
                "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            if push_to:
                ok, message = push_observation(push_to, push_token, observation)
                result["status"] = "ok" if ok else "push_failed"
                result["message"] = message
            else:
                db.record_observation(observation)
                result["status"] = "ok"
                stock = "" if listing.in_stock is not False else " (listed as out of stock)"
                result["message"] = f"stored via {listing.method}{stock}"
            results.append(result)

        summary = {
            "run_id": run_id,
            "trigger": trigger,
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "targets": len(targets),
            "stored": sum(r["status"] == "ok" for r in results),
            "rejected": sum(r["status"] == "rejected" for r in results),
            "blocked": sum(r["status"] in ("blocked", "throttled", "disallowed") for r in results),
            "errors": sum(r["status"] in ("http_error", "network_error", "push_failed") for r in results),
            "results": results,
        }
        summary["status"] = (
            "ok" if summary["stored"] == len(targets)
            else "partial" if summary["stored"] > 0
            else "failed"
        )
        if db:
            db.finish_collection_run(run_id, summary)
        return summary
    finally:
        _run_lock.release()


def push_observation(api_url: str, token: str | None, observation: dict) -> tuple[bool, str]:
    try:
        response = requests.post(
            api_url.rstrip("/") + "/api/collect/ingest",
            json={"observations": [observation]},
            headers={"X-Collector-Token": token or ""},
            timeout=20,
        )
        if response.status_code == 200:
            return True, "pushed to API"
        return False, f"API answered HTTP {response.status_code}: {response.text[:200]}"
    except requests.RequestException as error:
        return False, f"could not reach API: {error}"
