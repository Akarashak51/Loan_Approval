"""Tests for illustrative Capital tier-gap calculations."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from eligibility.gap_calculator import CAPITAL_TIER_CRITERIA, _normalized_gap, compute_gaps, rank_all_tiers


def test_merchant_can_qualify_for_starter_and_gap_growth():
    merchant = {
        "gmv_trend_30d": 0.0, "gmv_trend_90d": 0.0, "payment_success_rate": 0.95,
        "refund_rate": 0.09, "chargeback_rate": 0.01, "customer_concentration": 0.4,
        "order_volume_volatility": 0.7, "account_age_days": 200,
    }

    results = rank_all_tiers(merchant)

    assert any(result.tier == "Starter Advance" and result.eligible for result in results)
    growth = next(result for result in results if result.tier == "Growth Capital")
    assert growth.gaps
    assert growth.overall_message.startswith("Not yet eligible")


def test_normalized_gap_preserves_comparable_distance_logic():
    result = compute_gaps({"refund_rate": 0.15}, CAPITAL_TIER_CRITERIA[0])
    refund_gap = next(gap for gap in result.gaps if gap.feature == "refund_rate")

    assert _normalized_gap(refund_gap, CAPITAL_TIER_CRITERIA[0]) == refund_gap.delta / 0.10