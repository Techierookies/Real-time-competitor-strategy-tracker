"""
Application settings, read from the environment.

Nothing in this file has a usable secret as its default. The previous version
of this project shipped a live Gmail app password as a module-level constant
in `refresh_scraper.py`, which meant anyone who cloned the repository could
send mail as that account. Secrets now come from the environment only, and the
application refuses to start in production if they are missing.
"""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- Runtime -----------------------------------------------------------
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    api_title: str = "Competitor Strategy Tracker API"
    api_version: str = "2.0.0"

    # ---- Storage -----------------------------------------------------------
    # One database, not three. The previous layout had users in
    # backend/competitor_tracker.db and scraped prices in a different file at
    # the repository root, so the prediction layer and the auth layer were
    # looking at different databases and neither could see the other's data.
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{BASE_DIR / 'data' / 'tracker.db'}"
    )

    artifact_dir: str = Field(default_factory=lambda: str(BASE_DIR / "ml" / "artifacts"))

    # ---- Security ----------------------------------------------------------
    # Generated per-process when unset, which is fine for local development and
    # deliberately useless in production: a restart invalidates every token,
    # so the missing-secret failure is loud rather than silent.
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 12

    cors_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")

    # ---- Optional integrations --------------------------------------------
    gemini_api_key: str | None = Field(default=None)
    gemini_model: str = "gemini-2.5-flash"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    alert_recipients: str = ""

    scrape_user_agent: str = (
        "Mozilla/5.0 (compatible; CompetitorTracker/2.0; +https://example.org/bot)"
    )
    scrape_delay_seconds: float = 4.0
    respect_robots: bool = True
    targets_file: str = Field(
        default_factory=lambda: str(BASE_DIR / "collector" / "targets.json")
    )

    # ---- Live operation ----------------------------------------------------
    # 0 turns the in-app scheduler off. Six product pages every few hours is
    # plenty for daily-level forecasting and keeps load on the retailers low.
    collect_interval_minutes: int = Field(default=0, ge=0)
    # 0 turns automatic retraining off.
    retrain_interval_hours: int = Field(default=0, ge=0)
    # Days of live history every series needs before retraining switches from
    # the synthetic bootstrap data to real data.
    min_training_days: int = Field(default=60, ge=14)
    # Shared secret that lets an external collector (e.g. GitHub Actions) push
    # readings without an admin login. Unset disables the ingest endpoint.
    collector_token: str | None = Field(default=None)

    @field_validator("environment")
    @classmethod
    def _known_environment(cls, value: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"environment must be one of {sorted(allowed)}")
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def alert_recipient_list(self) -> list[str]:
        return [item.strip() for item in self.alert_recipients.split(",") if item.strip()]

    @property
    def sqlite_path(self) -> Path:
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("Only sqlite:/// URLs are supported in this build.")
        return Path(self.database_url.removeprefix("sqlite:///"))

    def validate_for_production(self) -> list[str]:
        """Return the list of things that must be fixed before going live."""
        problems: list[str] = []
        if not self.is_production:
            return problems
        if not os.getenv("JWT_SECRET"):
            problems.append(
                "JWT_SECRET is not set. Tokens would be invalidated on every "
                "restart and would differ between replicas."
            )
        if "*" in self.cors_origin_list:
            problems.append("CORS_ORIGINS must not be '*' in production.")
        if self.debug:
            problems.append("DEBUG must be false in production.")
        if self.collector_token is not None and len(self.collector_token) < 24:
            problems.append("COLLECTOR_TOKEN must be at least 24 characters.")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
