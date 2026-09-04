from dataclasses import dataclass
from enum import Enum

from app.core.security import (
    SecurityViolation,
    Severity,
)


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
    "get_monthly_spending": ToolDefinition(
        name="get_monthly_spending",
        permission=ToolPermission.READ,
    ),
    "get_category_spending": ToolDefinition(
        name="get_category_spending",
        permission=ToolPermission.READ,
    ),
    "compare_monthly_spending": ToolDefinition(
        name="compare_monthly_spending",
        permission=ToolPermission.ANALYZE,
    ),
    "find_recurring_expenses": ToolDefinition(
        name="find_recurring_expenses",
        permission=ToolPermission.ANALYZE,
    ),
    "get_cash_flow": ToolDefinition(
        name="get_cash_flow",
        permission=ToolPermission.ANALYZE,
    ),
    "detect_spending_anomalies": ToolDefinition(
        name="detect_spending_anomalies",
        permission=ToolPermission.ANALYZE,
    ),
    "detect_duplicate_charges": ToolDefinition(
        name="detect_duplicate_charges",
        permission=ToolPermission.ANALYZE,
    ),

    # Legacy policy names retained for compatibility with older tests/code.
    # They are not exposed through the current ToolRegistry.
    "get_category_total": ToolDefinition(
        name="get_category_total",
        permission=ToolPermission.READ,
    ),
    "compare_months": ToolDefinition(
        name="compare_months",
        permission=ToolPermission.ANALYZE,
    ),
}


def validate_tool(
    tool_name: str,
) -> SecurityViolation | None:
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
    allowed_permissions: set[
        ToolPermission
    ],
) -> SecurityViolation | None:
    violation = validate_tool(
        tool_name
    )

    if violation is not None:
        return violation

    tool = APPROVED_TOOLS[
        tool_name
    ]

    if (
        tool.permission
        not in allowed_permissions
    ):
        return SecurityViolation(
            rule_id="SH-TOOL-002",
            severity=Severity.WARNING,
            reason=(
                "tool_permission_not_allowed"
            ),
            shutdown_required=False,
        )

    return None
