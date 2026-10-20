"""Governance gate tests for both income and transaction model paths."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from fairness.governance_gate import check_governance


def test_unfair_income_metrics_fail_governance():
    result = check_governance({"disparity_metrics": {"demographic_parity_difference": 0.21, "equalized_odds_difference": 0.03}})

    assert result["passed"] is False
    assert any("demographic parity" in failure for failure in result["failed_checks"])


def test_unfair_transaction_metrics_fail_governance():
    result = check_governance({"disparity_metrics": {"demographic_parity_difference": 0.04, "equalized_odds_difference": 0.25}})

    assert result["passed"] is False
    assert any("equalized odds" in failure for failure in result["failed_checks"])