import json
from decimal import Decimal

from app.agents.chat_service import (
    FinancialChatService,
)
from app.agents.financial_agent import (
    FinancialAgent,
)
from app.agents.ollama_planner import (
    OllamaFinancialPlanner,
)
from app.agents.ollama_responder import (
    OllamaFinancialResponder,
)
from app.core import tool_policy
from app.core.tool_policy import (
    ToolPermission,
)
from app.tools.dispatcher import (
    ToolDispatcher,
)
from app.tools.registry import (
    RegisteredTool,
    ToolRegistry,
)


class SequencedFakeOllama:
    def __init__(self):
        self.responses = [
            json.dumps(
                {
                    "calls": [
                        {
                            "name": (
                                "synthetic_monthly"
                            ),
                            "arguments": {},
                        }
                    ],
                    "answer_instruction": (
                        "Explain the evidence."
                    ),
                }
            ),
            "Você pode revisar os gastos discricionários.",
        ]

    def chat(
        self,
        **kwargs,
    ):
        return self.responses.pop(0)


def synthetic_handler(
    session,
    arguments,
):
    return {
        "total": Decimal("123.45"),
    }


def test_agent_round_trip_from_model_plan_to_model_answer(
    monkeypatch,
):
    monkeypatch.setitem(
        tool_policy.APPROVED_TOOLS,
        "synthetic_monthly",
        tool_policy.ToolDefinition(
            name="synthetic_monthly",
            permission=ToolPermission.READ,
        ),
    )

    registry = ToolRegistry(
        {
            "synthetic_monthly": (
                RegisteredTool(
                    name=(
                        "synthetic_monthly"
                    ),
                    description=(
                        "synthetic monthly spending"
                    ),
                    permission=(
                        ToolPermission.READ
                    ),
                    handler=(
                        synthetic_handler
                    ),
                    argument_names=(),
                )
            )
        }
    )

    model = SequencedFakeOllama()

    planner = OllamaFinancialPlanner(
        client=model,
        registry=registry,
    )

    agent = FinancialAgent(
        planner=planner,
        dispatcher=ToolDispatcher(
            registry=registry
        ),
    )

    responder = (
        OllamaFinancialResponder(
            client=model
        )
    )

    service = FinancialChatService(
        agent=agent,
        responder=responder,
    )

    result = service.ask(
        None,
        user_message=(
            "Como reduzir meus gastos?"
        ),
    )

    assert result.tools_used == (
        "synthetic_monthly",
    )

    assert result.answer == (
        "Você pode revisar os "
        "gastos discricionários."
    )
