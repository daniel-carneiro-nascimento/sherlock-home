from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.services.financial_analysis import (
    compare_monthly_spending,
    detect_spending_anomalies,
    find_recurring_expenses,
    get_cash_flow,
    get_category_spending,
    get_monthly_spending,
)


ToolHandler = Callable[[Session, dict[str, Any]], object]


class ToolArgumentError(ValueError):
    pass


def _reject_unknown_arguments(arguments: dict[str, Any], *, allowed: set[str]) -> None:
    unknown = set(arguments) - allowed
    if unknown:
        raise ToolArgumentError(
            "unknown tool argument(s): " + ", ".join(sorted(unknown))
        )


def _required_int(arguments: dict[str, Any], name: str) -> int:
    value = arguments.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ToolArgumentError(f"{name} must be an integer")
    return value


def _required_date(arguments: dict[str, Any], name: str) -> date:
    value = arguments.get(name)
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ToolArgumentError(f"{name} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ToolArgumentError(f"{name} must be an ISO date") from exc


def _optional_int(arguments: dict[str, Any], name: str, default: int) -> int:
    return default if name not in arguments else _required_int(arguments, name)


def _optional_decimal(
    arguments: dict[str, Any],
    name: str,
    default: Decimal,
) -> Decimal:
    if name not in arguments:
        return default
    value = arguments[name]
    if isinstance(value, bool):
        raise ToolArgumentError(f"{name} must be a decimal value")
    if isinstance(value, (str, int, Decimal)):
        try:
            return Decimal(str(value))
        except Exception as exc:
            raise ToolArgumentError(f"{name} must be a decimal value") from exc
    raise ToolArgumentError(f"{name} must be a decimal value")


def run_monthly_spending(session: Session, arguments: dict[str, Any]) -> object:
    _reject_unknown_arguments(arguments, allowed={"year", "month"})
    return get_monthly_spending(
        session,
        year=_required_int(arguments, "year"),
        month=_required_int(arguments, "month"),
    )


def run_category_spending(session: Session, arguments: dict[str, Any]) -> object:
    _reject_unknown_arguments(arguments, allowed={"year", "month"})
    return get_category_spending(
        session,
        year=_required_int(arguments, "year"),
        month=_required_int(arguments, "month"),
    )


def run_spending_comparison(session: Session, arguments: dict[str, Any]) -> object:
    allowed = {"base_year", "base_month", "comparison_year", "comparison_month"}
    _reject_unknown_arguments(arguments, allowed=allowed)
    return compare_monthly_spending(
        session,
        base_year=_required_int(arguments, "base_year"),
        base_month=_required_int(arguments, "base_month"),
        comparison_year=_required_int(arguments, "comparison_year"),
        comparison_month=_required_int(arguments, "comparison_month"),
    )


def run_recurring_expenses(session: Session, arguments: dict[str, Any]) -> object:
    allowed = {
        "start_date", "end_date", "min_occurrences",
        "min_interval_days", "max_interval_days", "amount_tolerance",
    }
    _reject_unknown_arguments(arguments, allowed=allowed)
    return find_recurring_expenses(
        session,
        start_date=_required_date(arguments, "start_date"),
        end_date=_required_date(arguments, "end_date"),
        min_occurrences=_optional_int(arguments, "min_occurrences", 3),
        min_interval_days=_optional_int(arguments, "min_interval_days", 20),
        max_interval_days=_optional_int(arguments, "max_interval_days", 40),
        amount_tolerance=_optional_decimal(
            arguments,
            "amount_tolerance",
            Decimal("0.10"),
        ),
    )


def run_cash_flow(session: Session, arguments: dict[str, Any]) -> object:
    _reject_unknown_arguments(arguments, allowed={"start_date", "end_date"})
    return get_cash_flow(
        session,
        start_date=_required_date(arguments, "start_date"),
        end_date=_required_date(arguments, "end_date"),
    )


def run_spending_anomalies(session: Session, arguments: dict[str, Any]) -> object:
    allowed = {"start_date", "end_date", "min_history", "threshold_multiplier"}
    _reject_unknown_arguments(arguments, allowed=allowed)
    return detect_spending_anomalies(
        session,
        start_date=_required_date(arguments, "start_date"),
        end_date=_required_date(arguments, "end_date"),
        min_history=_optional_int(arguments, "min_history", 3),
        threshold_multiplier=_optional_decimal(
            arguments,
            "threshold_multiplier",
            Decimal("2.00"),
        ),
    )
