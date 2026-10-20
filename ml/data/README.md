# Dataset: Statlog (German Credit Data)

**Source:** UCI Machine Learning Repository
https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data

**How to obtain it:** run `python data/download_dataset.py` from inside
`ml/` (requires an internet connection). This downloads the original
`german.data` file, applies the UCI codebook's readable labels, and
writes `data/raw/german_credit.csv`. Nothing is fabricated or
synthesized -- every row is a real record from the published dataset.

## Why this dataset

- 1000 applicant records, 20 features -- enough to train and evaluate a
  real model, small enough to iterate on quickly.
- Binary target: good credit risk vs bad credit risk (`credit_risk`
  column: 1 = good, 0 = bad), a direct analogue of approve/reject.
- Financially meaningful features: checking/savings account status,
  credit history, credit amount, duration, employment history,
  existing credits, housing, job, etc.
- Mix of numeric and categorical features -- exercises SHAP, LIME, and
  DiCE across both types.
- Includes a `personal_status_sex` field and `age`, which we use for
  the Fairlearn audit (Milestone 11).

## Fields

| Column | Type | Description |
|---|---|---|
| checking_account_status | categorical | Status of existing checking account |
| duration_months | numeric | Loan duration in months |
| credit_history | categorical | Credit history |
| purpose | categorical | Purpose of the loan |
| credit_amount | numeric | Loan amount (DM) |
| savings_account | categorical | Savings account/bonds balance |
| employment_since | categorical | Present employment duration |
| installment_rate_percent | numeric | Installment rate as % of disposable income |
| personal_status_sex | categorical | Joint personal status + sex code (see caveat below) |
| other_debtors_guarantors | categorical | Other debtors / guarantors |
| present_residence_since | numeric | Years at present residence |
| property | categorical | Property type |
| age | numeric | Age in years |
| other_installment_plans | categorical | Other installment plans |
| housing | categorical | Housing situation |
| existing_credits_count | numeric | Number of existing credits at this bank |
| job | categorical | Job category |
| num_dependents | numeric | Number of people financially dependent |
| telephone | categorical | Has registered telephone |
| foreign_worker | categorical | Foreign worker status |
| **credit_risk** | **target (0/1)** | 1 = good credit risk, 0 = bad credit risk |
| sex | **derived proxy** | Split out of `personal_status_sex`; see caveat |

## Data quality notes

- No missing values in the original UCI release.
- Class distribution is imbalanced (~70% good / ~30% bad) -- this is
  documented and accounted for in model evaluation (we report
  precision/recall/F1/ROC-AUC, not just accuracy).
- All fields are encoded as short codes (e.g. `A11`) in the raw file;
  `download_dataset.py` decodes them to readable text per the UCI
  codebook (`german.doc`).

## Protected / proxy attribute caveat

`personal_status_sex` encodes marital status and sex jointly (e.g.
`"female:divorced/separated/married"` is one category with no
single/married distinction, while male categories are split further).
We derive a `sex` column from it for the fairness dashboard, but this
is a **proxy attribute inferred from a flawed joint encoding**, not a
clean self-reported field. Fairness results based on it should be read
as indicative of a known dataset limitation, not a definitive
real-world fairness claim. See `docs/fairness/README.md`.
