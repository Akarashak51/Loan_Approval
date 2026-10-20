"""
Tests the fairness metric calculation logic against a small synthetic
labeled dataset (not the real test set -- this just verifies the
Fairlearn wiring computes correctly, independent of any trained model).
Requires the `fairlearn` package (see requirements.txt); skipped if
unavailable so the rest of the suite can still run.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

import pandas as pd
import pytest

fairlearn = pytest.importorskip("fairlearn")

from fairness.fairness_analyzer import run_fairness_analysis, DISPARITY_FLAG_THRESHOLD
import config as ml_config


@pytest.fixture
def synthetic_test_set(tmp_path, monkeypatch):
    # Deliberately biased synthetic data: group A always approved, group B never.
    rows = []
    for i in range(20):
        rows.append({"credit_risk": 1, "prediction": 1, "sex": "male"})
    for i in range(20):
        rows.append({"credit_risk": 1, "prediction": 0, "sex": "female"})
    df = pd.DataFrame(rows)

    path = tmp_path / "test_with_predictions.csv"
    df.to_csv(path, index=False)
    monkeypatch.setattr(ml_config, "TEST_SET_WITH_PREDICTIONS", str(path))
    monkeypatch.setattr(
        sys.modules["fairness.fairness_analyzer"], "TEST_SET_WITH_PREDICTIONS", str(path)
    )
    return path


def test_fairness_flags_obvious_disparity(synthetic_test_set):
    report = run_fairness_analysis()
    assert abs(report["disparity_metrics"]["demographic_parity_difference"]) >= DISPARITY_FLAG_THRESHOLD
    assert any("Potential disparity" in line for line in report["interpretation"])


def test_fairness_report_never_claims_absolute_fairness(synthetic_test_set):
    report = run_fairness_analysis()
    full_text = " ".join(report["interpretation"]) + report["disclaimer"]
    assert "the model is fair" not in full_text.lower()
