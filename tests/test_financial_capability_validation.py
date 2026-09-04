from __future__ import annotations

from dataclasses import dataclass

import scripts.validate_financial_capabilities as validation


@dataclass(frozen=True)
class FakeResult:
    answer: str
    tools_used: tuple[str, ...]


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeService:
    def __init__(self, tools_used: tuple[str, ...]):
        self.tools_used = tools_used

    def ask(self, session, *, user_message):
        return FakeResult(
            answer="synthetic answer",
            tools_used=self.tools_used,
        )


def test_all_expected_capabilities_are_defined():
    names = {
        scenario.name
        for scenario in validation.SCENARIOS
    }

    assert names == {
        "category_spending",
        "recurring_expenses",
        "spending_anomalies",
        "duplicate_charges",
        "suspicious_spending",
    }


def test_category_scenario_requires_category_tool():
    scenario = next(
        s
        for s in validation.SCENARIOS
        if s.name == "category_spending"
    )

    assert "get_category_spending" in scenario.expected_tools


def test_recurring_scenario_requires_recurring_tool():
    scenario = next(
        s
        for s in validation.SCENARIOS
        if s.name == "recurring_expenses"
    )

    assert "find_recurring_expenses" in scenario.expected_tools


def test_anomaly_scenario_requires_anomaly_tool():
    scenario = next(
        s
        for s in validation.SCENARIOS
        if s.name == "spending_anomalies"
    )

    assert "detect_spending_anomalies" in scenario.expected_tools


def test_run_scenario_passes_when_expected_tool_is_used(monkeypatch):
    scenario = validation.Scenario(
        name="x",
        question="question",
        expected_tools=("tool_a",),
    )

    monkeypatch.setattr(
        validation,
        "build_financial_chat_service",
        lambda: FakeService(("tool_a",)),
    )
    monkeypatch.setattr(
        validation,
        "SessionLocal",
        lambda: FakeSession(),
    )

    assert validation.run_scenario(scenario=scenario) is True


def test_run_scenario_fails_when_expected_tool_is_missing(monkeypatch):
    scenario = validation.Scenario(
        name="x",
        question="question",
        expected_tools=("tool_a",),
    )

    monkeypatch.setattr(
        validation,
        "build_financial_chat_service",
        lambda: FakeService(("tool_b",)),
    )
    monkeypatch.setattr(
        validation,
        "SessionLocal",
        lambda: FakeSession(),
    )

    assert validation.run_scenario(scenario=scenario) is False
