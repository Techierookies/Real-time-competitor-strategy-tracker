"""
Inference layer: turn a stored price history into a calibrated forecast.

The important property here is that serving reuses exactly the same feature
code as training (`ml.features.build_features`). The original implementation
rebuilt roughly thirty features by hand inside the prediction function, which
is how a model ends up quietly scoring a different feature vector in
production than the one it was fitted on.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .features import (
    add_target_calendar_features,
    build_features,
    feature_matrix,
    normalise_model,
    normalise_source,
    to_daily_panel,
)

DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


@dataclass
class Forecast:
    model: str
    source: str
    horizon_days: int
    as_of: str
    target_date: str
    anchor_price: float
    predicted_price: float
    lower_price: float
    upper_price: float
    expected_change_pct: float
    confidence_level: float
    model_family: str
    history_points: int

    def to_dict(self) -> dict:
        return asdict(self)


class ForecastService:
    """Loads artifacts once and serves forecasts for any stored series."""

    def __init__(self, artifact_dir: Path | str = DEFAULT_ARTIFACT_DIR):
        self.artifact_dir = Path(artifact_dir)
        self.spec = joblib.load(self.artifact_dir / "feature_spec.joblib")
        self.horizons = list(self.spec["horizons"])
        self.families = self.spec.get("selected_families", {})
        self.offsets = self.spec.get("conformal_offsets", {})
        self._cache: dict[str, object] = {}

        metrics_path = self.artifact_dir / "metrics.json"
        self.metrics = (
            json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
        )

    def _estimator(self, horizon: int, kind: str):
        key = f"h{horizon}_{kind}"
        if key not in self._cache:
            self._cache[key] = joblib.load(
                self.artifact_dir / f"forecast_h{horizon}_{kind}.joblib"
            )
        return self._cache[key]

    def nearest_horizon(self, requested: int) -> int:
        """Snap to the nearest trained horizon rather than extrapolating."""
        return min(self.horizons, key=lambda h: abs(h - requested))

    def forecast(
        self,
        history: pd.DataFrame,
        model_name: str,
        source: str,
        horizon_days: int = 14,
    ) -> Forecast:
        """Forecast one series.

        `history` must contain Model, Source, Price, Rating, Reviews and
        Scraped_At for a single (model, source) pair, oldest first.
        """
        model_name = normalise_model(model_name)
        source = normalise_source(source)
        horizon = self.nearest_horizon(horizon_days)

        panel = to_daily_panel(history)
        if panel.empty:
            raise ValueError(f"No usable history for {model_name} on {source}")

        featured = build_features(panel)
        featured = add_target_calendar_features(featured, horizon)

        latest = featured.iloc[[-1]]
        matrix = feature_matrix(latest)

        family = self.families.get(str(horizon), "lightgbm")
        point = self._estimator(horizon, "point")
        inputs = matrix.fillna(-1) if family == "random_forest" else matrix

        anchor = float(latest["Price"].iloc[0])
        log_ratio = float(point.predict(inputs)[0])
        predicted = anchor * float(np.exp(log_ratio))

        offset = float(self.offsets.get(str(horizon), 0.0))
        low_ratio = float(self._estimator(horizon, "p10").predict(matrix)[0]) - offset
        high_ratio = float(self._estimator(horizon, "p90").predict(matrix)[0]) + offset

        as_of = pd.Timestamp(latest["Scraped_At"].iloc[0])
        return Forecast(
            model=model_name,
            source=source,
            horizon_days=horizon,
            as_of=as_of.isoformat(),
            target_date=(as_of + timedelta(days=horizon)).date().isoformat(),
            anchor_price=round(anchor, 2),
            predicted_price=round(predicted, 2),
            lower_price=round(anchor * float(np.exp(low_ratio)), 2),
            upper_price=round(anchor * float(np.exp(high_ratio)), 2),
            expected_change_pct=round((predicted / anchor - 1) * 100, 2),
            confidence_level=0.80,
            model_family=family,
            history_points=int(len(panel)),
        )

    def model_card(self) -> dict:
        """Everything the API needs to be honest about what it is serving."""
        horizons = self.metrics.get("horizons", {})
        return {
            "trained_at": self.metrics.get("trained_at"),
            "data_source": self.metrics.get("data_source", "synthetic"),
            "task": self.metrics.get("task"),
            "validation": self.metrics.get("validation"),
            "training_rows": self.metrics.get("daily_rows"),
            "date_range": self.metrics.get("date_range"),
            "horizons": {
                key: {
                    "selected_model": report.get("selection", {}).get("family"),
                    "mae_rupees": report["models"]
                    .get(report.get("selection", {}).get("family", ""), {})
                    .get("mae"),
                    "mape": report["models"]
                    .get(report.get("selection", {}).get("family", ""), {})
                    .get("mape"),
                    "beats_naive_baseline": report.get("selection", {}).get(
                        "beats_baseline"
                    ),
                    "improvement_over_baseline": report.get("selection", {}).get(
                        "improvement_over_best_baseline"
                    ),
                    "interval_coverage": report.get("p10_p90_interval_coverage"),
                }
                for key, report in horizons.items()
            },
        }


@lru_cache(maxsize=1)
def get_forecast_service(artifact_dir: str | None = None) -> ForecastService:
    return ForecastService(artifact_dir or DEFAULT_ARTIFACT_DIR)
