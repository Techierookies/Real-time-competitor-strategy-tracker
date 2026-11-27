"""Request and response models.

Validation lives here rather than being scattered through route bodies, so the
generated OpenAPI documentation describes the real contract and bad input is
rejected before it reaches the database.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def _strong_enough(cls, value: str) -> str:
        # A minimum length plus a character-class requirement blocks the
        # worst passwords without pushing users toward unmemorable ones.
        if value.isalpha() or value.isdigit():
            raise ValueError("Password must mix letters with digits or symbols.")
        return value


class LoginRequest(BaseModel):
    """Note the absence of an `isAdmin` field.

    The previous schema accepted the caller's own claim about whether it was an
    admin. Role now comes from the user record and is carried in a signed token.
    """

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    name: str
    email: EmailStr
    role: str


class ForecastRequest(BaseModel):
    model: str = Field(examples=["iPhone 17"])
    source: str = Field(examples=["Amazon"])
    horizon_days: int = Field(default=14, ge=1, le=90)


class ForecastResponse(BaseModel):
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


class PricingRequest(BaseModel):
    model: str
    source: str
    horizon_days: int = Field(default=14, ge=1, le=90)
    unit_cost: float | None = Field(default=None, gt=0)
    elasticity: float = Field(default=-1.8, lt=0)
    min_margin: float = Field(default=0.08, ge=0, le=1)
    max_move_pct: float = Field(default=0.08, gt=0, le=0.5)


class StoreProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=64)
    category: str = Field(min_length=1, max_length=80)
    price: float = Field(ge=0)
    cost: float | None = Field(default=None, ge=0)
    stock: int = Field(default=0, ge=0)
    status: str = Field(default="active")

    @field_validator("status")
    @classmethod
    def _known_status(cls, value: str) -> str:
        allowed = {"active", "inactive", "discontinued"}
        if value not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return value


class StoreProductUpdate(BaseModel):
    price: float | None = Field(default=None, ge=0)
    cost: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    status: str | None = None

    @field_validator("status")
    @classmethod
    def _known_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"active", "inactive", "discontinued"}
        if value not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return value


class ObservationIn(BaseModel):
    model: str
    source: str
    price: float = Field(gt=0)
    rating: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    review_text: str | None = None
    url: str | None = None
    observed_at: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
