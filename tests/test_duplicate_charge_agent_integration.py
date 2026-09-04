from __future__ import annotations

import json

from app.agents.ollama_planner import (
    OllamaFinancialPlanner,
    PLANNER_SYSTEM_PROMPT,
)
from app.core.tool_policy import (
    APPROVED_TOOLS,
    ToolPermission,
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
        self.calls.append(
            kwargs
        )
        return self.response


def test_duplicate_tool_is_policy_approved():
    assert (
        APPROVED_TOOLS[
            "detect_duplicate_charges"
        ].permission
        == ToolPermission.ANALYZE
    )


def test_duplicate_tool_is_registered():
    registry = ToolRegistry()

    tool = registry.get(
        "detect_duplicate_charges"
    )

    assert (
        tool.permission
        == ToolPermission.ANALYZE
    )

    assert tool.argument_names == (
        "start_date",
        "end_date",
    )

    assert (
        "Fingerprint is deliberately ignored"
        in tool.description
    )


def test_planner_prompt_requires_both_signals_for_broad_suspicion():
    assert (
        "request BOTH"
        in PLANNER_SYSTEM_PROMPT
    )
    assert (
        "detect_spending_anomalies"
        in PLANNER_SYSTEM_PROMPT
    )
    assert (
        "detect_duplicate_charges"
        in PLANNER_SYSTEM_PROMPT
    )


def test_suspicious_spending_plan_can_request_both_tools():
    client = FakeOllamaClient(
        json.dumps(
            {
                "calls": [
                    {
                        "name": (
                            "detect_spending_anomalies"
                        ),
                        "arguments": {
                            "start_date": (
                                "2026-07-01"
                            ),
                            "end_date": (
                                "2026-08-01"
                            ),
                        },
                    },
                    {
                        "name": (
                            "detect_duplicate_charges"
                        ),
                        "arguments": {
                            "start_date": (
                                "2026-07-01"
                            ),
                            "end_date": (
                                "2026-08-01"
                            ),
                        },
                    },
                ],
                "answer_instruction": (
                    "Combine both deterministic "
                    "signals."
                ),
            }
        )
    )

    planner = OllamaFinancialPlanner(
        client=client,
        registry=ToolRegistry(),
    )

    plan = planner.plan(
        "Existem gastos suspeitos "
        "em julho de 2026?"
    )

    assert [
        call.name
        for call in plan.calls
    ] == [
        "detect_spending_anomalies",
        "detect_duplicate_charges",
    ]
