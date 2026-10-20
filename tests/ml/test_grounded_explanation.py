"""Tests for SHAP-grounded LLM explanations and safe fallback behavior."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml")))

from explain import grounded_explanation


DRIVERS = [
    {"feature": "credit_score", "contribution": -0.42},
    {"feature": "income", "contribution": 0.18},
    {"feature": "age", "contribution": 0.03},
]


def test_grounded_response_is_accepted(monkeypatch):
    monkeypatch.setattr(grounded_explanation, "call_llm", lambda _prompt: "credit_score and income were the main drivers.")

    result = grounded_explanation.explain(DRIVERS)

    assert result["source"] == "llm"
    assert result["grounded_in"] == ["credit_score", "income", "age"]


def test_ungrounded_response_uses_template(monkeypatch):
    monkeypatch.setattr(grounded_explanation, "call_llm", lambda _prompt: "The applicant has a strong business profile.")

    result = grounded_explanation.explain(DRIVERS)

    assert result["source"] == "template"
    assert "credit_score" in result["text"]


def test_missing_api_key_falls_back_cleanly(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = grounded_explanation.explain(DRIVERS)

    assert result["source"] == "template"
    assert result["text"]


def test_prompt_contains_no_values_beyond_signed_shap_contributions():
    prompt = grounded_explanation.build_prompt(DRIVERS)

    assert "credit_score" in prompt and "-0.4200" in prompt
    assert "income" in prompt and "0.1800" in prompt
    assert "applicant" not in prompt.lower()