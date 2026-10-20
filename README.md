# GlassBox

[![CI](https://github.com/ri-dev-it/GlassBox/actions/workflows/ci.yml/badge.svg)](https://github.com/ri-dev-it/GlassBox/actions/workflows/ci.yml)

**An explainable, self-auditing AI Risk Manager for Razorpay Capital.**

GlassBox scores merchant and applicant risk, explains every decision in
plain language, tells rejected or borderline applicants exactly what
would change the outcome, audits itself for fairness before it's allowed
to serve predictions, detects fraud patterns in real time, and shows
which capital tier a merchant qualifies for â€” including how far away
they are from the next one.

> Built for the **Razorpay AI Buildathon 2026 â€” AI Risk Manager track**.

---

## Why this exists

Razorpay Capital underwrites merchants using their own transaction
data â€” GMV, refund rate, chargeback rate, payment success rate â€” not
just static bureau data. But that kind of behavioral underwriting is
usually a black box: a merchant gets a yes/no with no way to see why, no
path to improve, and no visibility into whether the system is treating
similar merchants fairly.

**GlassBox is built around one idea: every decision should be
explainable, actionable, and auditable â€” and the system should manage
the risk of its own model being wrong, unfair, or misunderstood, not
just the applicant's risk.**

---

## What it does

### Core risk assessment
- **Predicts** risk two ways: a traditional income/credit-score model
  (Logistic Regression vs. XGBoost, selected on held-out F1/ROC-AUC) and
  a **transaction-behavior model** using GMV trend, payment success
  rate, refund rate, chargeback rate, customer concentration, and order
  volume volatility â€” the kind of signal Razorpay Capital actually has
  access to that a traditional bank doesn't
- **Decides in three bands, not a binary cutoff** â€” APPROVE / REVIEW /
  DECLINE, calibrated against configurable risk thresholds instead of a
  flat probability cutoff, so borderline cases route to human review
  instead of a hard yes/no
- **Explains** every decision with SHAP (local + global) and LIME, with
  an explicit view of where the two methods agree or disagree

### Trust and recourse
- **Shows recourse** â€” DiCE-generated counterfactuals ("what would need
  to change") that respect immutable and protected features
- **Grounded AI explanations** â€” an LLM turns raw SHAP output into a
  plain-English explanation, but only after a validation check confirms
  the explanation actually references the model's real top drivers; if
  it can't be verified, the system falls back to a deterministic
  template instead of ever showing an ungrounded explanation
- **Audits itself for fairness** â€” a Fairlearn-based audit across
  protected groups (selection rate, TPR/FPR, demographic parity,
  equalized odds), with an explicit disparity threshold and a documented
  proxy-attribute caveat
- **Governance gate** â€” a model version that fails its own fairness or
  calibration thresholds is not allowed to serve predictions; the system
  keeps the last known-good governed model in place and flags the
  failure clearly instead of silently deploying a worse one

### Risk detection and portfolio view
- **Fraud pattern detection** â€” a transparent, rules-based detector that
  flags refund spikes, chargeback clusters, order-velocity anomalies,
  and GMV-refund mismatches in a merchant's transaction history, each
  flag human-readable and auditable, not a black-box fraud score
- **Applicant document verification** â€” uploads PDF/images, extracts text/OCR,
  classifies document slots, checks identity and arithmetic, parses bank
  transactions, and records an auditable verdict that can require decision review.
  Legacy merchant declaration checks remain a separate simulated feature.
- **Tier-based gap calculator** â€” for merchants not yet qualifying for a
  higher Razorpay Capital tier, shows exactly how much their GMV trend,
  refund rate, or customer concentration would need to improve, ranked
  by how close they already are
- **Portfolio exposure dashboard** â€” an aggregate view across all
  merchants: how many sit in each tier, total estimated capital
  exposure per tier, and which risk signal most commonly blocks tier
  advancement across the whole portfolio

### Visibility
- **Precision, recall, F1, and ROC-AUC** surfaced clearly on the admin
  dashboard for both models, side by side â€” not buried in a notebook

---

## Important notes (read before trusting any number here)

- SHAP/LIME explain model *behavior*; they do not prove causation.
- Counterfactuals describe what would change the *model's* prediction,
  not a guarantee of real-world approval.
- Fairness metrics are reported with an explicit disparity threshold and
  a documented proxy-attribute caveat â€” never as a blanket "the model is
  fair."
- The transaction-behavior dataset is **synthetic**, generated to
  reflect realistic relationships between merchant signals and risk â€”
  it is not real Razorpay merchant data.
- Razorpay Capital tier thresholds and portfolio exposure figures are
  **illustrative/simulated for demo purposes**, not real Razorpay
  Capital policy.
- Applicant document verification uses real parsing and optional OCR, but is
  **heuristic consistency checking**, not government or bank authentication.
  Merchant declaration checks still use manually entered values.
- Grounded AI explanations are clearly labeled "AI-generated" vs.
  "system-generated" depending on whether the LLM's output passed the
  grounding check â€” the system never presents an unverified explanation
  as if it were verified.
- No fabricated data, predictions, explanations, or fairness metrics
  anywhere â€” every number comes from real computation on real, cited, or
  clearly-labeled-synthetic data.

---

## Architecture

```
project-root/
â”œâ”€â”€ frontend/    React + TypeScript + Vite + Tailwind CSS
â”œâ”€â”€ backend/     Python + Flask REST API (routes -> services -> ML/DB)
â”œâ”€â”€ ml/          Models, training, explainability, fairness, decisioning,
â”‚                fraud detection, eligibility/gap logic, document
â”‚                verification, grounded explanation layer
â”œâ”€â”€ database/    MySQL schema + migrations + seed scripts
â”œâ”€â”€ tests/       Backend (pytest), ML (pytest), frontend (Vitest)
â””â”€â”€ docs/        Architecture, API, database, ML, explainability,
                 fairness, fraud detection, portfolio, testing
```

See `docs/` for the deep-dive on each area.

## Technology stack

| Layer    | Stack                                                                     |
| -------- | ------------------------------------------------------------------------- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router, Axios, Recharts      |
| Backend  | Python, Flask, Flask-CORS, Flask-SQLAlchemy, Flask-Bcrypt, PyJWT          |
| ML       | Pandas, NumPy, scikit-learn, XGBoost, SHAP, LIME, DiCE, Fairlearn, Joblib |
| AI       | Optional OpenAI-compatible chat API (grounded explanation with deterministic fallback) |
| Database | MySQL                                                                     |

---

## Installation and commands

### Prerequisites

Use Python 3.11 (the pinned ML stack is not validated on Python 3.14), Node.js
18+, and npm. MySQL 8 is optional for local development because the backend
defaults to SQLite when `DATABASE_URL` is unset. MySQL is needed only when you
choose it as the configured database. Training the individual credit model
downloads the public UCI dataset and therefore needs internet access. An
OpenAI-compatible `OPENAI_API_KEY` is optional; grounded explanations use a
deterministic template when it is not configured. Keep the key in
`backend/.env`, never in the frontend environment.

### 1. Configure the backend

From the repository root, copy `.env.example` to `backend/.env` and set a real
`SECRET_KEY` and `AADHAAR_HASH_KEY`. For SQLite, remove or comment out the sample
`DATABASE_URL` line so the backend uses `backend/xai_loan.db`. To use MySQL,
create the database and set `DATABASE_URL` to a `mysql+pymysql://...` URL. Do not
commit `backend/.env`.

PowerShell:

```powershell
Copy-Item .env.example backend/.env
python -c "import secrets; print(secrets.token_hex(32))"
```

Generate the command twice and use the two values for `SECRET_KEY` and
`AADHAAR_HASH_KEY`. Set `OPENAI_API_KEY` only if you want the optional grounded
LLM explanation path.

### 2. Install Python dependencies

PowerShell (from the repository root):

```powershell
py -3.11 -m venv backend/.venv
backend/.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

macOS/Linux:

```bash
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

Digital PDFs work without system OCR. Scanned PDFs require Tesseract on `PATH`
(`tesseract --version`); set `TESSERACT_CMD` in `backend/.env` if needed.
PDFium is supplied by the Python dependency; Poppler is not required. Uploads
are stored under `backend/private_uploads` with a 5 MB per-file limit. Aadhaar
extractions retain a masked summary, not the full identity number. Restart Flask
after changing `backend/.env`.

### 3. Initialize the database

SQLite development creates tables when the Flask app starts. For an existing
Alembic-managed MySQL database, run from the repository root:

```powershell
python -m flask --app backend.app db upgrade
```

If Flask cannot resolve the app package from the root, run the equivalent from
`backend/`:

```powershell
python -m flask --app app db upgrade
```

Do not stamp an existing database without verifying that its schema matches
the migration revision. See [database documentation](docs/database/README.md).

### 4. Train both models (required for prediction endpoints)

Run these from the repository root. The individual model downloads the UCI
German Credit dataset; the transaction model generates clearly labeled
synthetic data.

```powershell
python ml/data/download_dataset.py
python ml/training/train.py
python ml/training/train_transaction_model.py
```

Both governed model artifacts and their metadata are written under
`ml/models/saved/`. The binary artifacts and downloaded CSV are ignored by Git.
If governance rejects a trained model, the script reports the failed checks
and does not activate that model. Prediction endpoints return an explicit
unavailable response until a suitable artifact exists.

### 5. Start the services

Start the backend in one terminal from the repository root:

```powershell
backend/.venv/Scripts/Activate.ps1
python backend/run.py
```

The API listens on `http://localhost:5000`; check API reachability with
`Invoke-RestMethod http://localhost:5000/api/health`. This endpoint checks the
HTTP service only, not database or model readiness.

Start the frontend in a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to the backend on port 5000.
For production frontend verification, use `npm run build`; deployment must
serve the built `frontend/dist` files and route API calls to Flask.

Create a local first admin account after the database is available:

```powershell
python database/seeds/seed_admin.py admin@example.com "Admin Name" "a-strong-password"
```

### 6. Current validation commands

Run from the repository root with the backend virtual environment activated:

```powershell
python -m compileall -q backend ml tests
python -m pytest tests/backend -v
python -m pytest tests/ml -v
cd frontend
npm run lint
npm run build
npm run test -- --pool=forks --maxWorkers=1 --minWorkers=1
npm audit
```

The remaining npm advisories in the checked lockfile require major upgrades
(Vite/Vitest, Tailwind CSS, and React Router). `npm audit fix` applies compatible
patch updates, but does not resolve those breaking-major advisories; complete
and verify the framework migrations before treating the frontend dependency
tree as advisory-free.

The optional browser upload smoke test needs Chrome and Playwright installed in
the active Python environment, plus the frontend dependencies:

```powershell
python tests/e2e/document_upload_smoke.py
```

See [verification documentation](docs/document-verification.md),
[demo scenarios](DEMO.md), and [testing documentation](docs/testing/README.md)
for feature-specific details.

### Verification state (2026-10-13)

Frontend lint and production build pass; all 25 frontend tests pass. Python
bytecode compilation passes. Backend and ML pytest suites could not be run in
the review environment: it has Python 3.14 with no pytest installed, while this
project targets Python 3.11. The checkout has no `backend/.env` or active
`model.joblib` / `transaction_model.joblib` artifacts, so a live database
connection and end-to-end prediction could not be verified here. Run the setup
and training commands above before expecting live predictions. `npm audit`
reports 15 remaining advisories in dependencies whose available fixes require
major framework upgrades.

---
## Why "AI Risk Manager"

Razorpay's own framing for this track asks for a working detector,
verifier, or auto-responder for one class of loss, evaluated on measured
precision and recall. GlassBox is a working risk detector for both
traditional and transaction-behavior-based underwriting â€” extended with
the parts that make a risk model trustworthy enough to actually deploy:

- **Detection** â€” two working risk models plus a dedicated fraud
  pattern detector, all reporting real precision/recall/AUC
- **Policy** â€” three-band decisioning instead of a hard cutoff
- **Explanation** â€” SHAP/LIME/DiCE plus a grounded, hallucination-checked
  plain-English layer
- **Self-audit** â€” a fairness audit with a governance gate that blocks
  its own bad models
- **Recourse** â€” counterfactuals and a tier-gap calculator that show a
  real path forward, not just a rejection

That's the actual difference between a model that predicts risk and a
system that *manages* it.

---

## About
