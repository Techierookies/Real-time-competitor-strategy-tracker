"""Feature engineering and pricing logic."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from ml.features import (
    add_horizon_target,
    build_features,
    normalise_model,
    normalise_source,
    to_daily_panel,
)
from ml.pricing import detect_price_anomalies, recommend_price


def make_history(days: int = 90) -> pd.DataFrame:
    start = datetime(2026, 1, 1)
    rows = []
    for day in range(days):
        rows.append(
            {
                "Model": "iPhone 17",
                "Source": "Amazon",
                "Price": 90_000 - day * 20,
                "Rating": 4.4,
                "Reviews": "Good phone.",
                "Scraped_At": start + timedelta(days=day),
            }
        )
    return pd.DataFrame(rows)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("amazon.in", "Amazon"),
        ("AMAZON", "Amazon"),
        ("www.flipkart.com", "Flipkart"),
        ("Flipkart", "Flipkart"),
    ],
)
def test_source_normalisation(raw, expected):
    """The exact defect that silently broke live prices in the old code."""
    assert normalise_source(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [("iphone15", "iPhone 15"), ("iPhone-16", "iPhone 16"), ("IPHONE 17", "iPhone 17")],
)
def test_model_normalisation(raw, expected):
    assert normalise_model(raw) == expected


def test_lag_features_never_see_the_present():
    """The core anti-leakage guarantee: lag_price_1 is the previous price."""
    history = make_history()
    featured = build_features(to_daily_panel(history))
    row = featured.iloc[5]
    previous = featured.iloc[4]
    assert row["lag_price_1"] == pytest.approx(previous["Price"])
    assert row["lag_price_1"] != pytest.approx(row["Price"])


def test_first_observation_has_no_lag():
    featured = build_features(to_daily_panel(make_history()))
    assert np.isnan(featured.iloc[0]["lag_price_1"])


def test_rolling_means_exclude_the_current_row():
    featured = build_features(to_daily_panel(make_history()))
    row = featured.iloc[10]
    window = featured["Price"].iloc[3:10]
    assert row["roll_mean_7"] == pytest.approx(window.mean())


def test_horizon_target_is_the_future_price():
    featured = build_features(to_daily_panel(make_history()))
    dataset = add_horizon_target(featured, 7)
    first = dataset.iloc[0]
    assert first["target"] == pytest.approx(featured.iloc[7]["Price"])


def test_horizon_target_drops_rows_without_a_future():
    featured = build_features(to_daily_panel(make_history(50)))
    assert len(add_horizon_target(featured, 14)) == len(featured) - 14


def test_target_calendar_features_describe_the_target_date():
    featured = build_features(to_daily_panel(make_history()))
    dataset = add_horizon_target(featured, 30)
    origin = pd.Timestamp(dataset.iloc[0]["Scraped_At"])
    assert dataset.iloc[0]["target_month"] == (origin + pd.Timedelta(days=30)).month


def test_daily_panel_collapses_duplicate_days():
    history = make_history(10)
    doubled = pd.concat([history, history], ignore_index=True)
    assert len(to_daily_panel(doubled)) == 10


def test_recommendation_is_deterministic():
    """Unlike asking a language model, the same input gives the same price."""
    kwargs = dict(
        model="iPhone 17", source="Amazon", current_price=90_000,
        forecast_price=88_000, competitor_price=86_000, unit_cost=70_000,
    )
    assert recommend_price(**kwargs) == recommend_price(**kwargs)


def test_recommendation_only_partly_closes_a_competitor_gap():
    result = recommend_price(
        "iPhone 17", "Amazon", 90_000, 88_000, competitor_price=80_000
    )
    assert 80_000 < result.recommended_price < 88_000


def test_recommendation_never_breaches_the_margin_floor():
    result = recommend_price(
        "iPhone 17", "Amazon", 90_000, 60_000, unit_cost=70_000, min_margin=0.10,
        max_move_pct=0.9,
    )
    assert result.recommended_price >= 70_000 * 1.10 - 1
    assert "margin_floor" in result.constraints_applied


def test_recommendation_explains_itself():
    result = recommend_price("iPhone 17", "Amazon", 90_000, 88_000)
    assert len(result.rationale) >= 2


def test_anomaly_detector_separates_bad_scrapes_from_real_moves():
    history = make_history(60)
    history.loc[30, "Price"] = 5_000  # a parsing failure, not a sale
    events = detect_price_anomalies(history)
    kinds = {event["event_type"] for event in events}
    assert "suspected_scrape_error" in kinds


def test_anomaly_detector_stays_quiet_on_a_calm_series():
    assert detect_price_anomalies(make_history(60)) == []
