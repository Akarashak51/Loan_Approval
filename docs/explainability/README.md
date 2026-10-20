# Explainability

## SHAP (`ml/explainability/shap_explainer.py`)

Uses `shap.Explainer` wrapping the full pipeline's `predict_proba`, so it
works identically whether the final model is Logistic Regression,
XGBoost, or RandomForest -- no per-model branching, no hardcoded values.
`local_shap_explanation()` explains one applicant; `global_shap_importance()`
computes mean |SHAP value| across a sample, powering the admin dashboard's
"what generally influences the model?" view.

## LIME (`ml/explainability/lime_explainer.py`)

`LimeTabularExplainer` operating in the raw feature space, using the
pipeline's `predict_proba` as the black-box function -- so LIME and SHAP
explain the exact same served model, not two different representations of it.

## SHAP vs LIME comparison (`ml/explainability/comparison.py`)

Compares each method's top-5 features for the *same* applicant and
reports agreement / direction-disagreement / method-exclusive features
**without forcing alignment**. SHAP (game-theoretic Shapley values) and
LIME (local linear surrogate) are different methodologies and can
legitimately disagree -- the UI presents this as expected, not as an error.

## Plain-English engine (`ml/explainability/explanation_engine.py`)

Converts `(feature, value, contribution)` tuples into sentences using a
magnitude threshold (strongly/moderately/slightly) and direction
(toward approval/rejection) -- generated fresh from the real contribution
values every time, never hardcoded per-applicant text.

## What this does NOT claim

SHAP and LIME describe which inputs the model weighted, and how much --
they do not establish causation. Counterfactuals (`ml/counterfactual/`)
describe what would change the *model's* output, not a guarantee of a
real bank approving a real loan. Both the API responses and the UI say
this explicitly (see the Results page's probability disclaimer and the
counterfactual `message` field).
