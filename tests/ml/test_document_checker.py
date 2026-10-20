"""Tests for simulated manual document consistency checks."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from verification.document_checker import check_document_consistency


def test_consistent_declared_values():
    result = check_document_consistency(
        {"gst_reported_monthly_revenue": 100000, "bank_statement_monthly_inflow": 80000},
        {"actual_monthly_gmv": 100000, "actual_monthly_inflow": 80000},
    )

    assert result == {"consistent": True, "mismatches": []}


def test_mismatched_values_report_exact_percentages():
    result = check_document_consistency(
        {"gst_reported_monthly_revenue": 65000, "bank_statement_monthly_inflow": 125000},
        {"actual_monthly_gmv": 100000, "actual_monthly_inflow": 100000},
    )

    assert result["consistent"] is False
    assert [(item["field"], item["discrepancy_pct"]) for item in result["mismatches"]] == [
        ("gst_reported_monthly_revenue", 35.0),
        ("bank_statement_monthly_inflow", 25.0),
    ]