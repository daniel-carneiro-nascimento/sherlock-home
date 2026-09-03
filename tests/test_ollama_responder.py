from app.agents.financial_agent import (
    AgentEvidence,
)
from app.agents.ollama_responder import (
    OllamaFinancialResponder,
)
from app.tools.schemas import (
    ToolExecutionResult,
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


def test_responder_returns_local_model_answer():
    client = FakeOllamaClient(
        "Você gastou mais em alimentação."
    )

    responder = OllamaFinancialResponder(
        client=client
    )

    evidence = AgentEvidence(
        user_message=(
            "Como reduzir gastos?"
        ),
        tool_results=(
            ToolExecutionResult(
                tool_name=(
                    "get_category_spending"
                ),
                data={
                    "total": "100.00",
                    "categories": [],
                },
            ),
        ),
        answer_instruction=(
            "Use evidence only."
        ),
    )

    answer = responder.respond(
        evidence
    )

    assert answer == (
        "Você gastou mais em alimentação."
    )

    assert (
        client.calls[0]["json_mode"]
        is False
    )


def test_responder_receives_structured_tool_evidence():
    client = FakeOllamaClient(
        "ok"
    )

    responder = OllamaFinancialResponder(
        client=client
    )

    evidence = AgentEvidence(
        user_message="question",
        tool_results=(
            ToolExecutionResult(
                tool_name=(
                    "get_monthly_spending"
                ),
                data={
                    "total": "42.50",
                },
            ),
        ),
        answer_instruction=None,
    )

    responder.respond(evidence)

    payload = (
        client.calls[0]["messages"][1]
        ["content"]
    )

    assert (
        '"tool_name": '
        '"get_monthly_spending"'
        in payload
    )
    assert '"42.50"' in payload
