import json

import pytest

from app.agents.tool_planning import (
    MAX_PLAN_CALLS,
    ToolPlanError,
    build_tool_planning_context,
    parse_tool_plan,
)
from app.tools.registry import ToolRegistry


def test_parse_valid_tool_plan():
    raw = json.dumps({
        "calls": [{
            "name": "get_monthly_spending",
            "arguments": {"year": 2026, "month": 9},
        }],
        "answer_instruction": "Explain the result.",
    })
    plan = parse_tool_plan(raw, registry=ToolRegistry())
    assert plan.calls[0].name == "get_monthly_spending"


def test_plan_rejects_invalid_json():
    with pytest.raises(ToolPlanError):
        parse_tool_plan("not json", registry=ToolRegistry())


def test_plan_rejects_unregistered_tool():
    raw = json.dumps({
        "calls": [{"name": "execute_arbitrary_sql", "arguments": {}}],
    })
    with pytest.raises(ToolPlanError, match="unregistered"):
        parse_tool_plan(raw, registry=ToolRegistry())


def test_plan_rejects_extra_call_fields():
    raw = json.dumps({
        "calls": [{
            "name": "get_monthly_spending",
            "arguments": {},
            "callable": "evil",
        }],
    })
    with pytest.raises(ToolPlanError):
        parse_tool_plan(raw, registry=ToolRegistry())


def test_plan_rejects_too_many_calls():
    calls = [
        {
            "name": "get_monthly_spending",
            "arguments": {"year": 2026, "month": 9},
        }
        for _ in range(MAX_PLAN_CALLS + 1)
    ]
    with pytest.raises(ToolPlanError, match="maximum"):
        parse_tool_plan(json.dumps({"calls": calls}), registry=ToolRegistry())


def test_planning_context_exposes_metadata_only():
    context = build_tool_planning_context(ToolRegistry())
    serialized = json.dumps(context)
    assert "handler" not in serialized
    assert "Session" not in serialized
    assert "postgres" not in serialized.lower()
