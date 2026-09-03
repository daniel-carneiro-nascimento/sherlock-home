import pytest

from app.core.tool_policy import ToolPermission
from app.tools.registry import ToolNotRegisteredError, ToolRegistry


def test_registry_exposes_only_phase6_financial_tools():
    registry = ToolRegistry()
    assert set(registry.names()) == {
        "get_monthly_spending",
        "get_category_spending",
        "compare_monthly_spending",
        "find_recurring_expenses",
        "get_cash_flow",
        "detect_spending_anomalies",
    }


def test_registry_does_not_expose_legacy_policy_aliases():
    registry = ToolRegistry()
    assert "get_category_total" not in registry.names()
    assert "compare_months" not in registry.names()


def test_registry_returns_server_owned_tool_definition():
    tool = ToolRegistry().get("get_monthly_spending")
    assert tool.permission == ToolPermission.READ
    assert callable(tool.handler)


def test_registry_rejects_unknown_tool():
    with pytest.raises(ToolNotRegisteredError):
        ToolRegistry().get("execute_arbitrary_sql")


def test_model_description_contains_no_callable():
    for item in ToolRegistry().describe_for_model():
        assert "handler" not in item
        assert "callable" not in item
        assert isinstance(item["arguments"], list)
