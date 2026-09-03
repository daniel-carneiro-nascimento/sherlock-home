from dataclasses import dataclass
from enum import Enum

from app.core.security import SecurityViolation, Severity


class ToolPermission(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    WRITE = "write"
    ADMIN = "admin"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    permission: ToolPermission


APPROVED_TOOLS = {
    "get_monthly_spending": ToolDefinition("get_monthly_spending", ToolPermission.READ),
    "get_category_spending": ToolDefinition("get_category_spending", ToolPermission.READ),
    "compare_monthly_spending": ToolDefinition("compare_monthly_spending", ToolPermission.ANALYZE),
    "find_recurring_expenses": ToolDefinition("find_recurring_expenses", ToolPermission.ANALYZE),
    "get_cash_flow": ToolDefinition("get_cash_flow", ToolPermission.ANALYZE),
    "detect_spending_anomalies": ToolDefinition("detect_spending_anomalies", ToolPermission.ANALYZE),

    # Legacy policy names retained temporarily for backwards compatibility.
    "get_category_total": ToolDefinition("get_category_total", ToolPermission.READ),
    "compare_months": ToolDefinition("compare_months", ToolPermission.ANALYZE),
}


def validate_tool(tool_name: str) -> SecurityViolation | None:
    if tool_name not in APPROVED_TOOLS:
        return SecurityViolation(
            rule_id="SH-TOOL-001",
            severity=Severity.CRITICAL,
            reason="unauthorized_tool",
            shutdown_required=False,
        )
    return None


def validate_tool_permission(
    tool_name: str,
    allowed_permissions: set[ToolPermission],
) -> SecurityViolation | None:
    violation = validate_tool(tool_name)
    if violation is not None:
        return violation

    tool = APPROVED_TOOLS[tool_name]
    if tool.permission not in allowed_permissions:
        return SecurityViolation(
            rule_id="SH-TOOL-002",
            severity=Severity.WARNING,
            reason="tool_permission_not_allowed",
            shutdown_required=False,
        )

    return None
