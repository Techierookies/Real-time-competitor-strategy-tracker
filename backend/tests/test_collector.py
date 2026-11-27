"""Scraper parsing, validation, run logging and the live-data endpoints.

All tests run against saved pages and a fake fetcher, so they never touch the
network. They pin down behaviour (what gets stored, what gets rejected, what
counts as a block), not the exact markup of today's retailer pages.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from collector.fetcher import FetchResult
from collector.live import Target, collect_once, validate
from collector.parsers import ParsedListing, looks_blocked, parse, to_number

FIXTURES = Path(__file__).parent / "fixtures"


def page(name: str) -> str:
    return (FIXTURES / name).read_text()


# ---- Parsing -------------------------------------------------------------------

def test_amazon_reads_the_price_to_pay_not_the_emi_or_mrp():
    listing = parse("Amazon", page("amazon_product.html"))
    assert listing.price == 69_900
    assert listing.mrp == 79_900
    assert listing.method.startswith("css:")
    assert listing.rating == 4.5
    assert listing.review_count == 2341
    assert listing.in_stock is True
    assert "iPhone 16" in listing.title


def test_flipkart_prefers_structured_data():
    listing = parse("Flipkart", page("flipkart_product.html"))
    assert listing.price == 68_999
    assert listing.method == "json-ld"
    assert listing.rating == 4.6
    assert listing.review_count == 1890
    assert listing.in_stock is True


def test_flipkart_falls_back_to_selectors_and_ignores_offer_text():
    listing = parse("Flipkart", page("flipkart_css_only.html"))
    assert listing.price == 52_499
    assert listing.method == "css:div.Nx9bqj.CxhGGd"
    assert listing.review_count == 14_211


def test_challenge_page_is_reported_as_blocked_not_parsed():
    listing = parse("Amazon", page("amazon_captcha.html"))
    assert listing.blocked is True
    assert listing.price is None
    assert looks_blocked(page("amazon_captcha.html"))


def test_no_price_means_no_guess():
    """The old scraper grabbed the first rupee figure on the page here."""
    listing = parse("Amazon", page("no_price.html"))
    assert listing.price is None
    assert listing.in_stock is False


@pytest.mark.parametrize("text,value", [("₹69,900.00", 69900.0), ("1,23,456", 123456.0), ("abc", None)])
def test_number_parsing(text, value):
    assert to_number(text) == value


# ---- Validation ----------------------------------------------------------------

TARGET = Target("iPhone 16", "Amazon", "https://example.org/p", "128 GB", ("iPhone 16", "128"))


def test_validate_accepts_a_sane_reading():
    listing = ParsedListing(price=69_900, title="Apple iPhone 16 (128 GB) - Black")
    assert validate(TARGET, listing, last_price=70_500) is None


def test_validate_rejects_a_wrong_product_page():
    listing = ParsedListing(price=69_900, title="Apple iPhone 16 Pro (256 GB)")
    assert "does not mention" in validate(TARGET, listing, None)


def test_validate_holds_back_implausible_jumps():
    listing = ParsedListing(price=35_000, title="Apple iPhone 16 (128 GB)")
    assert "moved" in validate(TARGET, listing, last_price=70_000)


def test_validate_rejects_out_of_band_prices():
    listing = ParsedListing(price=3_389, title="Apple iPhone 16 (128 GB)")
    assert "plausible band" in validate(TARGET, listing, None)


# ---- A full run, with a fake fetcher ------------------------------------------------

class FakeFetcher:
    """Serves saved pages by URL; records nothing, fetches nothing."""

    def __init__(self, pages: dict[str, FetchResult]):
        self.pages = pages
        self.blocked = []

    def fetch(self, url):
        return self.pages[url]

    def mark_blocked(self, url):
        self.blocked.append(url)


def fake_targets():
    return [
        Target("iPhone 16", "Amazon", "https://amz/16", "128 GB", ("iPhone 16", "128")),
        Target("iPhone 16", "Flipkart", "https://fk/16", "128 GB", ("iPhone 16", "128")),
        Target("iPhone 15", "Flipkart", "https://fk/15", "128 GB", ("iPhone 15", "128")),
        Target("iPhone 17", "Amazon", "https://amz/17", "256 GB", ("iPhone 17", "256")),
        Target("iPhone 17", "Flipkart", "https://fk/17", "256 GB", ("iPhone 17", "256")),
    ]


def fake_fetcher():
    return FakeFetcher({
        "https://amz/16": FetchResult("https://amz/16", "ok", 200, page("amazon_product.html")),
        "https://fk/16": FetchResult("https://fk/16", "ok", 200, page("flipkart_product.html")),
        "https://fk/15": FetchResult("https://fk/15", "ok", 200, page("flipkart_css_only.html")),
        "https://amz/17": FetchResult("https://amz/17", "ok", 200, page("amazon_captcha.html")),
        "https://fk/17": FetchResult("https://fk/17", "throttled", 429, message="HTTP 429"),
    })


def settings_stub():
    return SimpleNamespace(scrape_user_agent="test", scrape_delay_seconds=0,
                           respect_robots=False, targets_file=None)


def test_collect_once_stores_good_readings_and_logs_every_target(client):
    from app.config import get_settings
    from app.db import Database

    db = Database(get_settings().sqlite_path)
    summary = collect_once(db, settings_stub(), trigger="test",
                           targets=fake_targets(), fetcher=fake_fetcher())

    assert summary["stored"] == 3
    assert summary["blocked"] == 2
    assert summary["status"] == "partial"

    latest = {(p["model"], p["source"]): p["price"] for p in db.latest_prices()}
    assert latest[("iPhone 16", "Amazon")] == 69_900
    assert latest[("iPhone 16", "Flipkart")] == 68_999
    assert ("iPhone 17", "Amazon") not in latest

    results = db.run_results(summary["run_id"])
    assert {r["status"] for r in results} == {"ok", "blocked", "throttled"}


def test_status_endpoint_reports_the_last_run(client):
    from app.config import get_settings
    from app.db import Database

    db = Database(get_settings().sqlite_path)
    collect_once(db, settings_stub(), trigger="test", targets=fake_targets(), fetcher=fake_fetcher())

    body = client.get("/api/collect/status").json()
    assert body["latest_run"]["stored"] == 3
    assert len(body["latest_run_results"]) == 5

    prices = client.get("/api/prices/latest").json()["prices"]
    assert any(p["model"] == "iPhone 16" and p["source"] == "Amazon" for p in prices)


def test_manual_run_requires_admin(client):
    assert client.post("/api/collect/run").status_code == 401


def test_manual_run_executes_through_the_api(client, admin_token, monkeypatch):
    import collector.live as live_module

    monkeypatch.setattr(live_module, "load_targets", lambda path=None: fake_targets())
    monkeypatch.setattr(live_module, "PoliteFetcher", lambda **kwargs: fake_fetcher())

    body = client.post(
        "/api/collect/run?wait=true", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert body["stored"] == 3


# ---- Ingestion from an external collector --------------------------------------------

READING = {"model": "iPhone 16", "source": "amazon.in", "price": 69_900,
           "observed_at": "2026-11-20T09:00:00"}


def test_ingest_disabled_without_a_token(client):
    response = client.post("/api/collect/ingest", json={"observations": [READING]})
    assert response.status_code == 404


def test_ingest_checks_the_token(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "collector_token", "x" * 32)
    bad = client.post("/api/collect/ingest", json={"observations": [READING]},
                      headers={"X-Collector-Token": "wrong"})
    assert bad.status_code == 401

    good = client.post("/api/collect/ingest", json={"observations": [READING]},
                       headers={"X-Collector-Token": "x" * 32})
    assert good.status_code == 200
    assert good.json()["stored"] == 1

    again = client.post("/api/collect/ingest", json={"observations": [READING]},
                        headers={"X-Collector-Token": "x" * 32})
    assert again.json()["duplicates"] == 1


def test_price_history_endpoint(client, seeded):
    body = client.get("/api/prices/history/iPhone 17/Amazon?days=30").json()
    assert len(body["points"]) == 30
    assert all(point["price"] > 0 for point in body["points"])


def test_reviews_endpoint_returns_stored_snippets(client, seeded):
    body = client.get("/api/reviews/iphone17?limit=5").json()
    assert body["model"] == "iPhone 17"
    assert len(body["reviews"]) == 5
    assert body["reviews"][0]["review"] == "Solid phone."


def test_model_card_names_its_training_data(client):
    assert client.get("/api/model-card").json()["data_source"] in {"synthetic", "live", "file"}
