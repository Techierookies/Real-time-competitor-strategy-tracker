"""
Generate a realistic synthetic competitor-pricing panel.

Why this file exists
--------------------
The original dataset drew each price as (per-model mean + large Gaussian
noise). That has no autocorrelation, no trend and no seasonality, so no model
can beat a group average on it -- and indeed none does. Any headline accuracy
figure reported on it is either leakage or luck.

This module replaces that with an explicit, documented price process that
mirrors how smartphone prices actually move in Indian e-commerce:

  price(t) = MSRP
             * depreciation(t)        exponential decay since launch
             * festive_discount(t)    Big Billion Days / Great Indian Festival
             * retailer_effect(t)     persistent spread + undercutting response
             * weekly_effect(t)       mid-week softness, weekend firmness
             * exp(noise(t))          AR(1) noise, not white noise

Every component is a modelling assumption, not a measurement. The data is
clearly labelled synthetic wherever it is used. The point is to exercise and
validate the pipeline end to end with a signal that is genuinely learnable,
so that the reported metrics mean something.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Handset:
    name: str
    msrp: float
    launch: datetime
    # Annual depreciation rate. Newer flagships hold value better early on.
    decay_per_year: float


# Indian launch prices of the tracked variants: 128 GB for the iPhone 15 and
# 16, 256 GB (the base model) for the iPhone 17.
HANDSETS = [
    Handset("iPhone 15", 79_900, datetime(2023, 9, 22), 0.34),
    Handset("iPhone 16", 79_900, datetime(2024, 9, 20), 0.28),
    Handset("iPhone 17", 82_900, datetime(2025, 9, 19), 0.22),
]

RETAILERS = ["Amazon", "Flipkart"]

# (name, start, end, peak depth). Depth is the fraction knocked off at the
# trough of the event; the shape is a smooth cosine bump.
FESTIVE_EVENTS = [
    ("Great Indian Festival", datetime(2025, 9, 27), datetime(2025, 10, 12), 0.17),
    ("Big Billion Days", datetime(2025, 9, 27), datetime(2025, 10, 10), 0.19),
    ("Diwali Sale", datetime(2025, 10, 18), datetime(2025, 10, 26), 0.12),
    ("Black Friday", datetime(2025, 11, 24), datetime(2025, 12, 2), 0.10),
    ("Republic Day Sale", datetime(2026, 1, 17), datetime(2026, 1, 27), 0.13),
    ("Summer Sale", datetime(2026, 5, 2), datetime(2026, 5, 12), 0.08),
]

REVIEW_SNIPPETS = [
    "Battery easily lasts a full day of heavy use.",
    "Camera is a clear step up, low light is much better.",
    "Display is bright and smooth, no complaints.",
    "Good phone but the price is hard to justify.",
    "Charging speed is average compared to rivals.",
    "Build quality feels premium in hand.",
    "Heats up slightly during long gaming sessions.",
    "Switched from Android, setup was painless.",
    "Storage filled up faster than expected.",
    "Great value during the sale, not at full price.",
]


def depreciation(handset: Handset, stamp: datetime) -> float:
    """Exponential decay in value since launch, floored at 55% of MSRP."""
    years = max((stamp - handset.launch).days, 0) / 365.25
    value = float(np.exp(-handset.decay_per_year * years))
    return max(value, 0.55)


def festive_multiplier(stamp: datetime, retailer: str) -> float:
    """Smooth discount bump during sale windows.

    Flipkart runs Big Billion Days, Amazon runs the Great Indian Festival, so
    each retailer only responds to its own events plus the shared ones.
    """
    owned = {
        "Big Billion Days": "Flipkart",
        "Great Indian Festival": "Amazon",
    }
    multiplier = 1.0
    for name, start, end, depth in FESTIVE_EVENTS:
        owner = owned.get(name)
        if owner is not None and owner != retailer:
            continue
        if not (start <= stamp <= end):
            continue
        span = (end - start).total_seconds()
        position = (stamp - start).total_seconds() / span if span else 0.0
        # Cosine bump: zero at the edges, full depth in the middle.
        shape = 0.5 * (1 - np.cos(2 * np.pi * position))
        multiplier *= 1 - depth * shape
    return float(multiplier)


def weekly_multiplier(stamp: datetime) -> float:
    """Small, stable day-of-week pattern. Sellers firm up over weekends."""
    return float(1 + 0.006 * np.cos(2 * np.pi * stamp.weekday() / 7))


def simulate(
    start: datetime,
    end: datetime,
    observations_per_day: int = 2,
    seed: int = 7,
) -> pd.DataFrame:
    """Produce one row per (handset, retailer, observation) over the window."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    identifier = 1

    total_days = (end - start).days

    for handset in HANDSETS:
        # Persistent retailer spread: one shop is structurally a little cheaper.
        spread = {
            "Amazon": float(rng.normal(1.000, 0.004)),
            "Flipkart": float(rng.normal(0.992, 0.004)),
        }
        # AR(1) noise state, one per retailer, so prices are sticky over time.
        noise_state = {name: 0.0 for name in RETAILERS}
        # Rolling memory of the rival's last price, for undercutting behaviour.
        last_price = {name: None for name in RETAILERS}

        for day_offset in range(total_days + 1):
            day = start + timedelta(days=day_offset)
            if day < handset.launch:
                continue

            base = handset.msrp * depreciation(handset, day)

            for retailer in RETAILERS:
                # AR(1): today's shock remembers 88% of yesterday's.
                noise_state[retailer] = (
                    0.88 * noise_state[retailer] + rng.normal(0, 0.012)
                )

                rival = "Flipkart" if retailer == "Amazon" else "Amazon"
                undercut = 1.0
                if last_price[rival] is not None:
                    expected = base * spread[retailer]
                    gap = (last_price[rival] - expected) / expected
                    # Respond to roughly a quarter of the rival's gap, capped.
                    undercut = 1 + float(np.clip(gap * 0.25, -0.05, 0.05))

                price = (
                    base
                    * spread[retailer]
                    * festive_multiplier(day, retailer)
                    * weekly_multiplier(day)
                    * undercut
                    * float(np.exp(noise_state[retailer]))
                )

                # Rare flash sale: a sharp, short-lived markdown.
                if rng.random() < 0.012:
                    price *= float(rng.uniform(0.86, 0.93))

                for _ in range(observations_per_day):
                    hour = int(rng.integers(7, 23))
                    minute = int(rng.integers(0, 60))
                    stamp = day.replace(hour=hour, minute=minute)
                    # Listing-level jitter: different sellers, same product page.
                    observed = price * float(rng.normal(1.0, 0.004))

                    # Rating drifts slowly upward as a model matures.
                    maturity = min((day - handset.launch).days / 365.25, 2.0)
                    rating = float(
                        np.clip(rng.normal(4.15 + 0.12 * maturity, 0.22), 3.3, 5.0)
                    )

                    rows.append(
                        {
                            "ID": identifier,
                            "Model": handset.name,
                            "Source": retailer,
                            "Price": round(observed, 2),
                            "Rating": round(rating, 1),
                            "Reviews": REVIEW_SNIPPETS[
                                int(rng.integers(0, len(REVIEW_SNIPPETS)))
                            ],
                            "URL": (
                                f"https://www.{retailer.lower()}."
                                f"{'in' if retailer == 'Amazon' else 'com'}/"
                                f"{handset.name.lower().replace(' ', '-')}"
                            ),
                            "Scraped_At": stamp.strftime("%Y-%m-%d %H:%M"),
                        }
                    )
                    identifier += 1

                last_price[retailer] = price

    frame = pd.DataFrame(rows)
    return frame.sort_values("Scraped_At").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic price data.")
    parser.add_argument("--out", required=True, help="Destination CSV path.")
    parser.add_argument("--start", default="2025-04-01")
    parser.add_argument("--end", default="2026-11-15")
    parser.add_argument("--per-day", type=int, default=2)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    frame = simulate(
        datetime.fromisoformat(args.start),
        datetime.fromisoformat(args.end),
        observations_per_day=args.per_day,
        seed=args.seed,
    )

    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)

    print(f"Wrote {len(frame):,} rows to {destination}")
    summary = frame.groupby(["Model", "Source"])["Price"].agg(["count", "mean", "std"])
    print(summary.round(0).to_string())


if __name__ == "__main__":
    main()
