# Multi-stage build. The runtime image carries no compilers and no build
# caches, which keeps it small and reduces the attack surface.

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/backend

# libgomp is LightGBM's OpenMP runtime; without it the model fails to import.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser

COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=appuser:appuser ml ./ml
COPY --chown=appuser:appuser backend ./backend
COPY --chown=appuser:appuser collector ./collector
COPY --chown=appuser:appuser data ./data

RUN mkdir -p /app/data /app/ml/artifacts && chown -R appuser:appuser /app

# Never run the application as root.
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Honour the platform-assigned PORT, which Render, Railway and Fly all set.
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
