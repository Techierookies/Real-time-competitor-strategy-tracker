# Migration guide

> **Status on the `v2-live-tracker` branch:** steps 2, 3 and 5 below are
> already done. The old backend, scrapers, databases, exports and pickles
> are removed, notebooks are kept in `notebooks/legacy/`, and every frontend
> page uses `frontend/src/lib/api.ts`. What is still yours to do:
> **step 0** (revoke the leaked password and decide on scrubbing history),
> **step 4** (optional import of old scraped rows), and the **step 7**
> checklist. For live collection, see "Live data collection" in the README.

---

## Step 0 — Rotate the leaked credential first

`backend/refresh_scraper.py` contains a working Gmail app password for
`techierookies0105@gmail.com`. It is public, it is in git history, and it is in
every teammate's fork.

1. Go to <https://myaccount.google.com/apppasswords> and **revoke** it now.
2. Tell your teammates — their forks carry the same credential.
3. Do this before anything else in this guide. Deleting the file does not help:
   git history keeps it.

Removing it from history as well:

```bash
pip install git-filter-repo
git filter-repo --path backend/refresh_scraper.py --invert-paths
git push origin --force --all
```

Force-pushing rewrites history. If that feels risky, the alternative is a fresh
repository with no history — which is often the better option here anyway,
since it also drops the 146 MB of committed binaries.

---

## Step 1 — Decide: fresh repository or in-place

**Fresh repository (recommended).** Your current repo is ~146 MB because a
54 MB database, a 14 MB model pickle and a 13 MB CSV are committed. Recruiters
clone repositories; a 146 MB clone of mostly binary data is a poor first
impression, and it is the simplest way to be certain the credential is gone.

```bash
mkdir competitor-strategy-tracker && cd competitor-strategy-tracker
git init
# copy the files from this bundle in, then:
git add . && git commit -m "Competitor strategy tracker"
```

**In place.** Follow steps 2–6 and commit normally. Still do step 0.

---

## Step 2 — Files to delete

These are replaced:

```
README.md                          # unresolved merge conflict + Vite boilerplate
requirements.txt/                  # a directory, so pip install -r fails
backend/main.py                    # replaced by backend/app/
backend/database.py
backend/admin_routes.py
backend/refresh_scraper.py         # contains the leaked credential
backend/model/llm.py
backend/model/chatbot.py
backend/model/train_model.py       # entirely commented out
data_collection/refresh_scraper.py
data_collection/scraper.py
data_collection/crawlai_scraper.py
data_collection/check_prices.py
```

Delete from version control (regenerate instead):

```
competitor_tracker.db              # 54 MB
backend/competitor_tracker.db      # 13 MB
iphone.db                          # 0 bytes
raw_scrapes_export.csv             # 13 MB
raw_scrapes_export.json            # 13 MB
exports/combined_raw_export.html   # 4.5 MB
AI-ML/*.pkl                        # 14 MB model pickle
backend/model/*.pkl
```

Keep `AI-ML/*.ipynb` if you like — notebooks are reasonable evidence of
exploratory work. Move them to `notebooks/` and say in the README that the
production path is `ml/`, not the notebooks.

---

## Step 3 — Copy in the new files

```
ml/                      simulate, features, train, predict, pricing
backend/app/             config, db, security, schemas, deps, main, routers, services
backend/tests/           conftest and the test suite
collector/collect.py
frontend/src/lib/api.ts
frontend/Dockerfile, frontend/nginx.conf, frontend/.env.example
scripts/bootstrap.sh
deploy/                  render.yaml, railway.json, Procfile
.github/workflows/ci.yml
Dockerfile, docker-compose.yml
requirements.txt, requirements-dev.txt, pytest.ini
.env.example, .gitignore
README.md, MIGRATION.md
```

---

## Step 4 — Bring your real scraped data across

Your root `competitor_tracker.db` has 102 rows in `dynamic_info`. Much of it is
unusable — Flipkart prices are a constant `10000.0` and Amazon rows are largely
`NaN` — but the migration validates as it goes and tells you what it rejected.

```bash
python - <<'PY'
import sqlite3, sys
sys.path.insert(0, ".")
from backend.app.config import get_settings
from backend.app.db import Database
from ml.features import normalise_model, normalise_source

old = sqlite3.connect("competitor_tracker.db")
old.row_factory = sqlite3.Row

db = Database(get_settings().sqlite_path)
db.initialise()

moved = skipped = 0
for row in old.execute("SELECT * FROM dynamic_info"):
    price = row["price"]
    # The same validation the collector applies: a constant 10000.0 is a
    # parsing failure, not a price, and must not enter the training data.
    if price is None or not (10_000 < float(price) <= 400_000):
        skipped += 1
        continue
    moved += db.record_observation({
        "model": normalise_model(row["model"]),
        "source": normalise_source(row["site"]),
        "price": float(price),
        "rating": row["rating"],
        "review_count": row["review_count"],
        "review_text": None,
        "url": row["url"],
        "observed_at": row["extracted_at"],
    })

print(f"migrated {moved}, skipped {skipped} unusable rows")
PY
```

Your users table migrates too, but the password hashes do not: they are
unsalted SHA-256 and cannot be converted to bcrypt without the original
passwords. `verify_password` fails closed on an unrecognised hash format, so
legacy accounts simply cannot log in. Have the handful of real users sign up
again, or insert them manually with `hash_password`.

---

## Step 5 — Update the frontend

Twelve components hardcode `http://localhost:8000` or `http://127.0.0.1:8000`.
Those are also two different CORS origins, so they fail independently. Replace
each `fetch` with the shared client.

Before:

```ts
const res = await fetch("http://localhost:8000/api/admin_dashboard");
const data = await res.json();
```

After:

```ts
import { api } from "@/lib/api";
const data = await api.accuracy();
```

Files to update: `contexts/AuthContext.tsx`, `components/Layout/ChatWidget.tsx`,
`components/Layout/UploadModel.tsx`, `pages/admin/AdminDashboard.tsx`,
`pages/admin/AdminProducts.tsx`, `pages/admin/AdminReviews.tsx`.

Endpoint changes to apply:

| Old | New |
|---|---|
| `POST /login` | `POST /api/auth/login` (no `isAdmin` field) |
| `POST /signup` | `POST /api/auth/signup` (no `role` field) |
| `POST /api/chatbot` | `POST /api/assistant` |
| `GET /api/admin_dashboard` | `GET /api/accuracy` and `GET /api/model-card` |
| `GET /api/store-products` | `GET /api/products` (now paginated) |
| `POST /api/store-products/add` | `POST /api/products` |
| `PUT /api/store-products/{id}/update` | `PATCH /api/products/{id}` |
| `DELETE /api/store-products/{id}` | `DELETE /api/products/{id}` |

`AuthContext` should store `access_token` via `setToken()` from the client
rather than keeping a user object in `localStorage`. All admin requests now
need the bearer header, which the client attaches automatically.

---

## Step 6 — Verify

```bash
./scripts/bootstrap.sh
```

Expect: data generated, three horizons trained with every one beating its
baselines, roughly 4,800 observations seeded, and 46 tests passing. Then:

```bash
uvicorn backend.app.main:app --reload
curl -s localhost:8000/health
curl -s -X POST localhost:8000/api/forecast \
  -H 'Content-Type: application/json' \
  -d '{"model":"iPhone 17","source":"amazon.in","horizon_days":30}'
```

The second call is the regression test for the original defect: `amazon.in`
must resolve to `Amazon` and return a real forecast.

---

## Step 7 — Before you share the link

- [ ] Gmail app password revoked
- [ ] `.env` is gitignored and not committed
- [ ] No `.db` or `.pkl` files tracked (`git ls-files | grep -E '\.(db|pkl)$'` is empty)
- [ ] README has no `<<<<<<< HEAD` markers
- [ ] CI badge is green
- [ ] Deployed API answers `/health`, and `/docs` loads
- [ ] A screenshot or short clip of the dashboard is in the README — most
      reviewers will not clone and run it

## Presenting this

Lead with the diagnosis, not the stack. "I found our reported R² of 0.80 came
from a shuffled split on leaky features; under a chronological split it lost to
a mean baseline, so I rebuilt the evaluation harness and reframed the task as
multi-horizon forecasting" is a far stronger opening than a list of libraries.
Interviewers rarely hear candidates volunteer that their own previous numbers
were wrong, and finding it yourself is the signal.

Keep the attribution accurate: team project, you led it, these enhancements are
yours. That is both honest and more impressive than implying you wrote the
original alone.
