"""
Tests for the preprocessing pipeline and feature config (spec section 40).
Runs against synthetic data matching the schema -- doesn't require the
real downloaded dataset, so it works in any environment.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

import numpy as np
import pandas as pd
import pytest

from preprocessing.feature_config import FEATURES, NUMERIC_FEATURES, CATEGORICAL_FEATURES, MUTABLE_FEATURES
from preprocessing.preprocessing import build_preprocessor


@pytest.fixture
def synthetic_df():
    np.random.seed(0)
    n = 40
    data = {}
    for col in NUMERIC_FEATURES:
        cfg = FEATURES[col]
        data[col] = np.random.randint(cfg["min"], cfg["max"] + 1, n)
    for col in CATEGORICAL_FEATURES:
        cfg = FEATURES[col]
        data[col] = np.random.choice(cfg["options"], n)
    return pd.DataFrame(data)


def test_feature_config_has_no_overlap():
    assert set(NUMERIC_FEATURES).isdisjoint(set(CATEGORICAL_FEATURES))


def test_immutable_features_excluded_from_mutable():
    assert "age" not in MUTABLE_FEATURES
    assert "personal_status_sex" not in MUTABLE_FEATURES
    assert "foreign_worker" not in MUTABLE_FEATURES


def test_preprocessor_fits_and_transforms(synthetic_df):
    preprocessor = build_preprocessor()
    transformed = preprocessor.fit_transform(synthetic_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
    assert transformed.shape[0] == len(synthetic_df)
    assert transformed.shape[1] > 0


def test_preprocessor_handles_unknown_category(synthetic_df):
    preprocessor = build_preprocessor()
    preprocessor.fit(synthetic_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES])

    unseen = synthetic_df.iloc[[0]].copy()
    unseen.loc[:, CATEGORICAL_FEATURES[0]] = "totally-unseen-category"
    # Should not raise -- OneHotEncoder(handle_unknown="ignore")
    result = preprocessor.transform(unseen[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
    assert result.shape[0] == 1
