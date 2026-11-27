"""Export the tracker's pipeline output as the dashboard's data files.

Run from the project root (python scripts/export_dashboard.py dashboard_data) after `python -m ml.train` and
`python -m collector.collect --source sample`:

    python export_dashboard.py <out_dir>
"""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")

from ml.features import load_frame, to_daily_panel  # noqa: E402
from ml.predict import ForecastService  # noqa: E402
from ml.pricing import detect_price_anomalies, recommend_price  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
CODE = Path(__file__).read_text()
CSV = "data/competitor_prices_synthetic.csv"


def dump(name, rows, extra_meta=None):
    meta = [
        {"label": "export_dashboard.py", "value": CODE, "type": "code", "lang": "python"},
        {"label": "Input", "value": CSV},
    ] + (extra_meta or [])
    (OUT / name).write_text(json.dumps({"rows": rows, "meta": meta}, default=str))


raw = pd.read_csv(CSV)
frame = load_frame(CSV)
panel = to_daily_panel(frame)
service = ForecastService("ml/artifacts")
metrics = json.loads(Path("ml/artifacts/metrics.json").read_text())

# 1. Weekly mean price per series (the full daily panel is ~2,400 rows).
weekly = []
for (model, source), block in panel.groupby(["Model", "Source"]):
    series = block.set_index("Scraped_At")["Price"].resample("W").mean().dropna()
    for stamp, price in series.items():
        weekly.append({"week": str(stamp.date()), "model": model,
                       "source": source, "price": round(float(price))})
pd.DataFrame(weekly).to_csv(OUT / "prices_weekly.csv", index=False)

# 2. A forecast for every series at every trained horizon.
forecasts = []
for (model, source), block in frame.groupby(["Model", "Source"]):
    for horizon in (7, 14, 30):
        row = service.forecast(block, model, source, horizon).to_dict()
        row["series"] = f"{model} · {source}"
        forecasts.append(row)
dump("forecasts.json", forecasts)

# 3. Cross-validated accuracy, v2 per horizon, plus the v1 re-evaluation.
roles = {"lightgbm": "learned", "random_forest": "learned",
         "baseline_persistence": "baseline", "baseline_seasonal_naive": "baseline"}
names = {"lightgbm": "LightGBM", "random_forest": "Random forest",
         "baseline_persistence": "Persistence (no change)",
         "baseline_seasonal_naive": "Seasonal naive (last week)"}
accuracy = []
for horizon, report in metrics["horizons"].items():
    selected = report["selection"]["family"]
    for key, scores in report["models"].items():
        accuracy.append({
            "version": "v2", "horizon_days": int(horizon), "model": names[key],
            "role": "selected" if key == selected else roles[key],
            "mae": scores["mae"], "mape_pct": round(scores["mape"] * 100, 2),
            "r2": scores["r2"],
        })
# The original approach, re-scored on a chronological split during the audit.
for model, mae, mape, r2, role in [
    ("Random forest (original features)", 22644, 23.0, 0.046, "learned"),
    ("LightGBM (original features)", 23680, 23.6, -0.052, "learned"),
    ("Group mean (baseline)", 22322, 22.4, 0.074, "baseline"),
]:
    accuracy.append({"version": "v1", "horizon_days": None, "model": model,
                     "role": role, "mae": mae, "mape_pct": mape, "r2": r2})
dump("accuracy.json", accuracy, [{"label": "Metrics", "value": "ml/artifacts/metrics.json"}])

# 4. One summary row per horizon.
summary = []
for horizon, report in metrics["horizons"].items():
    selection = report["selection"]
    summary.append({
        "horizon_days": int(horizon),
        "selected_model": names[selection["family"]],
        "mae": selection["mae"],
        "improvement_pct": round(selection["improvement_over_best_baseline"] * 100, 1),
        "beats_baseline": selection["beats_baseline"],
        "coverage_pct": round(report["p10_p90_interval_coverage"] * 100, 1),
        "test_rows": report["evaluated_rows"],
        "folds": report["n_splits"],
    })
dump("horizon_summary.json", summary)

# 5. Price recommendations at 14 days, each against the rival's forecast.
lookup = {(f["model"], f["source"], f["horizon_days"]): f for f in forecasts}
recommendations = []
for model in ("iPhone 15", "iPhone 16", "iPhone 17"):
    for source, rival in (("Amazon", "Flipkart"), ("Flipkart", "Amazon")):
        own, other = lookup[(model, source, 14)], lookup[(model, rival, 14)]
        rec = recommend_price(model, source, own["anchor_price"],
                              own["predicted_price"], other["predicted_price"])
        recommendations.append({
            "series": f"{model} · {source}", "model": model, "source": source,
            "current_price": rec.current_price,
            "rival_forecast": rec.competitor_price,
            "own_forecast": rec.forecast_price,
            "recommended_price": rec.recommended_price,
            "change_pct": rec.change_from_current_pct,
            "demand_index": rec.expected_demand_index,
            "reasoning": " ".join(rec.rationale),
        })
dump("recommendations.json", recommendations)

# 6. Unusual price moves, on the daily panel.
events = []
for (model, source), block in frame.groupby(["Model", "Source"]):
    events += detect_price_anomalies(to_daily_panel(block))
for index, event in enumerate(sorted(events, key=lambda e: e["timestamp"], reverse=True)):
    event["id"] = index + 1
    event["timestamp"] = str(event["timestamp"])[:10]
dump("anomalies.json", sorted(events, key=lambda e: e["id"]))

# 7. What the dataset holds, per series.
profile = []
for (model, source), block in frame.groupby(["Model", "Source"]):
    profile.append({
        "series": f"{model} · {source}", "model": model, "source": source,
        "rows": int(len(block)),
        "first": str(block["Scraped_At"].min().date()),
        "last": str(block["Scraped_At"].max().date()),
        "mean_price": round(float(block["Price"].mean())),
        "min_price": round(float(block["Price"].min())),
        "max_price": round(float(block["Price"].max())),
        "mean_rating": round(float(block["Rating"].mean()), 2),
    })
dump("data_profile.json", profile)

# 8. The first rows of the training file, exactly as stored.
raw.head(8).to_csv(OUT / "raw_sample.csv", index=False)

print("exported", sorted(p.name for p in OUT.iterdir()))
