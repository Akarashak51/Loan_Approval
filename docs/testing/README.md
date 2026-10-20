# Testing

## Backend (`tests/backend/`, pytest)

    cd backend
    pip install -r requirements.txt
    pytest ../tests/backend -v

Covers: registration (including that public signup can never
self-assign `loan_officer`/`admin`), login, JWT-protected routes,
role-based access control, application payload validation.

## ML (`tests/ml/`, pytest)

    cd ml
    pip install -r ../backend/requirements.txt   # shares the same ML deps
    pytest ../tests/ml -v

Covers: feature config consistency (no numeric/categorical overlap,
immutable features stay immutable), preprocessing pipeline fit/transform
(including unseen categories), the plain-English explanation engine, the
SHAP-vs-LIME comparison logic, and fairness metric calculation against a
synthetic labeled set (skipped automatically if `fairlearn` isn't installed).

These run against synthetic data matching the schema, not the real
downloaded dataset -- so they work in CI without needing internet access
or a trained model.

## Frontend (`tests/frontend/`, Vitest)

    cd frontend
    npm install
    npm run test

Currently covers the feature-config consistency that the Application
form and validation depend on. Component-level tests (form validation,
mocked API integration, result rendering) are the natural next addition.
