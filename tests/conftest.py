"""Shared test-only configuration for remote judging."""

import pytest

from style_audit.decision_api import DecisionAPISettings


@pytest.fixture(autouse=True)
def configured_decision_api(monkeypatch):
    settings = DecisionAPISettings(
        api_base="https://judge.invalid/openai/v1",
        model="Decision-1",
        custom_llm_provider="openai",
        api_key="test-only-api-key",
        timeout=30.0,
    )
    monkeypatch.setattr("style_audit.llm.load_decision_api", lambda *args, **kwargs: settings)
