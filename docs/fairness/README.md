# Fairness

## Method

`ml/fairness/fairness_analyzer.py` uses Fairlearn's `MetricFrame` over
the held-out test set + predictions saved by `train.py`
(`ml/data/processed/test_with_predictions.csv`), grouped by a `sex`
proxy attribute.

Metrics computed: accuracy, selection rate (~approval rate), true
positive rate, false positive rate, false negative rate per group; plus
`demographic_parity_difference` and `equalized_odds_difference` overall.

## Protected attribute caveat

The source dataset encodes sex jointly with marital status
(`personal_status_sex`), and does so asymmetrically -- male categories
are split by marital status, female categories are collapsed into one.
`sex` is *derived* from this field (see `ml/data/download_dataset.py:derive_sex`).
This is a real, documented limitation: findings on this attribute
describe a proxy, not a clean self-reported field. The admin dashboard
surfaces this caveat directly (`protected_attribute_caveat` in the API
response) rather than hiding it.

## Interpretation, not verdicts

A disparity is flagged when `|difference| >= 0.10` (see
`DISPARITY_FLAG_THRESHOLD` in `fairness_analyzer.py`) -- this threshold
is documented and adjustable, not an industry-standard cutoff. The
dashboard never states "the model is fair" or "the model is biased";
it reports the numbers and says whether they cross the documented
threshold, consistent with fairness being context-dependent (spec
section 47).

## Governance gate

`ml/fairness/governance_gate.py` runs after each model's held-out Fairlearn
audit. By default, both absolute demographic-parity difference and absolute
equalized-odds difference must be at most `0.10`. These defaults require real
regulatory and lending-policy review before production use. A failed gate
prevents that training run from overwriting the currently served model and is
recorded with the model version in `governance_checks`.

The income model audits the documented derived `sex` proxy. The synthetic
transaction model audits an `account_age_band` group because its demo data
does not include a self-reported protected attribute; this is a governance
signal, not a legal fairness determination.

Both predictor loaders enforce the stored governance result at inference time:
an artifact with a failed gate is refused and the currently served artifact is
left unchanged by training.
