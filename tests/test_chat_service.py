from dataclasses import dataclass

from app.agents.chat_service import (
    FinancialChatService,
)
from app.agents.financial_agent import (
    AgentEvidence,
)
from app.tools.schemas import (
    ToolExecutionResult,
)


@dataclass
class FakeAgent:
    evidence: AgentEvidence

    def gather_evidence(
        self,
        session,
        *,
        user_message,
    ):
        return self.evidence


@dataclass
class FakeResponder:
    answer: str

    def respond(
        self,
        evidence,
    ):
        return self.answer


def test_chat_service_returns_answer_and_tools_used():
    evidence = AgentEvidence(
        user_message=(
            "Como reduzir meus gastos?"
        ),
        tool_results=(
            ToolExecutionResult(
                tool_name=(
                    "get_monthly_spending"
                ),
                data={
                    "total": "100.00",
                },
            ),
            ToolExecutionResult(
                tool_name=(
                    "get_category_spending"
                ),
                data={
                    "total": "100.00",
                },
            ),
        ),
        answer_instruction=None,
    )

    service = FinancialChatService(
        agent=FakeAgent(
            evidence=evidence
        ),
        responder=FakeResponder(
            answer="Resposta baseada nos dados."
        ),
    )

    result = service.ask(
        None,
        user_message=(
            "Como reduzir meus gastos?"
        ),
    )

    assert result.answer == (
        "Resposta baseada nos dados."
    )

    assert result.tools_used == (
        "get_monthly_spending",
        "get_category_spending",
    )


def test_chat_service_rejects_empty_message():
    evidence = AgentEvidence(
        user_message="unused",
        tool_results=(),
        answer_instruction=None,
    )

    service = FinancialChatService(
        agent=FakeAgent(
            evidence=evidence
        ),
        responder=FakeResponder(
            answer="unused"
        ),
    )

    try:
        service.ask(
            None,
            user_message="   ",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "empty user message should fail"
        )
