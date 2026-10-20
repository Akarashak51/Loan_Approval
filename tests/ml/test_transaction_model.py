"""Tests for the simulated merchant transaction model path."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from data.synthetic_transactions import TRANSACTION_FEATURES, generate_synthetic_transactions


def test_synthetic_transactions_have_expected_schema_and_ranges():
    data = generate_synthetic_transactions(200, random_state=7)

    assert list(data.columns) == TRANSACTION_FEATURES + ["defaulted"]
    assert data["payment_success_rate"].between(0, 1).all()
    assert data["refund_rate"].between(0, 1).all()
    assert data["chargeback_rate"].between(0, 1).all()
    assert data["customer_concentration"].between(0, 1).all()
    assert set(data["defaulted"].unique()).issubset({0, 1})


def test_synthetic_risk_signal_is_learnable():
    data = generate_synthetic_transactions(2000)
    high_risk = data["defaulted"] == 1
    assert data.loc[high_risk, "refund_rate"].mean() > data.loc[~high_risk, "refund_rate"].mean()
    assert data.loc[high_risk, "gmv_trend_30d"].mean() < data.loc[~high_risk, "gmv_trend_30d"].mean()