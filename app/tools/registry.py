from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.core.tool_policy import ToolPermission
from app.tools.financial_tools import (
    ToolHandler,
    run_cash_flow,
    run_category_spending,
    run_monthly_spending,
    run_recurring_expenses,
    run_spending_anomalies,
    run_spending_comparison,
)


class ToolNotRegisteredError(KeyError):
    pass


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    permission: ToolPermission
    handler: ToolHandler
    argument_names: tuple[str, ...]


class ToolRegistry:
    def __init__(
        self,
        tools: Mapping[str, RegisteredTool] | None = None,
    ) -> None:
        self._tools = dict(
            DEFAULT_TOOLS
            if tools is None
            else tools
        )

    def get(
        self,
        name: str,
    ) -> RegisteredTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotRegisteredError(
                name
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(
            sorted(self._tools)
        )

    def describe_for_model(
        self,
    ) -> list[dict[str, object]]:
        return [
            {
                "name": tool.name,
                "description": (
                    tool.description
                ),
                "permission": (
                    tool.permission.value
                ),
                "arguments": list(
                    tool.argument_names
                ),
            }
            for tool in sorted(
                self._tools.values(),
                key=lambda item: item.name,
            )
        ]


DEFAULT_TOOLS = {
    "get_monthly_spending": RegisteredTool(
        "get_monthly_spending",
        (
            "Return total expense spending "
            "for one calendar month."
        ),
        ToolPermission.READ,
        run_monthly_spending,
        (
            "year",
            "month",
        ),
    ),
    "get_category_spending": RegisteredTool(
        "get_category_spending",
        (
            "Return expense spending grouped "
            "by category for one calendar month."
        ),
        ToolPermission.READ,
        run_category_spending,
        (
            "year",
            "month",
        ),
    ),
    "compare_monthly_spending": RegisteredTool(
        "compare_monthly_spending",
        (
            "Compare expense spending between two calendar months. "
            "IMPORTANT SEMANTICS: base_year/base_month is the month "
            "being evaluated (the newer/current/target month), while "
            "comparison_year/comparison_month is the reference month "
            "used as the denominator for percentage change. "
            "For a natural-language request such as 'compare June and "
            "July 2026', interpret the later month as the base/target "
            "and the earlier month as the comparison/reference unless "
            "the user explicitly states the opposite. "
            "Example: to answer how July changed relative to June, use "
            "base_year=2026, base_month=7, comparison_year=2026, "
            "comparison_month=6."
        ),
        ToolPermission.ANALYZE,
        run_spending_comparison,
        (
            "base_year",
            "base_month",
            "comparison_year",
            "comparison_month",
        ),
    ),
    "find_recurring_expenses": RegisteredTool(
        "find_recurring_expenses",
        (
            "Find deterministic recurring "
            "expense candidates in a date range."
        ),
        ToolPermission.ANALYZE,
        run_recurring_expenses,
        (
            "start_date",
            "end_date",
            "min_occurrences",
            "min_interval_days",
            "max_interval_days",
            "amount_tolerance",
        ),
    ),
    "get_cash_flow": RegisteredTool(
        "get_cash_flow",
        (
            "Return deterministic income, "
            "expense, transfer, and net "
            "cash-flow totals."
        ),
        ToolPermission.ANALYZE,
        run_cash_flow,
        (
            "start_date",
            "end_date",
        ),
    ),
    "detect_spending_anomalies": RegisteredTool(
        "detect_spending_anomalies",
        (
            "Find deterministic spending "
            "anomalies using prior "
            "merchant/category history."
        ),
        ToolPermission.ANALYZE,
        run_spending_anomalies,
        (
            "start_date",
            "end_date",
            "min_history",
            "threshold_multiplier",
        ),
    ),
}
