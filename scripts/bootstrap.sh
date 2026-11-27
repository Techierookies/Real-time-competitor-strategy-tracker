#!/usr/bin/env bash
# One command to get from a fresh clone to a running, populated API.
set -euo pipefail

echo "==> Creating virtual environment"
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements-dev.txt

echo "==> Preparing configuration"
[ -f .env ] || cp .env.example .env

echo "==> Generating the synthetic price panel"
python -m ml.simulate --out data/competitor_prices_synthetic.csv

echo "==> Training and evaluating the forecasters"
python -m ml.train --data data/competitor_prices_synthetic.csv

echo "==> Seeding the database"
python -m collector.collect --source sample

echo "==> Running the test suite"
pytest -q

cat <<'MESSAGE'

Ready.

  Start the API:   uvicorn backend.app.main:app --reload
  Interactive docs: http://localhost:8000/docs
  Offline metrics:  ml/artifacts/metrics.json

MESSAGE
