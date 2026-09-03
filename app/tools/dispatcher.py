from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.runtime_state import ensure_runtime_safe
from app.core.security_enforcer import enforce
from app.core.tool_policy import ToolPermission, validate_tool_permission
from app.tools.registry import ToolNotRegisteredError, ToolRegistry
from app.tools.schemas import ToolCall, ToolExecutionResult, to_json_safe


class ToolDispatchError(RuntimeError):
    pass


@dataclass
class ToolDispatcher:
    registry: ToolRegistry

    def execute(
        self,
        session: Session,
        call: ToolCall,
        *,
        allowed_permissions: set[ToolPermission],
    ) -> ToolExecutionResult:
        ensure_runtime_safe()

        try:
            tool = self.registry.get(call.name)
        except ToolNotRegisteredError:
            enforce(validate_tool_permission(call.name, allowed_permissions))
            raise ToolDispatchError("tool registry and policy allowlist are inconsistent")

        enforce(validate_tool_permission(tool.name, allowed_permissions))

        result = tool.handler(session, dict(call.arguments))
        serialized = to_json_safe(result)

        if not isinstance(serialized, dict):
            raise ToolDispatchError("tool result must serialize to an object")

        return ToolExecutionResult(tool_name=tool.name, data=serialized)
