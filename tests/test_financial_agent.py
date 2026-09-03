from dataclasses import dataclass

from app.agents.financial_agent import FinancialAgent
from app.agents.tool_planning import ToolPlan
from app.core.tool_policy import ToolPermission
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import RegisteredTool, ToolRegistry
from app.tools.schemas import ToolCall


@dataclass
class FakePlanner:
    plan_value: ToolPlan

    def plan(self, user_message: str) -> ToolPlan:
        return self.plan_value


def fake_handler(session, arguments):
    return {"echo": arguments["value"]}


def test_financial_agent_executes_plan_through_dispatcher(monkeypatch):
    from app.core import tool_policy
    monkeypatch.setitem(
        tool_policy.APPROVED_TOOLS,
        "synthetic_read",
        tool_policy.ToolDefinition("synthetic_read", ToolPermission.READ),
    )

    registry = ToolRegistry({
        "synthetic_read": RegisteredTool(
            "synthetic_read",
            "synthetic",
            ToolPermission.READ,
            fake_handler,
            ("value",),
        )
    })

    agent = FinancialAgent(
        planner=FakePlanner(
            ToolPlan(
                calls=(ToolCall("synthetic_read", {"value": "ok"}),),
                answer_instruction="Use evidence only.",
            )
        ),
        dispatcher=ToolDispatcher(registry),
    )

    evidence = agent.gather_evidence(
        None,
        user_message="How can I reduce spending?",
    )

    assert evidence.tool_results[0].data["echo"] == "ok"
    assert evidence.answer_instruction == "Use evidence only."
