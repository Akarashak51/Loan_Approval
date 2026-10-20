# Architecture

## Layers

```
Frontend (React + TS)
   |  Axios
   v
Flask routes  ->  Service layer  ->  ML package (ml/) / MySQL (SQLAlchemy)
```

Routes never contain business logic -- they validate input, call a
service function, and return JSON. Services orchestrate the ML package
and database models. The `ml/` package is a standalone, backend-agnostic
Python package that knows nothing about Flask; `backend/app/services/ml_service.py`
is the only file that imports from it.

## Request flow: submitting a loan application

1. Frontend `Application` page collects form data (validated client-side
   against `frontend/src/utils/featureConfig.ts`).
2. `POST /api/predict` -> `app/routes/predictions.py` validates server-side
   against `app/schemas/application_schema.py` (mirrors the same feature config).
3. `app/services/application_service.py` orchestrates:
   - `ml_service.predict_application()` -> loads the saved model, predicts.
   - `ml_service.get_shap_explanation()` / `get_lime_explanation()`.
   - `ml_service.get_counterfactual()`.
   - Persists `Application`, `Prediction`, `Explanation` (x2), `Counterfactual` rows.
4. Response includes prediction + both explanations + comparison + counterfactual
   in one payload, so the Results page can render everything without extra round-trips.

## Why one saved pipeline object

`ml/training/train.py` saves a single `sklearn.Pipeline` containing both
the fitted preprocessor and the fitted classifier. `ml/prediction/predictor.py`
loads it once (`lru_cache`) and calls `.predict_proba()` directly on raw
applicant data -- preprocessing is never reimplemented at serving time,
eliminating train/serve skew (spec sections 12-13).

## Database relationships

```
User --1:N--> Applicant --1:N--> Application --1:1--> Prediction
                                                          |--1:N--> Explanation (shap, lime)
                                                          |--1:N--> Counterfactual
```
