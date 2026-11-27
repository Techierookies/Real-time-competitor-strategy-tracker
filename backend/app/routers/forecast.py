"""Forecasting, price recommendation and live accuracy endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import Database
from ..deps import get_db, get_forecast_service
from ..schemas import ForecastRequest, ForecastResponse, PricingRequest
from ..security import require_admin

router = APIRouter(prefix="/api", tags=["forecast"])

RETAILERS = ("Amazon", "Flipkart")


def _history_or_404(db: Database, model: str, source: str, minimum: int = 20):
    from ml.features import clean_frame, normalise_model, normalise_source

    model = normalise_model(model)
    source = normalise_source(source)
    frame = db.series_history(model, source)

    if frame.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price history stored for {model} on {source}.",
        )

    frame = clean_frame(frame)
    if len(frame) < minimum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Only {len(frame)} usable observations for {model} on "
                f"{source}; at least {minimum} are needed for a forecast. "
                f"Run the collector for longer before relying on this series."
            ),
        )
    return frame, model, source


@router.get("/series")
def list_series(db: Database = Depends(get_db)) -> dict:
    """Every (model, retailer) series the tracker currently holds."""
    return {"series": db.known_series()}


@router.post("/forecast", response_model=ForecastResponse)
def create_forecast(
    payload: ForecastRequest,
    db: Database = Depends(get_db),
    service=Depends(get_forecast_service),
) -> ForecastResponse:
    """Forecast one series and persist the prediction.

    Persisting matters: a forecast that is never written down can never be
    scored. These rows are what `/api/accuracy` later grades against reality.
    """
    frame, model, source = _history_or_404(db, payload.model, payload.source)
    result = service.forecast(frame, model, source, payload.horizon_days)

    db.record_forecast(
        {
            "model": result.model,
            "source": result.source,
            "horizon_days": result.horizon_days,
            "anchor_price": result.anchor_price,
            "predicted_price": result.predicted_price,
            "lower_price": result.lower_price,
            "upper_price": result.upper_price,
            "model_family": result.model_family,
            "as_of": result.as_of,
            "target_date": result.target_date,
        }
    )
    return ForecastResponse(**result.to_dict())


@router.get("/compare/{model}")
def compare_retailers(
    model: str,
    horizon_days: int = Query(default=14, ge=1, le=90),
    db: Database = Depends(get_db),
    service=Depends(get_forecast_service),
) -> dict:
    """Forecast one handset across every retailer and name the cheaper one."""
    results = {}
    errors = {}

    for retailer in RETAILERS:
        try:
            frame, canonical, source = _history_or_404(db, model, retailer)
            results[source] = service.forecast(
                frame, canonical, source, horizon_days
            ).to_dict()
        except HTTPException as error:
            errors[retailer] = error.detail

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "No retailer had enough history.", "detail": errors},
        )

    cheapest = min(results, key=lambda key: results[key]["predicted_price"])
    spread = None
    if len(results) == 2:
        values = [entry["predicted_price"] for entry in results.values()]
        spread = round(abs(values[0] - values[1]), 2)

    return {
        "model": model,
        "horizon_days": horizon_days,
        "forecasts": results,
        "cheapest_forecast": cheapest,
        "forecast_spread": spread,
        "unavailable": errors,
    }


@router.post("/pricing/recommend")
def recommend(
    payload: PricingRequest,
    db: Database = Depends(get_db),
    service=Depends(get_forecast_service),
) -> dict:
    """Recommend a listing price, with the reasoning attached."""
    from ml.pricing import recommend_price

    frame, model, source = _history_or_404(db, payload.model, payload.source)
    own = service.forecast(frame, model, source, payload.horizon_days)

    rival_name = "Flipkart" if source == "Amazon" else "Amazon"
    rival_price = None
    try:
        rival_frame, _, rival_source = _history_or_404(db, model, rival_name)
        rival_price = service.forecast(
            rival_frame, model, rival_source, payload.horizon_days
        ).predicted_price
    except HTTPException:
        # A missing rival series is normal early on and must not break the
        # recommendation; it just removes the competitive-response term.
        rival_price = None

    recommendation = recommend_price(
        model=model,
        source=source,
        current_price=own.anchor_price,
        forecast_price=own.predicted_price,
        competitor_price=rival_price,
        unit_cost=payload.unit_cost,
        elasticity=payload.elasticity,
        min_margin=payload.min_margin,
        max_move_pct=payload.max_move_pct,
    )

    return {
        "forecast": own.to_dict(),
        "recommendation": recommendation.to_dict(),
    }


@router.get("/anomalies/{model}/{source}")
def anomalies(
    model: str,
    source: str,
    db: Database = Depends(get_db),
) -> dict:
    """Statistically unusual price moves in a series, newest first."""
    from ml.pricing import detect_price_anomalies

    frame, canonical, canonical_source = _history_or_404(db, model, source, minimum=5)
    events = detect_price_anomalies(frame)
    return {
        "model": canonical,
        "source": canonical_source,
        "event_count": len(events),
        "events": list(reversed(events))[:50],
    }


@router.get("/model-card")
def model_card(service=Depends(get_forecast_service)) -> dict:
    """Offline evaluation results for the models currently being served."""
    return service.model_card()


@router.get("/accuracy")
def accuracy(db: Database = Depends(get_db)) -> dict:
    """How the stored forecasts actually performed once the date arrived."""
    newly_resolved = db.resolve_due_forecasts()
    return {
        "newly_resolved": newly_resolved,
        "by_horizon": db.live_accuracy(),
        "note": (
            "Measured against observations the collector recorded after each "
            "forecast was made. Empty until forecasts reach their target date."
        ),
    }


@router.post("/accuracy/resolve", dependencies=[Depends(require_admin)])
def resolve(db: Database = Depends(get_db)) -> dict:
    return {"resolved": db.resolve_due_forecasts()}
