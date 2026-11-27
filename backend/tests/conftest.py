"""Shared pytest fixtures: an isolated app against a temporary database."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("JWT_SECRET", "test-secret-not-used-anywhere-real")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("ARTIFACT_DIR", str(ROOT / "ml" / "artifacts"))

    from app.config import get_settings
    from app.deps import _database, _forecast_service

    # Settings and connections are cached for speed in production; the cache
    # has to be cleared between tests or every test shares one database.
    get_settings.cache_clear()
    _database.cache_clear()
    _forecast_service.cache_clear()

    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

    get_settings.cache_clear()
    _database.cache_clear()
    _forecast_service.cache_clear()


@pytest.fixture()
def admin_token(client):
    """Create an admin directly, since signup deliberately cannot grant it."""
    from app.config import get_settings
    from app.db import Database
    from app.security import create_access_token, hash_password

    settings = get_settings()
    db = Database(settings.sqlite_path)
    with db.connect() as connection:
        connection.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'admin')
            """,
            ("Admin", "admin@example.com", hash_password("admin-pass-123")),
        )
    return create_access_token("admin@example.com", "admin", settings)


@pytest.fixture()
def seeded(client):
    """Insert a believable price history for one series."""
    from app.config import get_settings
    from app.db import Database

    db = Database(get_settings().sqlite_path)
    start = datetime(2026, 1, 1)
    price = 90_000.0
    for day in range(120):
        stamp = start + timedelta(days=day)
        price *= 0.9995
        for source, offset in (("Amazon", 0), ("Flipkart", -400)):
            db.record_observation(
                {
                    "model": "iPhone 17",
                    "source": source,
                    "price": round(price + offset, 2),
                    "rating": 4.4,
                    "review_count": 100 + day,
                    "review_text": "Solid phone.",
                    "url": None,
                    "observed_at": stamp.isoformat(timespec="seconds"),
                }
            )
    return db
