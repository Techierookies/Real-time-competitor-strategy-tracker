"""
SQLite access layer.

Three defects from the previous version are fixed here.

1. A single module-level connection was shared across every request with
   `check_same_thread=False`. FastAPI serves requests on a thread pool, so
   concurrent writes raced against each other on one cursor. Connections are
   now per-operation and scoped by a context manager.
2. Scraped prices lived in one database file and users in another, so the
   prediction code could never see the data the scraper wrote.
3. There were no indexes, so every "latest price for this series" lookup was
   a full table scan.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'user'
                  CHECK (role IN ('user', 'admin')),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- One row per observation of one product on one retailer at one time.
CREATE TABLE IF NOT EXISTS price_observations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    model        TEXT    NOT NULL,
    source       TEXT    NOT NULL,
    price        REAL    NOT NULL CHECK (price > 0),
    rating       REAL,
    review_count INTEGER,
    review_text  TEXT,
    url          TEXT,
    observed_at  TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- The lookup that runs on every forecast: newest row for one series.
CREATE INDEX IF NOT EXISTS idx_observations_series
    ON price_observations (model, source, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_observations_time
    ON price_observations (observed_at DESC);

-- Stops the scraper writing the same reading twice when it is re-run.
CREATE UNIQUE INDEX IF NOT EXISTS idx_observations_unique
    ON price_observations (model, source, observed_at);

CREATE TABLE IF NOT EXISTS forecasts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    model             TEXT    NOT NULL,
    source            TEXT    NOT NULL,
    horizon_days      INTEGER NOT NULL,
    anchor_price      REAL    NOT NULL,
    predicted_price   REAL    NOT NULL,
    lower_price       REAL    NOT NULL,
    upper_price       REAL    NOT NULL,
    model_family      TEXT,
    as_of             TEXT    NOT NULL,
    target_date       TEXT    NOT NULL,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_forecasts_lookup
    ON forecasts (model, source, horizon_days, created_at DESC);

-- Written when a forecast is compared against what actually happened, so the
-- dashboard can show live accuracy rather than only offline test metrics.
CREATE TABLE IF NOT EXISTS forecast_outcomes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_id     INTEGER NOT NULL REFERENCES forecasts (id) ON DELETE CASCADE,
    actual_price    REAL    NOT NULL,
    absolute_error  REAL    NOT NULL,
    percent_error   REAL    NOT NULL,
    within_interval INTEGER NOT NULL,
    resolved_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model       TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,
    severity    TEXT    NOT NULL,
    old_price   REAL,
    new_price   REAL,
    change_pct  REAL,
    message     TEXT,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_alerts_recent
    ON alerts (created_at DESC);

CREATE TABLE IF NOT EXISTS store_products (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL,
    sku      TEXT    NOT NULL UNIQUE,
    category TEXT    NOT NULL,
    price    REAL    NOT NULL CHECK (price >= 0),
    cost     REAL    CHECK (cost >= 0),
    stock    INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    status   TEXT    NOT NULL DEFAULT 'active'
             CHECK (status IN ('active', 'inactive', 'discontinued'))
);

-- One row per live collection run, and one per product within it, so a
-- stale selector or a block shows up in the status endpoint the same day.
CREATE TABLE IF NOT EXISTS collection_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger     TEXT    NOT NULL,
    targets     INTEGER NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'running',
    stored      INTEGER NOT NULL DEFAULT 0,
    rejected    INTEGER NOT NULL DEFAULT 0,
    blocked     INTEGER NOT NULL DEFAULT 0,
    errors      INTEGER NOT NULL DEFAULT 0,
    started_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS collection_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES collection_runs (id) ON DELETE CASCADE,
    model       TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    url         TEXT,
    status      TEXT    NOT NULL,
    http_status INTEGER,
    price       REAL,
    method      TEXT,
    message     TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_collection_results_run
    ON collection_results (run_id);
"""


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """One connection per unit of work, committed or rolled back as a whole."""
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialise(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    # ---- Reads -------------------------------------------------------------

    def series_history(
        self, model: str, source: str, limit: int = 400
    ) -> pd.DataFrame:
        """Return one series oldest-first, shaped for the feature pipeline."""
        query = """
            SELECT model AS Model, source AS Source, price AS Price,
                   rating AS Rating, COALESCE(review_text, '') AS Reviews,
                   observed_at AS Scraped_At
            FROM price_observations
            WHERE model = ? AND source = ?
            ORDER BY observed_at DESC
            LIMIT ?
        """
        with self.connect() as connection:
            frame = pd.read_sql_query(query, connection, params=(model, source, limit))
        return frame.iloc[::-1].reset_index(drop=True)

    def latest_price(self, model: str, source: str) -> dict | None:
        query = """
            SELECT price, rating, review_count, observed_at
            FROM price_observations
            WHERE model = ? AND source = ?
            ORDER BY observed_at DESC
            LIMIT 1
        """
        with self.connect() as connection:
            row = connection.execute(query, (model, source)).fetchone()
        return dict(row) if row else None

    def known_series(self) -> list[dict]:
        query = """
            SELECT model, source, COUNT(*) AS observations,
                   MIN(observed_at) AS first_seen,
                   MAX(observed_at) AS last_seen
            FROM price_observations
            GROUP BY model, source
            ORDER BY model, source
        """
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query)]

    # ---- Writes ------------------------------------------------------------

    def record_observation(self, observation: dict) -> bool:
        """Insert one reading. Returns False if it was already recorded."""
        query = """
            INSERT OR IGNORE INTO price_observations
                (model, source, price, rating, review_count, review_text,
                 url, observed_at)
            VALUES (:model, :source, :price, :rating, :review_count,
                    :review_text, :url, :observed_at)
        """
        with self.connect() as connection:
            cursor = connection.execute(query, observation)
            return cursor.rowcount > 0

    def record_forecast(self, forecast: dict) -> int:
        query = """
            INSERT INTO forecasts
                (model, source, horizon_days, anchor_price, predicted_price,
                 lower_price, upper_price, model_family, as_of, target_date)
            VALUES (:model, :source, :horizon_days, :anchor_price,
                    :predicted_price, :lower_price, :upper_price,
                    :model_family, :as_of, :target_date)
        """
        with self.connect() as connection:
            cursor = connection.execute(query, forecast)
            return int(cursor.lastrowid)

    def record_alert(self, alert: dict) -> int:
        query = """
            INSERT INTO alerts
                (model, source, event_type, severity, old_price, new_price,
                 change_pct, message)
            VALUES (:model, :source, :event_type, :severity, :old_price,
                    :new_price, :change_pct, :message)
        """
        with self.connect() as connection:
            cursor = connection.execute(query, alert)
            return int(cursor.lastrowid)

    def resolve_due_forecasts(self) -> int:
        """Score past forecasts whose target date has arrived.

        This is what makes the accuracy figure on the dashboard real rather
        than a number copied out of a notebook: it compares what was predicted
        against what the scraper later observed.
        """
        query = """
            SELECT f.id, f.model, f.source, f.target_date,
                   f.predicted_price, f.lower_price, f.upper_price
            FROM forecasts f
            LEFT JOIN forecast_outcomes o ON o.forecast_id = f.id
            WHERE o.id IS NULL AND date(f.target_date) <= date('now')
        """
        resolved = 0
        with self.connect() as connection:
            pending = connection.execute(query).fetchall()
            for row in pending:
                actual = connection.execute(
                    """
                    SELECT price FROM price_observations
                    WHERE model = ? AND source = ?
                      AND date(observed_at) = date(?)
                    ORDER BY observed_at DESC LIMIT 1
                    """,
                    (row["model"], row["source"], row["target_date"]),
                ).fetchone()
                if actual is None:
                    continue

                price = float(actual["price"])
                error = abs(price - float(row["predicted_price"]))
                connection.execute(
                    """
                    INSERT INTO forecast_outcomes
                        (forecast_id, actual_price, absolute_error,
                         percent_error, within_interval)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        price,
                        error,
                        (error / price * 100) if price else 0.0,
                        int(row["lower_price"] <= price <= row["upper_price"]),
                    ),
                )
                resolved += 1
        return resolved

    def live_accuracy(self) -> dict:
        query = """
            SELECT f.horizon_days,
                   COUNT(*)                    AS resolved,
                   AVG(o.absolute_error)       AS mae,
                   AVG(o.percent_error)        AS mape,
                   AVG(o.within_interval)      AS coverage
            FROM forecast_outcomes o
            JOIN forecasts f ON f.id = o.forecast_id
            GROUP BY f.horizon_days
            ORDER BY f.horizon_days
        """
        with self.connect() as connection:
            return {
                str(row["horizon_days"]): {
                    "resolved_forecasts": row["resolved"],
                    "mae": round(row["mae"], 2) if row["mae"] else None,
                    "mape": round(row["mape"], 2) if row["mape"] else None,
                    "interval_coverage": (
                        round(row["coverage"], 4) if row["coverage"] else None
                    ),
                }
                for row in connection.execute(query)
            }

    # ---- Live collection log ---------------------------------------------

    def start_collection_run(self, trigger: str, targets: int) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO collection_runs (trigger, targets) VALUES (?, ?)",
                (trigger, targets),
            )
            return int(cursor.lastrowid)

    def finish_collection_run(self, run_id: int, summary: dict) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE collection_runs
                SET status = ?, stored = ?, rejected = ?, blocked = ?, errors = ?,
                    finished_at = datetime('now')
                WHERE id = ?
                """,
                (summary["status"], summary["stored"], summary["rejected"],
                 summary["blocked"], summary["errors"], run_id),
            )
            connection.executemany(
                """
                INSERT INTO collection_results
                    (run_id, model, source, url, status, http_status, price,
                     method, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (run_id, r["model"], r["source"], r["url"], r["status"],
                     r["http_status"], r["price"], r["method"], r["message"])
                    for r in summary["results"]
                ],
            )

    def recent_runs(self, limit: int = 10) -> list[dict]:
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM collection_runs ORDER BY id DESC LIMIT ?", (limit,)
                )
            ]

    def run_results(self, run_id: int) -> list[dict]:
        with self.connect() as connection:
            return [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT model, source, url, status, http_status, price,
                           method, message
                    FROM collection_results WHERE run_id = ?
                    ORDER BY model, source
                    """,
                    (run_id,),
                )
            ]

    def latest_prices(self) -> list[dict]:
        """Newest and previous reading for every series, with the change."""
        query = """
            SELECT model, source, price, rating, review_count, observed_at, url,
                   ROW_NUMBER() OVER (
                       PARTITION BY model, source ORDER BY observed_at DESC
                   ) AS rank
            FROM price_observations
        """
        with self.connect() as connection:
            rows = [dict(row) for row in connection.execute(
                f"SELECT * FROM ({query}) WHERE rank <= 2 ORDER BY model, source, rank"
            )]
        series: dict[tuple, dict] = {}
        for row in rows:
            key = (row["model"], row["source"])
            if row["rank"] == 1:
                series[key] = {
                    "model": row["model"], "source": row["source"],
                    "price": row["price"], "rating": row["rating"],
                    "review_count": row["review_count"],
                    "observed_at": row["observed_at"], "url": row["url"],
                    "previous_price": None, "change_pct": None,
                }
            elif key in series and row["price"]:
                entry = series[key]
                entry["previous_price"] = row["price"]
                entry["change_pct"] = round((entry["price"] / row["price"] - 1) * 100, 2)
        return list(series.values())

    def observations_frame(self):
        """All stored observations, shaped for the training pipeline."""
        query = """
            SELECT model AS Model, source AS Source, price AS Price,
                   rating AS Rating, COALESCE(review_text, '') AS Reviews,
                   observed_at AS Scraped_At
            FROM price_observations
            ORDER BY observed_at
        """
        with self.connect() as connection:
            return pd.read_sql_query(query, connection)
