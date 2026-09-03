import json

import pytest

from app.agents.ollama_planner import (
    OllamaFinancialPlanner,
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
