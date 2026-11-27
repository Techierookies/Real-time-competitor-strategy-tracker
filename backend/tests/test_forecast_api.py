"""Forecasting, pricing and alert endpoints."""

from __future__ import annotations


def test_health_is_cheap_and_always_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_reports_component_checks(client):
    body = client.get("/ready").json()
    assert "database" in body["checks"]
    assert "model_artifacts" in body["checks"]


def test_forecast_404_for_unknown_series(client):
    response = client.post(
        "/api/forecast",
        json={"model": "iPhone 16", "source": "Amazon", "horizon_days": 14},
    )
    assert response.status_code == 404


def test_forecast_refuses_thin_history(client, seeded):
    """A series with too few points must fail loudly, not guess."""
    from app.config import get_settings
    from app.db import Database

    db = Database(get_settings().sqlite_path)
    db.record_observation(
        {
            "model": "iPhone 15", "source": "Amazon", "price": 50000.0,
            "rating": 4.0, "review_count": 1, "review_text": "",
            "url": None, "observed_at": "2026-02-01T10:00:00",
        }
    )
    response = client.post(
        "/api/forecast", json={"model": "iPhone 15", "source": "Amazon"}
    )
    assert response.status_code == 422


def test_forecast_returns_ordered_interval(client, seeded):
    response = client.post(
        "/api/forecast",
        json={"model": "iPhone 17", "source": "Amazon", "horizon_days": 14},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["lower_price"] <= body["predicted_price"] <= body["upper_price"]
    assert body["anchor_price"] > 0
    assert body["confidence_level"] == 0.80


def test_forecast_is_persisted_for_later_scoring(client, seeded):
    client.post(
        "/api/forecast",
        json={"model": "iPhone 17", "source": "Amazon", "horizon_days": 7},
    )
    with seeded.connect() as connection:
        count = connection.execute("SELECT COUNT(*) AS n FROM forecasts").fetchone()
    assert count["n"] == 1


def test_horizon_is_validated(client, seeded):
    assert (
        client.post(
            "/api/forecast",
            json={"model": "iPhone 17", "source": "Amazon", "horizon_days": 9999},
        ).status_code
        == 422
    )


def test_source_aliases_resolve(client, seeded):
    """'amazon.in' is the label the old scraper wrote; it must still resolve."""
    response = client.post(
        "/api/forecast", json={"model": "iphone17", "source": "amazon.in"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "Amazon"


def test_compare_names_the_cheaper_retailer(client, seeded):
    body = client.get("/api/compare/iPhone 17?horizon_days=14").json()
    assert set(body["forecasts"]) == {"Amazon", "Flipkart"}
    assert body["cheapest_forecast"] in {"Amazon", "Flipkart"}


def test_pricing_respects_margin_floor(client, seeded):
    body = client.post(
        "/api/pricing/recommend",
        json={
            "model": "iPhone 17",
            "source": "Amazon",
            "unit_cost": 95_000,
            "min_margin": 0.10,
        },
    ).json()
    recommendation = body["recommendation"]
    # Cost is above market here, so the floor must bind and be reported.
    assert "margin_floor" in recommendation["constraints_applied"]
    assert recommendation["rationale"]


def test_pricing_caps_move_size(client, seeded):
    body = client.post(
        "/api/pricing/recommend",
        json={"model": "iPhone 17", "source": "Amazon", "max_move_pct": 0.01},
    ).json()["recommendation"]
    assert abs(body["change_from_current_pct"]) <= 1.01


def test_model_card_reports_baseline_comparison(client):
    body = client.get("/api/model-card").json()
    assert "horizons" in body
    for report in body["horizons"].values():
        assert "beats_naive_baseline" in report


def test_alert_scan_groups_by_model_and_source(client, seeded, admin_token):
    from app.config import get_settings
    from app.db import Database

    db = Database(get_settings().sqlite_path)
    db.record_observation(
        {
            "model": "iPhone 17", "source": "Amazon", "price": 70_000.0,
            "rating": 4.4, "review_count": 1, "review_text": "",
            "url": None, "observed_at": "2026-06-01T10:00:00",
        }
    )
    body = client.post(
        "/api/alerts/scan", headers={"Authorization": f"Bearer {admin_token}"}
    ).json()
    assert body["alerts_created"] >= 1
    assert all(alert["source"] in {"Amazon", "Flipkart"} for alert in body["alerts"])


def test_duplicate_observations_are_ignored(client, seeded):
    row = {
        "model": "iPhone 17", "source": "Amazon", "price": 88_000.0,
        "rating": 4.4, "review_count": 1, "review_text": "",
        "url": None, "observed_at": "2026-07-01T10:00:00",
    }
    assert seeded.record_observation(row) is True
    assert seeded.record_observation(row) is False


def test_assistant_is_grounded_in_stored_data(client, seeded):
    body = client.post(
        "/api/assistant", json={"message": "iPhone 17 on Amazon next month"}
    ).json()
    assert body["grounded"] is True
    assert body["data"]["horizon_days"] == 30
    assert "Amazon" in body["data"]["forecasts"]


def test_assistant_asks_for_a_model_when_none_given(client):
    body = client.post("/api/assistant", json={"message": "what is the price"}).json()
    assert body["data"] is None
