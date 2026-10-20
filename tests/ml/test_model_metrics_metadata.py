"""Regression tests for both saved model metric contracts."""

import json
from pathlib import Path


def test_both_model_metadata_files_contain_held_out_metrics():
    saved = Path(__file__).parents[2] / "ml" / "models" / "saved"
    required = {"precision", "recall", "f1", "roc_auc"}

    for filename in ("metadata.json", "transaction_model_metadata.json"):
        metadata = json.loads((saved / filename).read_text())
        assert required.issubset(metadata)
        assert all(0 <= metadata[key] <= 1 for key in required)