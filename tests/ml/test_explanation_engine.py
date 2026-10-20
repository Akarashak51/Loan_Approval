"""
Tests for the plain-English explanation engine and SHAP/LIME comparison
logic -- pure-Python, no ML libraries required, so always runnable.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from explainability.explanation_engine import explain_feature, generate_summary
from explainability.comparison import compare_explanations


def test_explain_feature_mentions_direction():
    sentence = explain_feature("Credit Utilization", "78%", -0.12, "REJECTED")
    assert "toward rejection" in sentence
    assert "strongly" in sentence  # |contribution| >= 0.08


def test_explain_feature_positive_direction():
    sentence = explain_feature("Savings Account", ">= 1000 DM", 0.05, "APPROVED")
    assert "toward approval" in sentence


def test_generate_summary_includes_confidence_disclaimer():
    contributions = [
        {"label": "Credit History", "value": "critical account", "contribution": -0.15, "direction": "negative"},
        {"label": "Age", "value": 45, "contribution": 0.02, "direction": "positive"},
    ]
    summary = generate_summary(contributions, "REJECTED", 0.30)
    assert "not a guarantee" in summary
    assert "Credit History" in summary


def test_compare_explanations_detects_agreement():
    shap_results = [
        {"feature": "credit_amount", "label": "Loan Amount", "contribution": -0.1, "direction": "negative"},
    ]
    lime_results = [
        {"feature": "credit_amount", "label": "Loan Amount", "contribution": -0.08, "direction": "negative"},
    ]
    result = compare_explanations(shap_results, lime_results)
    assert len(result["agreement"]) == 1
    assert len(result["direction_disagreement"]) == 0


def test_compare_explanations_detects_direction_disagreement():
    shap_results = [
        {"feature": "age", "label": "Age", "contribution": 0.05, "direction": "positive"},
    ]
    lime_results = [
        {"feature": "age", "label": "Age", "contribution": -0.03, "direction": "negative"},
    ]
    result = compare_explanations(shap_results, lime_results)
    assert len(result["direction_disagreement"]) == 1
    assert len(result["agreement"]) == 0


def test_compare_explanations_never_forces_alignment():
    """SHAP-only and LIME-only top features must be reported, not hidden."""
    shap_results = [{"feature": "a", "label": "A", "contribution": 0.1, "direction": "positive"}]
    lime_results = [{"feature": "b", "label": "B", "contribution": 0.1, "direction": "positive"}]
    result = compare_explanations(shap_results, lime_results)
    assert result["shap_only_top_features"] == ["A"]
    assert result["lime_only_top_features"] == ["B"]
