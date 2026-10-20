"""Tests for shared income and transaction decision banding."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from decisioning.bands import decide


@pytest.mark.parametrize("probability, expected", [
    (0.0, "APPROVE"),
    (0.1499, "APPROVE"),
    (0.15, "REVIEW"),
    (0.5499, "REVIEW"),
    (0.55, "DECLINE"),
    (1.0, "DECLINE"),
])
def test_default_probability_boundaries(probability, expected):
    assert decide(probability) == expected


@pytest.mark.parametrize("probability, expected", [(0.10, "APPROVE"), (0.20, "REVIEW"), (0.60, "DECLINE")])
def test_custom_thresholds_support_both_flows(probability, expected):
    assert decide(probability, approve_below=0.20, decline_at_or_above=0.60) == expected