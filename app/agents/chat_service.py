from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.financial_agent import (
    FinancialAgent,
)
from app.agents.ollama_planner import (
    OllamaFinancialPlanner,
)
from app.agents.ollama_responder import (
    OllamaFinancialResponder,
)
from app.agents.ollama_runtime import (
    OllamaClient,
)
from app.core.config import settings
from app.tools.dispatcher import (
    ToolDispatcher,
)
from app.tools.registry import (
    ToolRegistry,
)


@dataclass(frozen=True)
class FinancialChatResult:
    answer: str
    tools_used: tuple[str, ...]


@dataclass
class FinancialChatService:
    agent: FinancialAgent
    responder: OllamaFinancialResponder

    def ask(
        self,
        session: Session,
        *,
        user_message: str,
    ) -> FinancialChatResult:
        user_message = (
            user_message.strip()
        )

        if not user_message:
            raise ValueError(
                "user_message must not be empty"
            )

        evidence = (
            self.agent.gather_evidence(
                session,
                user_message=(
                    user_message
                ),
            )
        )

        answer = self.responder.respond(
            evidence
        )

        return FinancialChatResult(
            answer=answer,
            tools_used=tuple(
                result.tool_name
                for result
                in evidence.tool_results
            ),
        )


def build_financial_chat_service(
    *,
    client: OllamaClient | None = None,
) -> FinancialChatService:
    """
    Compose the current Phase 6 agent using the existing deterministic
    registry, dispatcher, tool policy, and local Ollama configuration.
    """
    ollama_client = (
        client
        if client is not None
        else OllamaClient(
            host=settings.ollama_host,
            model=settings.ollama_model,
        )
    )

    registry = ToolRegistry()

    planner = OllamaFinancialPlanner(
        client=ollama_client,
        registry=registry,
    )

    agent = FinancialAgent(
        planner=planner,
        dispatcher=ToolDispatcher(
            registry=registry
        ),
    )

    responder = OllamaFinancialResponder(
        client=ollama_client
    )

    return FinancialChatService(
        agent=agent,
        responder=responder,
    )
