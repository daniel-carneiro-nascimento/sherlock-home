from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from app.agents.tool_planning import ToolPlan
from app.core.tool_policy import ToolPermission
from app.tools.dispatcher import ToolDispatcher
from app.tools.schemas import ToolExecutionResult


class FinancialPlanner(Protocol):
    def plan(self, user_message: str) -> ToolPlan:
        ...


@dataclass(frozen=True)
class AgentEvidence:
    user_message: str
    tool_results: tuple[ToolExecutionResult, ...]
    answer_instruction: str | None


@dataclass
class FinancialAgent:
    planner: FinancialPlanner
    dispatcher: ToolDispatcher

    def gather_evidence(
        self,
        session: Session,
        *,
        user_message: str,
        allowed_permissions: set[ToolPermission] | None = None,
    ) -> AgentEvidence:
        permissions = (
            allowed_permissions
            if allowed_permissions is not None
            else {ToolPermission.READ, ToolPermission.ANALYZE}
        )

        plan = self.planner.plan(user_message)

        results = tuple(
            self.dispatcher.execute(
                session,
                call,
                allowed_permissions=permissions,
            )
            for call in plan.calls
        )

        return AgentEvidence(
            user_message=user_message,
            tool_results=results,
            answer_instruction=plan.answer_instruction,
        )
