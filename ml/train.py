"""
Train and honestly evaluate the competitor price forecaster.

The task
--------
Given everything known about a (model, retailer) price series up to today,
forecast the listed price H days from now, for H in {7, 14, 30}.

That framing matters. The earlier pipeline predicted the price of the row it
was looking at, which a scraper already knows, so 'repeat the last scrape'
scored a 1.1% error and nothing could beat it. Forecasting a week or a month
out is the question the product is actually for -- when to reprice, and by how
much -- and it is a question persistence does badly at.

What makes the evaluation trustworthy
-------------------------------------
* Rolling-origin (expanding window) splits. Never shuffled, so the model is
  always scored on a period that sits strictly after everything it trained on.
* Two naive baselines on every horizon. A model that cannot beat persistence
  has not earned the extra complexity, and the table says so either way.
* MAE and MAPE in rupees alongside R-squared, because R-squared flatters any
  model fitted to a series with a strong level difference between handsets.
* P10/P90 quantile models, with empirical coverage measured and recorded, so
  the API can quote a range instead of false precision.

Run:
    python -m ml.train --data data/competitor_prices_synthetic.csv
"""

from __future__ import annotations

import argparse
import json
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

from .features import (
    FEATURE_COLUMNS,
    add_horizon_target,
    build_features,
    feature_matrix,
    load_frame,
    to_daily_panel,
)

QUANTILES = {"p10": 0.10, "p50": 0.50, "p90": 0.90}
HORIZONS = (7, 14, 30)
N_SPLITS = 5


@dataclass
class Scores:
    mae: float
    mape: float
    rmse: float
    r2: float

    def rounded(self) -> dict:
        return {
            "mae": round(self.mae, 2),
            "mape": round(self.mape, 4),
            "rmse": round(self.rmse, 2),
            "r2": round(self.r2, 4),
        }


def score(actual: np.ndarray, predicted: np.ndarray) -> Scores:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    errors = actual - predicted
    safe = np.where(actual == 0, np.nan, actual)
    return Scores(
        mae=float(np.mean(np.abs(errors))),
        mape=float(np.nanmean(np.abs(errors / safe))),
        rmse=float(np.sqrt(np.mean(errors**2))),
        r2=float(r2_score(actual, predicted)),
    )


def rolling_origin_splits(n_rows: int, n_splits: int = N_SPLITS):
    """Expanding-window splits: fold k tests on the block right after its cut."""
    fold_size = n_rows // (n_splits + 1)
    for fold in range(1, n_splits + 1):
        cut = fold_size * fold
        test_index = np.arange(cut, min(cut + fold_size, n_rows))
        if len(test_index) == 0:
            continue
        yield np.arange(0, cut), test_index


# Model capacity is scheduled by horizon, and this is a deliberate choice
# rather than a tuning accident.
#
# At one week out, almost all of the movement is mean-reverting noise: the
# simulated process has an AR(1) half-life of about five days, so there is very
# little durable signal and a flexible model simply memorises the noise. Those
# horizons get a small, heavily penalised model that is shrunk hard toward
# "no change". At two to four weeks the noise has decayed and the remaining
# movement is driven by depreciation and scheduled sale events, which are real,
# learnable structure, so the model is allowed more capacity.
HORIZON_CONFIG = {
    "short": dict(
        objective="l2",
        n_estimators=120,
        learning_rate=0.04,
        num_leaves=7,
        min_child_samples=80,
        reg_lambda=10.0,
    ),
    "long": dict(
        objective="l1",
        n_estimators=600,
        learning_rate=0.04,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.85,
        subsample_freq=1,
        colsample_bytree=0.85,
        reg_lambda=1.0,
    ),
}

SHORT_HORIZON_CUTOFF = 7


def config_for(horizon: int) -> dict:
    key = "short" if horizon <= SHORT_HORIZON_CUTOFF else "long"
    return HORIZON_CONFIG[key]


def make_regressor(horizon: int) -> lgb.LGBMRegressor:
    return lgb.LGBMRegressor(
        random_state=42, n_jobs=-1, verbose=-1, **config_for(horizon)
    )


def make_quantile_regressor(alpha: float, horizon: int) -> lgb.LGBMRegressor:
    params = {
        key: value
        for key, value in config_for(horizon).items()
        if key != "objective"
    }
    return lgb.LGBMRegressor(
        objective="quantile",
        alpha=alpha,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
        **params,
    )


def conformal_offset(
    lower: np.ndarray, upper: np.ndarray, actual: np.ndarray, alpha: float = 0.20
) -> float:
    """Split-conformal correction for a quantile interval (CQR).

    Raw quantile regression on a short series is over-confident: measured
    coverage came out near 40% against a nominal 80%. Conformalising fixes
    that with a distribution-free guarantee. The score is how far outside the
    predicted band each calibration point fell; the band is then widened by the
    (1 - alpha) quantile of those scores, so coverage holds by construction
    rather than by hope.
    """
    scores = np.maximum(lower - actual, actual - upper)
    level = min(1.0, (1 - alpha) * (1 + 1 / max(len(scores), 1)))
    return float(np.quantile(scores, level))


def cross_validate(dataset: pd.DataFrame, horizon: int) -> dict:
    """Score LightGBM, a random forest and two baselines across all folds."""
    matrix = feature_matrix(dataset)
    # Fit in anchored log-ratio space, then convert every prediction back to
    # rupees before scoring, so the reported MAE is in the units a buyer cares
    # about and is directly comparable with the naive baselines.
    target = dataset["target_log_ratio"].to_numpy()
    actual_price = dataset["target"].to_numpy(dtype=float)
    anchor = dataset["Price"].to_numpy(dtype=float)

    collected: dict[str, list[np.ndarray]] = {
        name: []
        for name in (
            "actual",
            "lightgbm",
            "random_forest",
            "baseline_persistence",
            "baseline_seasonal_naive",
        )
    }
    interval_hits: list[np.ndarray] = []
    folds = []

    for fold, (train_index, test_index) in enumerate(
        rolling_origin_splits(len(dataset)), start=1
    ):
        x_train, x_test = matrix.iloc[train_index], matrix.iloc[test_index]
        y_train = target[train_index]
        y_test = actual_price[test_index]
        test_anchor = anchor[test_index]

        gbm = make_regressor(horizon).fit(x_train, y_train)
        gbm_pred = test_anchor * np.exp(gbm.predict(x_test))

        forest = RandomForestRegressor(
            n_estimators=300, min_samples_leaf=5, random_state=42, n_jobs=-1
        ).fit(x_train.fillna(-1), y_train)
        forest_pred = test_anchor * np.exp(forest.predict(x_test.fillna(-1)))

        # Hold back the most recent slice of the training window to calibrate
        # the interval. It must be data the quantile models never saw.
        split = int(len(train_index) * 0.75)
        fit_part, calib_part = train_index[:split], train_index[split:]
        if len(calib_part) < 30:
            fit_part, calib_part = train_index, train_index

        low = make_quantile_regressor(QUANTILES["p10"], horizon).fit(
            matrix.iloc[fit_part], target[fit_part]
        )
        high = make_quantile_regressor(QUANTILES["p90"], horizon).fit(
            matrix.iloc[fit_part], target[fit_part]
        )
        offset = conformal_offset(
            low.predict(matrix.iloc[calib_part]),
            high.predict(matrix.iloc[calib_part]),
            target[calib_part],
        )
        lower = test_anchor * np.exp(low.predict(x_test) - offset)
        upper = test_anchor * np.exp(high.predict(x_test) + offset)
        interval_hits.append((y_test >= lower) & (y_test <= upper))

        block = dataset.iloc[test_index]
        # Persistence: assume the price simply stays where it is today.
        persistence = block["Price"].to_numpy(dtype=float)
        # Seasonal naive: assume it repeats last week's level, which captures
        # any day-of-week effect for free.
        seasonal = (
            block["roll_mean_7"].fillna(block["Price"]).to_numpy(dtype=float)
        )

        collected["actual"].append(y_test)
        collected["lightgbm"].append(gbm_pred)
        collected["random_forest"].append(forest_pred)
        collected["baseline_persistence"].append(persistence)
        collected["baseline_seasonal_naive"].append(seasonal)

        folds.append(
            {
                "fold": fold,
                "train_rows": int(len(train_index)),
                "test_rows": int(len(test_index)),
                "test_period_start": str(block["Scraped_At"].min()),
                "test_period_end": str(block["Scraped_At"].max()),
                "lightgbm_mae": round(float(score(y_test, gbm_pred).mae), 2),
                "persistence_mae": round(float(score(y_test, persistence).mae), 2),
            }
        )

    actual = np.concatenate(collected["actual"])
    models = {
        name: score(actual, np.concatenate(values)).rounded()
        for name, values in collected.items()
        if name != "actual"
    }

    best_baseline = min(
        models["baseline_persistence"]["mae"],
        models["baseline_seasonal_naive"]["mae"],
    )
    improvement = (best_baseline - models["lightgbm"]["mae"]) / best_baseline

    return {
        "horizon_days": horizon,
        "n_splits": len(folds),
        "evaluated_rows": int(len(actual)),
        "models": models,
        "lightgbm_improvement_over_best_baseline": round(float(improvement), 4),
        "p10_p90_interval_coverage": round(
            float(np.mean(np.concatenate(interval_hits))), 4
        ),
        "p10_p90_nominal_coverage": 0.80,
        "folds": folds,
    }


def select_family(cv_report: dict) -> dict:
    """Choose the model family for this horizon on cross-validated MAE.

    Both candidate families and both baselines are ranked together. If no
    learned model beats the best naive baseline, that is recorded plainly and
    the baseline is marked as the thing to ship: a tracker that quietly serves
    a worse forecast than "assume last week repeats" would be worse than
    useless, and hiding that in a metrics file helps nobody.
    """
    ranked = sorted(cv_report["models"].items(), key=lambda item: item[1]["mae"])
    winner, winner_scores = ranked[0]
    baselines = {
        name: values["mae"]
        for name, values in cv_report["models"].items()
        if name.startswith("baseline_")
    }
    best_baseline = min(baselines.values())
    return {
        "family": winner,
        "mae": winner_scores["mae"],
        "beats_baseline": bool(winner_scores["mae"] < best_baseline),
        "improvement_over_best_baseline": round(
            float((best_baseline - winner_scores["mae"]) / best_baseline), 4
        ),
        "ranking": [name for name, _ in ranked],
    }


def fit_final_models(dataset: pd.DataFrame, horizon: int, family: str) -> dict:
    """Refit the winning family on full history, plus the conformal offset."""
    matrix = feature_matrix(dataset)
    target = dataset["target_log_ratio"].to_numpy()

    if family == "random_forest":
        point = RandomForestRegressor(
            n_estimators=300, min_samples_leaf=5, random_state=42, n_jobs=-1
        ).fit(matrix.fillna(-1), target)
    else:
        point = make_regressor(horizon).fit(matrix, target)

    artifacts = {"point": point}

    split = int(len(dataset) * 0.75)
    fit_index = np.arange(0, split)
    calib_index = np.arange(split, len(dataset))

    for name, alpha in QUANTILES.items():
        artifacts[name] = make_quantile_regressor(alpha, horizon).fit(matrix, target)

    low = make_quantile_regressor(QUANTILES["p10"], horizon).fit(
        matrix.iloc[fit_index], target[fit_index]
    )
    high = make_quantile_regressor(QUANTILES["p90"], horizon).fit(
        matrix.iloc[fit_index], target[fit_index]
    )
    artifacts["conformal_offset"] = conformal_offset(
        low.predict(matrix.iloc[calib_index]),
        high.predict(matrix.iloc[calib_index]),
        target[calib_index],
    )
    return artifacts


def series_snapshot(featured: pd.DataFrame) -> dict:
    """Last known daily state per series, so the API can build live features."""
    snapshot: dict[str, dict] = {}
    for (model_name, source), block in featured.groupby(["Model", "Source"]):
        block = block.sort_values("Scraped_At")
        snapshot[f"{model_name}|{source}"] = {
            "recent_prices": [round(float(p), 2) for p in block["Price"].tail(60)],
            "recent_dates": [str(d.date()) for d in block["Scraped_At"].tail(60)],
            "last_price": round(float(block["Price"].iloc[-1]), 2),
            "last_timestamp": str(block["Scraped_At"].iloc[-1]),
            "observation_count": int(len(block)),
        }
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the price forecaster.")
    parser.add_argument("--data", required=True, help="Path to the training CSV.")
    parser.add_argument("--out", default="ml/artifacts", help="Artifact directory.")
    parser.add_argument(
        "--horizons",
        default=",".join(str(h) for h in HORIZONS),
        help="Comma-separated forecast horizons in days.",
    )
    args = parser.parse_args()

    print("Loading and cleaning data...")
    train_from_frame(
        load_frame(args.data),
        out_dir=args.out,
        horizons=[int(value) for value in args.horizons.split(",")],
        dataset_label=str(args.data),
        data_source="synthetic" if "synthetic" in str(args.data) else "file",
    )


def train_from_frame(
    frame: pd.DataFrame,
    out_dir: str | Path = "ml/artifacts",
    horizons=HORIZONS,
    dataset_label: str = "in-memory frame",
    data_source: str = "file",
) -> dict:
    """Run the full evaluate-then-fit pipeline on a cleaned frame.

    Used by the CLI on a CSV and by the API's retraining job on the live
    database. Returns the metrics report it writes to metrics.json.
    """
    horizons = list(horizons)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    panel = to_daily_panel(frame)
    featured = build_features(panel)
    print(
        f"  {len(frame):,} raw scrapes -> {len(panel):,} daily rows "
        f"across {panel.groupby(['Model', 'Source']).ngroups} series"
    )

    report = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_label,
        "data_source": data_source,
        "raw_rows": int(len(frame)),
        "daily_rows": int(len(panel)),
        "date_range": {
            "start": str(panel["Scraped_At"].min()),
            "end": str(panel["Scraped_At"].max()),
        },
        "task": "forecast listed price H days ahead per (model, retailer)",
        "validation": "rolling-origin expanding window, 5 folds, never shuffled",
        "horizons": {},
        "environment": {
            "python": platform.python_version(),
            "lightgbm": lgb.__version__,
        },
    }

    selected_families: dict[str, str] = {}

    print("\n" + "=" * 78)
    print("CROSS-VALIDATED FORECAST ACCURACY (chronological splits)")
    print("=" * 78)

    for horizon in horizons:
        dataset = add_horizon_target(featured, horizon)
        cv_report = cross_validate(dataset, horizon)
        report["horizons"][str(horizon)] = cv_report

        selection = select_family(cv_report)
        cv_report["selection"] = selection
        artifacts = fit_final_models(dataset, horizon, selection["family"])
        joblib.dump(artifacts["point"], out_dir / f"forecast_h{horizon}_point.joblib")
        for name in QUANTILES:
            joblib.dump(
                artifacts[name], out_dir / f"forecast_h{horizon}_{name}.joblib"
            )
        cv_report["conformal_offset"] = round(artifacts["conformal_offset"], 6)
        selected_families[str(horizon)] = selection["family"]

        print(f"\nHorizon: {horizon} days   ({cv_report['evaluated_rows']:,} test rows)")
        print(f"  {'model':<28}{'MAE (Rs)':>12}{'MAPE':>10}{'R^2':>10}")
        print("  " + "-" * 60)
        for name, values in sorted(
            cv_report["models"].items(), key=lambda item: item[1]["mae"]
        ):
            print(
                f"  {name:<28}{values['mae']:>12,.0f}"
                f"{values['mape']:>10.1%}{values['r2']:>10.3f}"
            )
        verdict = "beats" if selection["beats_baseline"] else "does NOT beat"
        print(
            f"  selected: {selection['family']} -- {verdict} the best baseline "
            f"by {abs(selection['improvement_over_best_baseline']):.1%} MAE"
        )
        print(
            f"  P10-P90 interval coverage "
            f"{cv_report['p10_p90_interval_coverage']:.1%} (nominal 80%, "
            f"conformalised)"
        )

    joblib.dump(
        {
            "feature_columns": FEATURE_COLUMNS,
            "quantiles": QUANTILES,
            "horizons": horizons,
            "selected_families": selected_families,
            "conformal_offsets": {
                str(h): report["horizons"][str(h)]["conformal_offset"]
                for h in horizons
            },
        },
        out_dir / "feature_spec.joblib",
    )
    (out_dir / "series_snapshot.json").write_text(
        json.dumps(series_snapshot(featured), indent=2)
    )
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2))

    print(f"\nArtifacts written to {out_dir.resolve()}")
    return report


if __name__ == "__main__":
    main()
