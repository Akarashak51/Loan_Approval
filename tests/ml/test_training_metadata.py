"""Tests for the metrics persisted by the training pipeline."""

import json
from pathlib import Path


def test_saved_metadata_contains_final_model_metrics():
    metadata_path = Path(__file__).parents[2] / "ml" / "models" / "saved" / "metadata.json"
    metadata = json.loads(metadata_path.read_text())

    assert {"precision", "recall", "f1", "roc_auc"}.issubset(metadata)
    assert all(0 <= metadata[key] <= 1 for key in ("precision", "recall", "f1", "roc_auc"))