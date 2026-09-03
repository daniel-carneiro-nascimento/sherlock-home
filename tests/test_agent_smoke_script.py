from __future__ import annotations

import sys

import scripts.smoke_test_agent as smoke
from app.agents.tool_planning import ToolPlan
from app.tools.schemas import ToolCall


class FakeClient:
    pass


def test_registry_check_uses_current_financial_registry():
    registry = smoke.ToolRegistry()

    detail = smoke._registry_check(
        registry
    )

    assert (
        "approved financial tools"
        in detail
    )


def test_planner_check_requires_expected_monthly_tool(
    monkeypatch,
):
    class FakePlanner:
        def __init__(
            self,
            *,
            client,
            registry,
        ):
            pass

        def plan(
            self,
            user_message,
        ):
            return ToolPlan(
                calls=(
                    ToolCall(
                        name=(
                            "get_monthly_spending"
                        ),
                        arguments={
                            "year": 2026,
                            "month": 9,
                        },
                    ),
                ),
                answer_instruction=None,
            )

    monkeypatch.setattr(
        smoke,
        "OllamaFinancialPlanner",
        FakePlanner,
    )

    detail = smoke._planner_check(
        FakeClient(),
        smoke.ToolRegistry(),
    )

    assert (
        "get_monthly_spending"
        in detail
    )


def test_planner_check_rejects_wrong_tool(
    monkeypatch,
):
    class FakePlanner:
        def __init__(
            self,
            *,
            client,
            registry,
        ):
            pass

        def plan(
            self,
            user_message,
        ):
            return ToolPlan(
                calls=(
                    ToolCall(
                        name=(
                            "get_category_spending"
                        ),
                        arguments={
                            "year": 2026,
                            "month": 9,
                        },
                    ),
                ),
                answer_instruction=None,
            )

    monkeypatch.setattr(
        smoke,
        "OllamaFinancialPlanner",
        FakePlanner,
    )

    try:
        smoke._planner_check(
            FakeClient(),
            smoke.ToolRegistry(),
        )
    except RuntimeError as exc:
        assert (
            "get_monthly_spending"
            in str(exc)
        )
    else:
        raise AssertionError(
            "wrong tool should fail "
            "compatibility smoke check"
        )


def test_run_check_converts_exception_to_failure():
    result = smoke._run_check(
        "synthetic",
        lambda: (
            _raise_value_error()
        ),
    )

    assert result.passed is False
    assert (
        "ValueError"
        in result.detail
    )


def _raise_value_error():
    raise ValueError("synthetic")


def test_main_returns_zero_when_all_checks_pass(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["smoke_test_agent.py"],
    )

    monkeypatch.setattr(
        smoke,
        "OllamaClient",
        lambda **kwargs: FakeClient(),
    )

    monkeypatch.setattr(
        smoke,
        "_runtime_check",
        lambda client: "ok",
    )

    monkeypatch.setattr(
        smoke,
        "_registry_check",
        lambda registry: "ok",
    )

    monkeypatch.setattr(
        smoke,
        "_planner_check",
        lambda client, registry: "ok",
    )

    monkeypatch.setattr(
        smoke,
        "_responder_check",
        lambda client: "ok",
    )

    assert smoke.main() == 0


def test_main_returns_one_when_check_fails(
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["smoke_test_agent.py"],
    )

    monkeypatch.setattr(
        smoke,
        "OllamaClient",
        lambda **kwargs: FakeClient(),
    )

    monkeypatch.setattr(
        smoke,
        "_runtime_check",
        lambda client: "ok",
    )

    monkeypatch.setattr(
        smoke,
        "_registry_check",
        lambda registry: "ok",
    )

    def fail_planner(
        client,
        registry,
    ):
        raise RuntimeError(
            "planner failed"
        )

    monkeypatch.setattr(
        smoke,
        "_planner_check",
        fail_planner,
    )

    monkeypatch.setattr(
        smoke,
        "_responder_check",
        lambda client: "ok",
    )

    assert smoke.main() == 1
