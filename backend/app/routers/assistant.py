"""Natural-language assistant over the tracker's own numbers."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends

from ..config import Settings, get_settings
from ..db import Database
from ..deps import get_db, get_forecast_service
from ..schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["assistant"])

RETAILERS = ("Amazon", "Flipkart")


def parse_model(text: str) -> str | None:
    """Match an iPhone generation without matching stray digits.

    The previous parser checked `'15' in user_input.split()`, so the message
    "forecast for 30 days" resolved to a handset and "iphone15" did not. A
    word-boundary pattern handles both.
    """
    match = re.search(r"\biphone\s*-?\s*(15|16|17)\b", text, flags=re.IGNORECASE)
    if match:
        return f"iPhone {match.group(1)}"
    match = re.search(r"\b(15|16|17)\b", text)
    return f"iPhone {match.group(1)}" if match else None


def parse_retailers(text: str) -> list[str]:
    lowered = text.lower()
    found = [name for name in RETAILERS if name.lower() in lowered]
    return found or list(RETAILERS)


def parse_horizon(text: str) -> int:
    match = re.search(r"(\d{1,3})\s*(day|days|d)\b", text, flags=re.IGNORECASE)
    if match:
        return max(1, min(90, int(match.group(1))))
    if re.search(r"\bnext month\b|\bmonth\b", text, flags=re.IGNORECASE):
        return 30
    if re.search(r"\bnext week\b|\bweek\b", text, flags=re.IGNORECASE):
        return 7
    return 14


@router.post("/assistant")
def assistant(
    payload: ChatRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
    service=Depends(get_forecast_service),
) -> dict:
    """Answer a pricing question from stored data.

    The numbers are always computed by the forecasting pipeline. A language
    model, if configured, only rewrites those numbers into prose. It is never
    asked to invent a price, which is what the previous implementation did and
    why its 'Gemini predicted price' disagreed with the model by tens of
    thousands of rupees with no way to tell which was right.
    """
    from ml.features import clean_frame

    message = payload.message.strip()
    model_name = parse_model(message)
    if not model_name:
        return {
            "reply": (
                "Tell me which handset you mean - iPhone 15, 16 or 17 - and "
                "I will forecast it. For example: "
                "'iPhone 17 on Amazon over the next 30 days'."
            ),
            "data": None,
        }

    horizon = parse_horizon(message)
    results, unavailable = {}, {}

    for retailer in parse_retailers(message):
        frame = clean_frame(db.series_history(model_name, retailer))
        if len(frame) < 20:
            unavailable[retailer] = f"only {len(frame)} observations stored"
            continue
        results[retailer] = service.forecast(
            frame, model_name, retailer, horizon
        ).to_dict()

    if not results:
        return {
            "reply": (
                f"I do not have enough price history for {model_name} yet "
                f"({unavailable}). Run the collector for a couple of weeks "
                f"and ask again."
            ),
            "data": {"unavailable": unavailable},
        }

    lines = [f"{model_name} - {horizon}-day forecast"]
    for retailer, entry in results.items():
        lines.append(
            f"{retailer}: Rs {entry['anchor_price']:,.0f} today, forecast "
            f"Rs {entry['predicted_price']:,.0f} by {entry['target_date']} "
            f"({entry['expected_change_pct']:+.1f}%), 80% range "
            f"Rs {entry['lower_price']:,.0f}-Rs {entry['upper_price']:,.0f}"
        )

    if len(results) == 2:
        cheaper = min(results, key=lambda key: results[key]["predicted_price"])
        gap = abs(
            results["Amazon"]["predicted_price"]
            - results["Flipkart"]["predicted_price"]
        )
        lines.append(f"{cheaper} is forecast cheaper, by about Rs {gap:,.0f}.")

    reply = "\n".join(lines)
    narrative = _narrate(reply, settings)

    return {
        "reply": narrative or reply,
        "data": {
            "model": model_name,
            "horizon_days": horizon,
            "forecasts": results,
            "unavailable": unavailable,
        },
        "grounded": True,
        "narrated_by_llm": bool(narrative),
    }


def _narrate(summary: str, settings: Settings) -> str | None:
    """Optionally rewrite the computed summary as prose."""
    if not settings.gemini_api_key:
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        llm = genai.GenerativeModel(settings.gemini_model)
        prompt = (
            "Rewrite the pricing summary below as two or three plain sentences "
            "for a retail manager. Use only the figures given. Do not invent "
            "numbers, and do not add predictions of your own.\n\n" + summary
        )
        return llm.generate_content(prompt).text.strip()
    except Exception:
        # Narration is cosmetic; the computed answer stands on its own.
        return None
