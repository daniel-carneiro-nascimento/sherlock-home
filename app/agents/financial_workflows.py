from __future__ import annotations

from datetime import date

from app.agents.tool_planning import ToolPlan
from app.tools.schemas import ToolCall


def _previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _months_ago_start(*, year: int, month: int, months: int) -> date:
    index = year * 12 + (month - 1) - months
    result_year, zero_month = divmod(index, 12)
    return date(result_year, zero_month + 1, 1)


def _next_month_start(*, year: int, month: int) -> date:
    return date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)


def spending_reduction_workflow(*, today: date) -> ToolPlan:
    year = today.year
    month = today.month
    previous_year, previous_month = _previous_month(year, month)
    recurring_start = _months_ago_start(year=year, month=month, months=3)
    recurring_end = _next_month_start(year=year, month=month)

    return ToolPlan(
        calls=(
            ToolCall(
                "get_monthly_spending",
                {"year": year, "month": month},
            ),
            ToolCall(
                "get_category_spending",
                {"year": year, "month": month},
            ),
            ToolCall(
                "compare_monthly_spending",
                {
                    "base_year": year,
                    "base_month": month,
                    "comparison_year": previous_year,
                    "comparison_month": previous_month,
                },
            ),
            ToolCall(
                "find_recurring_expenses",
                {
                    "start_date": recurring_start.isoformat(),
                    "end_date": recurring_end.isoformat(),
                },
            ),
        ),
        answer_instruction=(
            "Explain practical opportunities to reduce current-month spending "
            "using only the returned evidence. Distinguish facts from suggestions."
        ),
    )
