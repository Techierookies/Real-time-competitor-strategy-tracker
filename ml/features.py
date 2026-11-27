"""
Leak-free feature engineering for competitor price modelling.

Design rule enforced throughout this module:
    every feature for a row at time t is computed using ONLY rows strictly
    before t within the same (Model, Source) series.

The previous implementation computed Model_Price_mean / std / min / max /
median over the *entire* dataframe, including the rows that later ended up in
the test split. That inflates offline scores and cannot be reproduced at
serving time, because at serving time the future does not exist yet.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RAW_COLUMNS = ["Model", "Source", "Price", "Rating", "Reviews", "Scraped_At"]

# Features that depend only on the row itself (always safe).
STATIC_FEATURES = [
    "model_code",
    "source_code",
    "rating",
    "review_len",
    "review_words",
    "month",
    "day_of_week",
    "day_of_year",
    "hour",
    "is_weekend",
    "is_launch_season",
    "is_holiday_season",
    "days_since_series_start",
]

# Features derived from the past of the same series (safe because shifted).
LAG_FEATURES = [
    "lag_price_1",
    "lag_price_2",
    "roll_mean_3",
    "roll_mean_7",
    "roll_std_7",
    "roll_mean_30",
    "expanding_mean",
    "expanding_std",
    "momentum_1",
    "momentum_7",
    "days_since_prev_obs",
    "obs_index",
]

# Features expressed relative to today's known price (the "anchor").
#
# Gradient-boosted trees cannot extrapolate: they can only predict values they
# saw during training. A handset's price trends steadily downward, so a model
# asked for an absolute rupee figure a month out is being asked for a number
# below anything in its training set, and it will systematically overshoot.
# Anchoring every feature (and the target) to today's price turns the problem
# into "how far will this move, in percent", which is stationary and learnable.
RELATIVE_FEATURES = [
    "rel_lag_1",
    "rel_roll_mean_7",
    "rel_roll_mean_30",
    "rel_expanding_mean",
    "rel_roll_max_30",
    "rel_roll_min_30",
    "volatility_7",
    "volatility_30",
    "drawdown_from_30d_high",
    "trend_7",
    "trend_30",
]

# Known-future covariates: facts about the date being forecast that are already
# certain today. A forecast made on 1 October for 20 October must know that the
# 20th falls inside Diwali week -- otherwise the model is guessing at a
# discount that is published weeks in advance. Indexing calendar features at
# the target date rather than the origin date is the single biggest accuracy
# win in this pipeline.
HORIZON_FEATURES = [
    "horizon_days",
    "target_month",
    "target_day_of_week",
    "target_day_of_year",
    "target_is_launch_season",
    "target_is_holiday_season",
    "target_in_sale_window",
    "target_sale_depth",
    "days_to_next_sale",
    "days_since_last_sale",
    "sale_state_change",
]

# Published Indian e-commerce sale windows, as (start, end, typical depth).
# These are announced well ahead of time, so they are legitimately knowable at
# forecast time. Extend this list as the business calendar is confirmed.
SALE_CALENDAR = [
    ("2025-09-27", "2025-10-12", 0.18),
    ("2025-10-18", "2025-10-26", 0.12),
    ("2025-11-24", "2025-12-02", 0.10),
    ("2026-01-17", "2026-01-27", 0.13),
    ("2026-05-02", "2026-05-12", 0.08),
    ("2026-09-26", "2026-10-11", 0.18),
    ("2026-10-25", "2026-11-02", 0.12),
]

FEATURE_COLUMNS = (
    STATIC_FEATURES + LAG_FEATURES + RELATIVE_FEATURES + HORIZON_FEATURES
)

MODEL_CODES = {"iPhone 15": 0, "iPhone 16": 1, "iPhone 17": 2}
SOURCE_CODES = {"Amazon": 0, "Flipkart": 1}


def normalise_source(value: str) -> str:
    """Map every spelling of a retailer onto one canonical label.

    This is the fix for the defect that silently broke the live-price lookup:
    the scraper wrote 'amazon.in' / 'flipkart.com' into the database while the
    prediction layer filtered on 'Amazon' / 'Flipkart', so the filter matched
    zero rows and the 'current market price' fell back to the model's own
    prediction on every single request.
    """
    if value is None:
        return "Unknown"
    text = str(value).strip().lower()
    if "amazon" in text:
        return "Amazon"
    if "flipkart" in text:
        return "Flipkart"
    return str(value).strip().title()


def normalise_model(value: str) -> str:
    """Map free-text model names onto canonical 'iPhone NN' labels."""
    if value is None:
        return "Unknown"
    text = str(value).strip().lower().replace("-", " ")
    for number in ("17", "16", "15"):
        if number in text:
            return f"iPhone {number}"
    return str(value).strip()


def load_frame(csv_path: str) -> pd.DataFrame:
    """Read the training CSV and return a clean, canonical, sorted frame."""
    frame = pd.read_csv(csv_path)
    return clean_frame(frame)


def clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Canonicalise labels, coerce types, drop unusable rows, sort by time."""
    frame = frame.copy()

    if "Reviews" not in frame.columns:
        frame["Reviews"] = ""
    if "Rating" not in frame.columns:
        frame["Rating"] = np.nan

    frame["Model"] = frame["Model"].map(normalise_model)
    frame["Source"] = frame["Source"].map(normalise_source)
    frame["Price"] = pd.to_numeric(frame["Price"], errors="coerce")
    frame["Rating"] = pd.to_numeric(frame["Rating"], errors="coerce")
    frame["Scraped_At"] = pd.to_datetime(
        frame["Scraped_At"], format="mixed", errors="coerce"
    )

    frame = frame.dropna(subset=["Price", "Scraped_At"])
    frame = frame[frame["Price"] > 0]

    # Rating is missing often enough that dropping rows would be wasteful.
    # Fill with the per-model median and flag nothing: rating carries little
    # signal here, and an explicit median is more honest than a magic 4.2.
    frame["Rating"] = frame.groupby("Model")["Rating"].transform(
        lambda column: column.fillna(column.median())
    )
    frame["Rating"] = frame["Rating"].fillna(frame["Rating"].median())
    frame["Reviews"] = frame["Reviews"].fillna("").astype(str)

    frame = frame.sort_values("Scraped_At").reset_index(drop=True)
    return frame


def to_daily_panel(frame: pd.DataFrame) -> pd.DataFrame:
    """Collapse raw scrapes into one row per (Model, Source, calendar day).

    Scrapes arrive at irregular times and sometimes several per day. Modelling
    on the raw stream makes 'predict the next row' almost the same question as
    'repeat the previous row', which flatters the model. A daily panel states
    the forecasting problem the product actually needs to solve.

    The daily price is the median of that day's observations, which shrugs off
    the occasional mis-parsed listing without dropping the day entirely.
    """
    frame = frame.copy()
    frame["day"] = frame["Scraped_At"].dt.normalize()

    panel = (
        frame.groupby(["Model", "Source", "day"])
        .agg(
            Price=("Price", "median"),
            Rating=("Rating", "mean"),
            observations=("Price", "size"),
            Reviews=("Reviews", "first"),
        )
        .reset_index()
        .rename(columns={"day": "Scraped_At"})
    )

    # Reindex each series onto a continuous daily calendar so that gaps are
    # explicit. Missing days are forward-filled, which is what a trader would
    # assume: the last listed price stands until a new one is observed.
    filled = []
    for (model_name, source), block in panel.groupby(["Model", "Source"]):
        block = block.set_index("Scraped_At").sort_index()
        calendar = pd.date_range(block.index.min(), block.index.max(), freq="D")
        block = block.reindex(calendar)
        block["Model"] = model_name
        block["Source"] = source
        block["observations"] = block["observations"].fillna(0).astype(int)
        block["Price"] = block["Price"].ffill()
        block["Rating"] = block["Rating"].ffill()
        block["Reviews"] = block["Reviews"].ffill().fillna("")
        filled.append(block.rename_axis("Scraped_At").reset_index())

    out = pd.concat(filled, ignore_index=True)
    out = out.dropna(subset=["Price"])
    return out.sort_values("Scraped_At").reset_index(drop=True)


def _sale_windows() -> list[tuple[pd.Timestamp, pd.Timestamp, float]]:
    return [
        (pd.Timestamp(start), pd.Timestamp(end), depth)
        for start, end, depth in SALE_CALENDAR
    ]


def add_target_calendar_features(
    featured: pd.DataFrame, horizon_days: int
) -> pd.DataFrame:
    """Describe the date being forecast, not the date the forecast is made.

    Everything here is knowable at forecast time: calendar arithmetic and a
    published sale schedule. Nothing reads the future price.
    """
    featured = featured.copy()
    origin = featured["Scraped_At"]
    target_date = origin + pd.Timedelta(days=horizon_days)

    featured["horizon_days"] = horizon_days
    featured["target_month"] = target_date.dt.month
    featured["target_day_of_week"] = target_date.dt.dayofweek
    featured["target_day_of_year"] = target_date.dt.dayofyear
    featured["target_is_launch_season"] = target_date.dt.month.isin([9, 10]).astype(int)
    featured["target_is_holiday_season"] = (
        target_date.dt.month.isin([11, 12]).astype(int)
    )

    windows = _sale_windows()

    def describe(stamp: pd.Timestamp) -> tuple[int, float, float, float]:
        inside, depth = 0, 0.0
        for start, end, window_depth in windows:
            if start <= stamp <= end:
                inside, depth = 1, window_depth
                break
        upcoming = [(start - stamp).days for start, _, _ in windows if start > stamp]
        past = [(stamp - end).days for _, end, _ in windows if end < stamp]
        return (
            inside,
            depth,
            float(min(upcoming)) if upcoming else 365.0,
            float(min(past)) if past else 365.0,
        )

    described = [describe(stamp) for stamp in target_date]
    featured["target_in_sale_window"] = [row[0] for row in described]
    featured["target_sale_depth"] = [row[1] for row in described]
    featured["days_to_next_sale"] = [row[2] for row in described]
    featured["days_since_last_sale"] = [row[3] for row in described]

    # Whether the forecast crosses into or out of a sale. This is what makes a
    # price move, far more than simply sitting inside a sale window.
    origin_inside = [describe(stamp)[0] for stamp in origin]
    featured["sale_state_change"] = (
        featured["target_in_sale_window"].to_numpy() - np.array(origin_inside)
    )
    return featured


def add_horizon_target(featured: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
    """Attach the price this series printed `horizon_days` later.

    Rows near the end of each series have no future to compare against and are
    dropped, rather than being filled with a guess.
    """
    featured = featured.sort_values("Scraped_At").copy()
    featured["target"] = featured.groupby(["Model", "Source"])["Price"].shift(
        -horizon_days
    )
    featured["horizon_days"] = horizon_days
    featured = featured.dropna(subset=["target"])
    featured = add_target_calendar_features(featured, horizon_days)

    # The model is trained on this, not on `target`. Working in log-ratio space
    # makes the target roughly stationary and symmetric: a 10% rise and a 10%
    # fall become equal and opposite, which an L1 objective handles cleanly.
    featured["target_log_ratio"] = np.log(
        featured["target"] / featured["Price"].replace(0, np.nan)
    )
    featured = featured.replace([np.inf, -np.inf], np.nan)
    featured = featured.dropna(subset=["target_log_ratio"])
    return featured.reset_index(drop=True)


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the full feature matrix plus Price, Scraped_At, Model, Source.

    Lag and rolling columns are computed per (Model, Source) series and shifted
    by one observation, so no row can ever see its own price or any later one.
    """
    frame = frame.sort_values("Scraped_At").reset_index(drop=True)
    out = pd.DataFrame(index=frame.index)

    out["model_code"] = frame["Model"].map(MODEL_CODES).fillna(-1).astype(int)
    out["source_code"] = frame["Source"].map(SOURCE_CODES).fillna(-1).astype(int)
    out["rating"] = frame["Rating"].astype(float)

    reviews = frame["Reviews"].astype(str)
    out["review_len"] = reviews.str.len()
    out["review_words"] = reviews.str.split().str.len().fillna(0)

    stamp = frame["Scraped_At"]
    out["month"] = stamp.dt.month
    out["day_of_week"] = stamp.dt.dayofweek
    out["day_of_year"] = stamp.dt.dayofyear
    out["hour"] = stamp.dt.hour
    out["is_weekend"] = stamp.dt.dayofweek.isin([5, 6]).astype(int)
    # September/October is the Apple launch window; November/December is the
    # Indian festive + year-end discounting window.
    out["is_launch_season"] = stamp.dt.month.isin([9, 10]).astype(int)
    out["is_holiday_season"] = stamp.dt.month.isin([11, 12]).astype(int)
    out["days_since_series_start"] = (stamp - stamp.min()).dt.total_seconds() / 86400.0

    grouped = frame.groupby(["Model", "Source"], sort=False)
    price = frame["Price"]

    # shift(1) is what makes every one of these causal.
    past = grouped["Price"].shift(1)
    out["lag_price_1"] = past
    out["lag_price_2"] = grouped["Price"].shift(2)

    def rolled(window: int, statistic: str) -> pd.Series:
        shifted = grouped["Price"].shift(1)
        roller = shifted.groupby([frame["Model"], frame["Source"]]).rolling(
            window=window, min_periods=1
        )
        series = getattr(roller, statistic)()
        return series.reset_index(level=[0, 1], drop=True)

    out["roll_mean_3"] = rolled(3, "mean")
    out["roll_mean_7"] = rolled(7, "mean")
    out["roll_std_7"] = rolled(7, "std")
    out["roll_mean_30"] = rolled(30, "mean")

    expanding = grouped["Price"].shift(1).groupby(
        [frame["Model"], frame["Source"]]
    ).expanding(min_periods=1)
    out["expanding_mean"] = expanding.mean().reset_index(level=[0, 1], drop=True)
    out["expanding_std"] = expanding.std().reset_index(level=[0, 1], drop=True)

    out["momentum_1"] = out["lag_price_1"] - out["lag_price_2"]
    out["momentum_7"] = out["lag_price_1"] - out["roll_mean_7"]

    elapsed = grouped["Scraped_At"].diff().dt.total_seconds() / 86400.0
    out["days_since_prev_obs"] = elapsed
    out["obs_index"] = grouped.cumcount()

    # ---- Anchored features -------------------------------------------------
    # The anchor is today's price, which is known at forecast time. Dividing by
    # it strips out the level and the long-run depreciation trend, leaving the
    # part of the series a tree model can actually generalise over.
    anchor = price.replace(0, np.nan)

    roll_max_30 = rolled(30, "max")
    roll_min_30 = rolled(30, "min")

    out["rel_lag_1"] = out["lag_price_1"] / anchor
    out["rel_roll_mean_7"] = out["roll_mean_7"] / anchor
    out["rel_roll_mean_30"] = out["roll_mean_30"] / anchor
    out["rel_expanding_mean"] = out["expanding_mean"] / anchor
    out["rel_roll_max_30"] = roll_max_30 / anchor
    out["rel_roll_min_30"] = roll_min_30 / anchor

    # Volatility as a coefficient of variation, so it is comparable across
    # handsets that sit at very different price points.
    out["volatility_7"] = out["roll_std_7"] / anchor
    out["volatility_30"] = rolled(30, "std") / anchor

    # How far below its recent high the series is trading. Large drawdowns tend
    # to mean a sale is running, and sales mend.
    out["drawdown_from_30d_high"] = (anchor - roll_max_30) / roll_max_30

    # Short and medium momentum, normalised.
    out["trend_7"] = (anchor - out["roll_mean_7"]) / anchor
    out["trend_30"] = (anchor - out["roll_mean_30"]) / anchor

    out["Price"] = price.values
    out["Scraped_At"] = stamp.values
    out["Model"] = frame["Model"].values
    out["Source"] = frame["Source"].values
    return out


def feature_matrix(featured: pd.DataFrame) -> pd.DataFrame:
    """Select the model input columns in a fixed, serialisable order."""
    return featured[FEATURE_COLUMNS].astype(float)
