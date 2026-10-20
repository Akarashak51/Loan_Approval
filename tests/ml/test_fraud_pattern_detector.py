"""Tests for the transparent merchant fraud-pattern rules engine."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from fraud.pattern_detector import detect_fraud_signals


def _history(count: int, overrides=None):
    overrides = overrides or {}
    return [
        {
            "date": f"2026-01-{index + 1:02d}",
            "gmv": 1000,
            "refund_count": 1,
            "chargeback_count": 0,
            "order_count": 10,
            **overrides.get(index, {}),
        }
        for index in range(count)
    ]


def test_normal_history_has_low_score_and_no_flags():
    result = detect_fraud_signals(_history(35))

    assert result == {"fraud_score": 0.0, "flags": [], "flagged_days": []}


def test_refund_spike_is_flagged():
    result = detect_fraud_signals(_history(35, {34: {"refund_count": 20}}))

    assert result["fraud_score"] >= 0.25
    assert any("Refund spike" in flag for flag in result["flags"])
    assert "2026-01-35" in result["flagged_days"]


def test_chargeback_cluster_is_flagged():
    result = detect_fraud_signals(_history(20, {
        15: {"chargeback_count": 1}, 16: {"chargeback_count": 1}, 17: {"chargeback_count": 1},
    }))

    assert result["fraud_score"] >= 0.25
    assert any("Chargeback cluster" in flag for flag in result["flags"])


def test_velocity_anomaly_is_flagged():
    result = detect_fraud_signals(_history(15, {14: {"order_count": 50}}))

    assert result["fraud_score"] >= 0.25
    assert any("Velocity anomaly" in flag for flag in result["flags"])


def test_gmv_refund_mismatch_is_flagged():
    result = detect_fraud_signals(_history(12, {
        10: {"gmv": 2500}, 11: {"refund_count": 3, "order_count": 10},
    }))

    assert result["fraud_score"] >= 0.25
    assert any("GMV-refund mismatch" in flag for flag in result["flags"])