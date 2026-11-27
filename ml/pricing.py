"""
Price recommendation and anomaly detection.

Why this replaces the previous approach
---------------------------------------
The original "optimal price" was produced by asking a language model to reply
with a single number. That is not a pricing strategy: it is unreproducible, it
cannot be back-tested, it changes between identical calls, and it cannot
explain itself to the person who has to sign off on a repricing decision.

This module computes the recommendation arithmetically from the forecast, a
stated margin floor and a stated demand elasticity. Every number it returns is
reproducible and every one comes with the reasoning that produced it. The
language model's job is moved to where language models are actually good:
writing the human-readable summary of a decision that has already been made.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

# Smartphone demand is elastic: buyers comparison-shop hard on a commodity
# flagship. A price elasticity of -1.8 means a 10% price cut lifts units by
# about 18%. Override per category once real conversion data exists.
DEFAULT_ELASTICITY = -1.8

# Never recommend a price below this multiple of unit cost.
DEFAULT_MIN_MARGIN = 0.08


@dataclass
class PriceRecommendation:
    model: str
    source: str
    current_price: float
    competitor_price: float | None
    forecast_price: float
    recommended_price: float
    change_from_current_pct: float
    expected_margin_pct: float | None
    expected_demand_index: float
    rationale: list[str] = field(default_factory=list)
    constraints_applied: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def recommend_price(
    model: str,
    source: str,
    current_price: float,
    forecast_price: float,
    competitor_price: float | None = None,
    unit_cost: float | None = None,
    elasticity: float = DEFAULT_ELASTICITY,
    min_margin: float = DEFAULT_MIN_MARGIN,
    max_move_pct: float = 0.08,
) -> PriceRecommendation:
    """Recommend a listing price, showing the work.

    The logic, in order:
      1. Start from where the market is forecast to be. Pricing to today's
         market means always reacting a step late.
      2. If a competitor is cheaper, shade toward them, but only partway: a
         full match starts a price war and gives away margin unnecessarily.
      3. Apply the margin floor. This is a hard constraint, not a preference.
      4. Cap the size of any single move, because large jumps erode buyer
         trust and trip marketplace repricing penalties.
    """
    rationale: list[str] = []
    constraints: list[str] = []

    target = float(forecast_price)
    rationale.append(
        f"Anchored on the {source} forecast of Rs {target:,.0f} rather than "
        f"today's Rs {current_price:,.0f}, so the price leads the market "
        f"instead of trailing it."
    )

    if competitor_price is not None and competitor_price > 0:
        if competitor_price < target:
            # Close half the gap. Enough to stay visible in a sorted listing,
            # not so much that it invites a matching cut.
            adjusted = target - 0.5 * (target - competitor_price)
            rationale.append(
                f"Rival listed at Rs {competitor_price:,.0f}, below the "
                f"forecast. Closing half the gap to Rs {adjusted:,.0f} keeps "
                f"the listing competitive without fully conceding margin."
            )
            target = adjusted
        else:
            rationale.append(
                f"Rival listed at Rs {competitor_price:,.0f}, at or above the "
                f"forecast, so there is no need to discount below it."
            )

    expected_margin = None
    if unit_cost is not None and unit_cost > 0:
        floor = unit_cost * (1 + min_margin)
        if target < floor:
            rationale.append(
                f"Forecast-led price fell below the margin floor of "
                f"Rs {floor:,.0f} ({min_margin:.0%} over unit cost)."
            )
            target = floor
            constraints.append("margin_floor")
        expected_margin = (target - unit_cost) / target

    # Cap the move size relative to where the price sits today.
    ceiling = current_price * (1 + max_move_pct)
    floor_move = current_price * (1 - max_move_pct)
    if target > ceiling:
        target = ceiling
        constraints.append("max_increase_cap")
        rationale.append(
            f"Increase capped at {max_move_pct:.0%} of the current price."
        )
    elif target < floor_move:
        target = floor_move
        constraints.append("max_decrease_cap")
        rationale.append(
            f"Decrease capped at {max_move_pct:.0%} of the current price."
        )

    # Constant-elasticity demand index, normalised so today's price scores 1.0.
    demand_index = float((target / current_price) ** elasticity)
    direction = "lift" if demand_index > 1 else "reduce"
    rationale.append(
        f"At elasticity {elasticity}, this should {direction} unit demand to "
        f"{demand_index:.2f}x today's level."
    )

    return PriceRecommendation(
        model=model,
        source=source,
        current_price=round(float(current_price), 2),
        competitor_price=(
            round(float(competitor_price), 2) if competitor_price else None
        ),
        forecast_price=round(float(forecast_price), 2),
        recommended_price=round(float(target), 2),
        change_from_current_pct=round((target / current_price - 1) * 100, 2),
        expected_margin_pct=(
            round(expected_margin * 100, 2) if expected_margin is not None else None
        ),
        expected_demand_index=round(demand_index, 3),
        rationale=rationale,
        constraints_applied=constraints,
    )


def detect_price_anomalies(
    history: pd.DataFrame, window: int = 14, z_threshold: float = 3.0
) -> list[dict]:
    """Flag price moves that are large relative to the series' own volatility.

    Uses a robust z-score built from the median and the median absolute
    deviation, so a single bad scrape cannot inflate the threshold and hide
    the very anomalies this is meant to catch.

    Two kinds of event matter to the product and they are labelled
    differently: a genuine competitor price move, and a scraping defect that
    only looks like one.
    """
    history = history.sort_values("Scraped_At").copy()
    history["Price"] = pd.to_numeric(history["Price"], errors="coerce")
    history = history.dropna(subset=["Price"])

    if len(history) < max(window, 5):
        return []

    returns = history["Price"].pct_change()
    median = returns.rolling(window, min_periods=5).median()
    deviation = (returns - median).abs().rolling(window, min_periods=5).median()
    # 1.4826 rescales MAD to be comparable with a standard deviation.
    scale = (deviation * 1.4826).replace(0, np.nan)
    z_scores = (returns - median) / scale

    events = []
    for index, z_score in z_scores.items():
        if pd.isna(z_score) or abs(z_score) < z_threshold:
            continue
        row = history.loc[index]
        change = float(returns.loc[index])

        # A move beyond 40% in a single step is almost always a parsing
        # failure rather than a real price. Flagging it as a data-quality
        # issue stops a bad scrape from triggering a real repricing decision.
        if abs(change) > 0.40:
            kind, severity = "suspected_scrape_error", "data_quality"
        elif change < 0:
            kind, severity = "price_drop", "high" if change < -0.10 else "medium"
        else:
            kind, severity = "price_increase", "high" if change > 0.10 else "medium"

        events.append(
            {
                "timestamp": str(row["Scraped_At"]),
                "model": row.get("Model"),
                "source": row.get("Source"),
                "price": round(float(row["Price"]), 2),
                "change_pct": round(change * 100, 2),
                "robust_z_score": round(float(z_score), 2),
                "event_type": kind,
                "severity": severity,
            }
        )

    return events
