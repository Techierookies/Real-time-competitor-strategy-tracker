# Real-Time Competitor Strategy Tracker

Scrapes live iPhone listing prices from Amazon and Flipkart on a schedule,
forecasts where each price is heading 7 to 30 days out, flags unusual moves,
and turns the forecasts into a defensible repricing recommendation.

Originally built as a team project during an Infosys Springboard internship,
where I led the team. This repository is my continuation of that work: the
data pipeline, the modelling approach, the evaluation harness, the API and the
deployment setup have been rebuilt. The [engineering notes](#engineering-notes)
section is honest about what was wrong in the first version and why the fixes
were necessary — that history is the most interesting part of the project.

---

## What it does

| Capability | Endpoint |
|---|---|
| Latest scraped price for every tracked series | `GET /api/prices/latest` |
| Daily price history for one series | `GET /api/prices/history/{model}/{source}` |
| What the collector did on each run, product by product | `GET /api/collect/status` |
| Run a collection pass now (admin) | `POST /api/collect/run` |
| Retrain the forecasters, on live data once there is enough (admin) | `POST /api/model/retrain` |
| Accept readings from an external collector (token) | `POST /api/collect/ingest` |
| Forecast a price 7, 14 or 30 days ahead, with an 80% interval | `POST /api/forecast` |
| Compare both retailers and name the cheaper one | `GET /api/compare/{model}` |
| Recommend a listing price from forecast, margin floor and elasticity | `POST /api/pricing/recommend` |
| Flag unusual price moves, separating real moves from bad scrapes | `GET /api/anomalies/{model}/{source}` |
| Report how past forecasts actually performed | `GET /api/accuracy` |
| Publish the offline evaluation of the models being served | `GET /api/model-card` |
| Answer questions in natural language, grounded in stored numbers | `POST /api/assistant` |

Interactive documentation is at `/docs` once running.

---

## Accuracy

Measured by rolling-origin cross-validation on a 3,222-row daily panel of the
synthetic bootstrap data (see [Data](#data)). Splits are chronological and
never shuffled, so each score comes from a period that sits strictly after
everything the model trained on.

| Horizon | Selected model | MAE | MAPE | vs. best naive baseline | 80% interval coverage |
|---|---|---|---|---|---|
| 7 days | Random Forest | ₹2,153 | 4.0% | **−3.0% error** | 72.8% |
| 14 days | Random Forest | ₹2,182 | 4.0% | **−3.2% error** | 75.9% |
| 30 days | LightGBM | ₹2,178 | 4.0% | **−14.4% error** | 78.0% |

The gain over "assume the price holds" is small a week or two out, where
most movement is noise, and large a month out, where depreciation and sale
events dominate. These figures describe the synthetic process. Once the live
collector has 60 days of history per series, retraining switches to real data
and the model card (`/api/model-card`) reports which data it was trained on.

Two baselines are scored alongside every model on every run: *persistence*
(assume the price does not move) and *seasonal naive* (assume last week's
level repeats). A forecaster that cannot beat "assume no change" has not
earned its complexity, and CI fails the build if any horizon stops beating its
baselines.

The model family is chosen per horizon by cross-validated MAE rather than
fixed in advance, which is why different horizons can end up with different
models.

Full results, including per-fold detail and feature importances, are written to
`ml/artifacts/metrics.json` on every training run.

---

## How the forecaster works

**Target.** The model predicts `log(price_at_t+h / price_at_t)` — the relative
change from today's known price — not the absolute rupee figure. Gradient-
boosted trees cannot extrapolate beyond their training range, and handset
prices trend steadily downward, so a model asked for an absolute price a month
out is asked for a number below anything it has ever seen. Anchoring makes the
target roughly stationary, and predictions are converted back to rupees before
anything is scored or served.

**Known-future covariates.** Festive discounts are the largest driver of price
movement in Indian e-commerce, and sale windows are published weeks ahead.
Calendar features are therefore indexed at the *target* date rather than the
origin date, so a forecast made on 1 October for 20 October knows that the 20th
falls inside Diwali week. This was the single largest accuracy gain in the
pipeline.

**Leak-free features.** Every lag, rolling and expanding statistic is computed
per `(model, retailer)` series and shifted by one observation, so no row can
see its own price or any later one. `ml/features.py` is used unchanged at both
training and serving time, so the vector scored in production is the vector the
model was fitted on.

**Capacity scheduled by horizon.** At one week out, most movement is
mean-reverting noise, so that horizon gets a small, heavily penalised model
shrunk toward "no change". At two to four weeks the noise has decayed and the
remaining movement is depreciation and scheduled sales — real structure — so
the model is allowed more capacity.

**Calibrated intervals.** Raw quantile regression was badly overconfident:
40% empirical coverage against a nominal 80%. Conformalised quantile
regression (split-conformal on a held-back recent slice) brings measured
coverage to roughly 76%.

### Pricing recommendations

The recommendation is arithmetic, not a language-model guess. It starts from
the forecast, shades halfway toward a cheaper competitor rather than matching
them, applies a hard margin floor, caps the size of any single move, and
reports the expected demand change at a stated elasticity. Every call returns
the reasoning that produced the number, and identical inputs always produce
identical output.

A language model is optional and does one job: rewriting figures that have
already been computed into prose. It is never asked to produce a price.

---

## Live data collection

The collector scrapes one fixed product page per tracked series, listed in
`collector/targets.json`: the iPhone 15 and 16 (128 GB) and iPhone 17 (256 GB)
on Amazon and Flipkart. Tracking a fixed variant matters: the first version
scraped search-results pages, where the first price was often an advert, an
accessory or a different storage size.

**How a reading is extracted.** Structured data first (schema.org JSON-LD,
then product meta tags), because it exists for search engines and rarely
changes. Retailer CSS selectors are the fallback, newest generation first.
If none of these yields a price, nothing is stored. The old fallback of
taking the first rupee figure on the page is gone.

**How a reading is validated before storage.**
- the price falls inside a plausible band,
- the page title still names the tracked model and storage, which catches a
  URL that now redirects to another product,
- the price has not moved more than 40% since the last reading, which
  catches EMI amounts and exchange-offer prices parsed by mistake.

**How the collector behaves.** It reads and honours `robots.txt`, spaces out
requests to each site with jitter, retries server errors with backoff, and
identifies itself with a configurable user agent. On throttling (429/503) or
a bot-challenge page it stops for that site until the next scheduled run. It
does not rotate proxies, solve CAPTCHAs or disguise itself. Each retailer's
terms of use still apply, and checking them is the operator's responsibility.

**Every run is logged.** Each product gets a result (`ok`, `rejected`,
`blocked`, `throttled`, `disallowed`, `http_error`) with the extraction
method used and a reason. `GET /api/collect/status` shows the last run
product by product, so a stale selector shows up the same day it breaks.

**Three ways to run it:**

| Mode | How | When |
|---|---|---|
| Inside the API | `COLLECT_INTERVAL_MINUTES=240` | A host that stays up (Render starter, Railway, a VPS) |
| GitHub Actions | `.github/workflows/collect.yml`, every six hours, pushes to `/api/collect/ingest` | A free tier that sleeps |
| By hand | `python -m collector.collect --source live` | Testing selectors locally |

Retailers often challenge requests from cloud IP ranges, including GitHub's
runners. If runs keep coming back `blocked`, run the collector from a home
machine on a schedule and push with `--push-to`.

**From synthetic to live models.** `RETRAIN_INTERVAL_HOURS=24` retrains daily.
Until every series has `MIN_TRAINING_DAYS` (60 by default) of live history,
training uses the synthetic bootstrap data. After that it trains on the scraped
prices. The swap happens only after training fully succeeds, and the model
card names the data it was trained on. Forecasts for a series start once it
has about 20 days of readings.

---

## Data

The bootstrap dataset is **synthetic and clearly labelled as such**. Its
launch prices match the tracked variants' Indian launch prices (₹79,900 for
the iPhone 15 and 16, ₹82,900 for the iPhone 17), and it runs from April
2025 to November 2026. It is generated by a documented stochastic price
process in `ml/simulate.py`:

```
price(t) = MSRP
         × depreciation(t)       exponential decay since launch
         × festive_discount(t)   Big Billion Days, Great Indian Festival, Diwali
         × retailer_effect(t)    persistent spread plus undercutting response
         × weekly_effect(t)      day-of-week pattern
         × exp(AR(1) noise)      sticky, not white
```

Every component is a modelling assumption, not a measurement. The purpose is
to exercise and validate the pipeline against a signal that is genuinely
learnable, so the reported metrics mean something.

Live readings land in the same table, so the forecasting, alerting and
pricing code is identical for synthetic and scraped data.

---

## Running it

```bash
git clone <your-fork-url>
cd Real-time-competitor-strategy-tracker
./scripts/bootstrap.sh          # venv, data, training, seeding, tests
source .venv/bin/activate
uvicorn backend.app.main:app --reload
```

Then open <http://localhost:8000/docs>.

Step by step, if you prefer:

```bash
pip install -r requirements-dev.txt
cp .env.example .env
python -m ml.simulate --out data/competitor_prices_synthetic.csv
python -m ml.train --data data/competitor_prices_synthetic.csv
python -m collector.collect --source sample
pytest
```

Collect real prices once, then turn on the schedule:

```bash
python -m collector.collect --source live      # prints a result per product
COLLECT_INTERVAL_MINUTES=240 RETRAIN_INTERVAL_HOURS=24 uvicorn backend.app.main:app
```

Frontend:

```bash
cd frontend
cp .env.example .env.local
npm ci && npm run dev
```

With Docker:

```bash
docker compose up --build
```

---

## Deploying

The API is a stateless container that honours `$PORT`, runs as a non-root
user, and exposes `/health` (liveness) and `/ready` (readiness, checking the
database and model artifacts).

`deploy/render.yaml` is a Render blueprint for both services.
`deploy/railway.json` and `deploy/Procfile` cover Railway and Heroku-style
platforms.

Required in production:

| Variable | Why |
|---|---|
| `JWT_SECRET` | Without it a secret is generated per process, so tokens die on restart and replicas disagree. The app refuses to start in production without it. |
| `CORS_ORIGINS` | Must list the deployed frontend origin. `*` is rejected. |
| `VITE_API_BASE_URL` | Baked in at frontend build time, so changing it needs a rebuild. |

SQLite is used for portability. It is a genuine constraint — single-writer,
and it needs a persistent disk on platforms with ephemeral filesystems. The
data layer is isolated in `backend/app/db.py` behind a small interface, so
moving to Postgres means changing that one module.

---

## Testing

```bash
pytest --cov=ml --cov=backend/app --cov-report=term-missing
```

67 tests covering the scraper (saved retailer pages, block detection,
validation, run logging, token-authenticated ingestion), authentication and
privilege escalation, input validation,
forecast interval ordering, horizon validation, the retailer-label
normalisation that caused the original live-price defect, anti-leakage
guarantees on every lag and rolling feature, margin-floor and move-cap
enforcement, and anomaly classification.

CI additionally regenerates the data, retrains from scratch, and **fails the
build if any horizon stops beating its naive baselines**. It also runs a
secret scan over the full git history.

---

## Architecture

```
ml/                     modelling, independent of the web layer
  simulate.py           documented synthetic price process
  features.py           leak-free feature engineering, shared by train and serve
  train.py              rolling-origin CV, baselines, conformal calibration
  predict.py            inference, reusing the training feature code
  pricing.py            elasticity-based recommendation, anomaly detection

backend/app/
  config.py             environment-driven settings, no secret defaults
  db.py                 schema, indexes, scoped connections
  security.py           bcrypt hashing, JWT issue and verification
  routers/              auth, forecast, live data, catalogue, alerts, assistant, health
  services/alerting.py  change detection and notification
  services/live.py      scheduled collection and retraining

collector/
  targets.json          the product pages to track (edit to add products)
  fetcher.py            robots.txt, per-site pacing, backoff, block handling
  parsers.py            JSON-LD, meta tags, then retailer selectors
  live.py               one run: fetch, parse, validate, store, log
  collect.py            CLI: live scrape, push to a hosted API, or replay sample

frontend/src/lib/api.ts single typed API client
.github/workflows/      CI, and the six-hourly price collection job
```

---

## Engineering notes

What the first version got wrong, and what changed. This section exists
because the debugging is the part of the project worth talking about.

**The headline accuracy figure did not survive a chronological split.** The
original README reported R² = 0.7997. That came from a shuffled
`train_test_split` over features that included `Model_Price_mean`, `_std`,
`_min` and `_max` computed across the entire dataset — test rows included.
Re-evaluated chronologically, the same approach scored R² ≈ 0.05 and **lost to
a group-mean baseline** (MAE ₹22,644 against ₹22,322).

The underlying cause was the data, not the model: the original synthetic set
drew each price as a per-model mean plus large Gaussian noise, with no
autocorrelation, trend or seasonality. Nothing could have beaten an average on
it. That is why the data generator was replaced before the model was.

**Every "current market price" in the dashboard was fabricated.** The scraper
wrote `amazon.in` and `flipkart.com`; the prediction layer filtered for
`Amazon` and `Flipkart`. The filter matched zero rows, `get_latest_current_price`
returned `None`, and the code silently fell back to the model's own output —
which is why `Current_Price` and `ML_Predicted` were byte-identical in every
exported row. Labels are now canonicalised on write and on read, with tests.

**The task framing made the problem trivial.** Predicting the price of the row
being scored, when the scraper already knows it, let persistence score a 1.1%
error that nothing could beat. The task is now forecasting 7 to 30 days ahead,
which is the question a repricing decision actually needs.

**A live Gmail app password was committed in plain text** as a module constant
in `refresh_scraper.py`, so every clone carried working credentials. All
secrets now come from the environment, `.env` is gitignored, and CI scans the
full history for credentials.

**Passwords were unsalted SHA-256 and there were no sessions.** SHA-256 is
built to be fast, which is the opposite of what a password hash needs, and
unsalted digests fall to a single rainbow table. The login endpoint also took
an `isAdmin` flag from the request body, and nothing re-verified identity after
login. Now: bcrypt, signed JWTs, and server-side role checks on every admin
route.

**Three other structural problems.** Users and scraped prices lived in separate
database files that could not see each other. A single module-level SQLite
connection with `check_same_thread=False` was shared across FastAPI's thread
pool. `requirements.txt` was a directory, so installing dependencies failed.
And a 54 MB database plus a 14 MB model pickle were committed, making the
repository ~146 MB to clone — both are now generated and gitignored.

---

## Limitations

- The bundled data is synthetic. Reported accuracy describes performance on a
  process whose structure is known, which is an upper bound on what to expect
  from live retail data.
- SQLite is single-writer and needs a persistent disk.
- Retailer pages change and retailers block automated clients, especially
  from cloud IP ranges. The run log shows when that happens; the fix is
  usually a selector update in `collector/parsers.py` or running the
  collector from a different network.
- Demand elasticity defaults to −1.8 from published consumer-electronics
  estimates, not from this system's own conversion data. It is a parameter,
  and the recommendation surfaces it rather than hiding it.
