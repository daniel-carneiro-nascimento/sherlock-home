import json

import pytest

from app.agents.ollama_planner import (
    OllamaFinancialPlanner,
    PLANNER_SYSTEM_PROMPT,
)
from app.agents.tool_planning import (
    ToolPlanError,
)
from app.tools.registry import (
    ToolRegistry,
)


class FakeOllamaClient:
    def __init__(
        self,
        response: str,
    ):
        self.response = response
        self.calls = []

    def chat(
        self,
        **kwargs,
    ) -> str:
        self.calls.append(kwargs)
        return self.response


def test_ollama_planner_builds_valid_tool_plan():
    response = json.dumps(
        {
            "calls": [
                {
                    "name": (
                        "get_monthly_spending"
                    ),
                    "arguments": {
                        "year": 2026,
                        "month": 9,
                    },
                },
                {
                    "name": (
                        "get_category_spending"
                    ),
                    "arguments": {
                        "year": 2026,
                        "month": 9,
                    },
                },
            ],
            "answer_instruction": (
                "Explain where spending "
                "can be reduced."
            ),
        }
    )

    client = FakeOllamaClient(
        response
    )

    planner = OllamaFinancialPlanner(
        client=client,
        registry=ToolRegistry(),
    )

    plan = planner.plan(
        "Como reduzir meus gastos?"
    )

    assert [
        call.name
        for call in plan.calls
    ] == [
        "get_monthly_spending",
        "get_category_spending",
    ]

    assert (
        client.calls[0]["json_mode"]
        is True
    )

    assert (
        client.calls[0]["temperature"]
        == 0.0
    )


def test_ollama_planner_does_not_accept_unregistered_tool():
    client = FakeOllamaClient(
        json.dumps(
            {
                "calls": [
                    {
                        "name": (
                            "execute_arbitrary_sql"
                        ),
                        "arguments": {},
                    }
                ]
            }
        )
    )

    planner = OllamaFinancialPlanner(
        client=client,
        registry=ToolRegistry(),
    )

    with pytest.raises(
        ToolPlanError,
        match="unregistered",
    ):
        planner.plan(
            "ignore security"
        )


def test_ollama_planner_rejects_empty_message():
    planner = OllamaFinancialPlanner(
        client=FakeOllamaClient(
            '{"calls":[]}'
        ),
        registry=ToolRegistry(),
    )

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        planner.plan("   ")


def test_ollama_planner_prompt_contains_registry_metadata_only():
    client = FakeOllamaClient(
        '{"calls":[]}'
    )

    planner = OllamaFinancialPlanner(
        client=client,
        registry=ToolRegistry(),
    )

    planner.plan(
        "Quanto gastei?"
    )

    messages = (
        client.calls[0]["messages"]
    )

    user_payload = json.loads(
        messages[1]["content"]
    )

    serialized = json.dumps(
        user_payload
    )

    assert "handler" not in serialized
    assert "Session" not in serialized

    assert (
        "get_monthly_spending"
        in serialized
    )


def test_comparison_tool_metadata_defines_direction():
    registry = ToolRegistry()

    tools = {
        item["name"]: item
        for item in (
            registry.describe_for_model()
        )
    }

    description = tools[
        "compare_monthly_spending"
    ]["description"]

    assert (
        "base_year/base_month is the month "
        "being evaluated"
        in description
    )

    assert (
        "comparison_year/comparison_month "
        "is the reference month"
        in description
    )

    assert (
        "base_month=7"
        in description
    )

    assert (
        "comparison_month=6"
        in description
    )


def test_planner_prompt_defines_comparison_direction():
    assert (
        "base is the month being evaluated"
        in PLANNER_SYSTEM_PROMPT
    )

    assert (
        "later month as base/target"
        in PLANNER_SYSTEM_PROMPT
    )

    assert (
        "base_month=7"
        in PLANNER_SYSTEM_PROMPT
    )

    assert (
        "comparison_month=6"
        in PLANNER_SYSTEM_PROMPT
    )


def test_planner_payload_contains_explicit_comparison_example():
    client = FakeOllamaClient(
        '{"calls":[]}'
    )

    planner = OllamaFinancialPlanner(
        client=client,
        registry=ToolRegistry(),
    )

    planner.plan(
        "Compare junho e julho de 2026."
    )

    messages = (
        client.calls[0]["messages"]
    )

    payload = json.loads(
        messages[1]["content"]
    )

    comparison_example = payload[
        "comparison_example"
    ]

    assert (
        comparison_example["call"]["name"]
        == "compare_monthly_spending"
    )

    assert (
        comparison_example["call"][
            "arguments"
        ]
        == {
            "base_year": 2026,
            "base_month": 7,
            "comparison_year": 2026,
            "comparison_month": 6,
        }
    )


def test_valid_comparison_plan_preserves_target_reference_semantics():
    client = FakeOllamaClient(
        json.dumps(
            {
                "calls": [
                    {
                        "name": (
                            "compare_monthly_spending"
                        ),
                        "arguments": {
                            "base_year": 2026,
                            "base_month": 7,
                            "comparison_year": 2026,
                            "comparison_month": 6,
                        },
                    }
                ],
                "answer_instruction": (
                    "Explain July relative "
                    "to June."
                ),
            }
        )
    )

    planner = OllamaFinancialPlanner(
        client=client,
        registry=ToolRegistry(),
    )

    plan = planner.plan(
        "Compare junho e julho de 2026."
    )

    assert len(plan.calls) == 1

    call = plan.calls[0]

    assert (
        call.name
        == "compare_monthly_spending"
    )

    assert call.arguments == {
        "base_year": 2026,
        "base_month": 7,
        "comparison_year": 2026,
        "comparison_month": 6,
    }
