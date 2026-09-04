from __future__ import annotations

from datetime import date, timedelta
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
from app.tools.schemas import to_json_safe


ToolHandler = Callable[[Session, dict[str, Any]], object]

FINANCIAL_CURRENCY = "BRL"


class ToolArgumentError(ValueError):
    pass


def _reject_unknown_arguments(
    arguments: dict[str, Any],
    *,
    allowed: set[str],
) -> None:
    unknown = set(arguments) - allowed

    if unknown:
        raise ToolArgumentError(
            "unknown tool argument(s): "
            + ", ".join(sorted(unknown))
        )


def _required_int(
    arguments: dict[str, Any],
    name: str,
) -> int:
    value = arguments.get(name)

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
    ):
        raise ToolArgumentError(
            f"{name} must be an integer"
        )

    return value


def _required_date(
    arguments: dict[str, Any],
    name: str,
) -> date:
    value = arguments.get(name)

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise ToolArgumentError(
            f"{name} must be an ISO date"
        )

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ToolArgumentError(
            f"{name} must be an ISO date"
        ) from exc


def _optional_int(
    arguments: dict[str, Any],
    name: str,
    default: int,
) -> int:
    return (
        default
        if name not in arguments
        else _required_int(
            arguments,
            name,
        )
    )


def _optional_decimal(
    arguments: dict[str, Any],
    name: str,
    default: Decimal,
) -> Decimal:
    if name not in arguments:
        return default

    value = arguments[name]

    if isinstance(value, bool):
        raise ToolArgumentError(
            f"{name} must be a decimal value"
        )

    if isinstance(
        value,
        (
            str,
            int,
            float,
            Decimal,
        ),
    ):
        try:
            return Decimal(
                str(value)
            )
        except Exception as exc:
            raise ToolArgumentError(
                f"{name} must be a decimal value"
            ) from exc

    raise ToolArgumentError(
        f"{name} must be a decimal value"
    )


def _calendar_month_span(
    *,
    start_date: date,
    end_date: date,
) -> int:
    """
    Return the number of calendar months touched by a half-open date range.

    Example:
        2026-06-01 <= date < 2026-08-01
        touches June and July -> 2 months.
    """
    if end_date <= start_date:
        raise ToolArgumentError(
            "end_date must be after start_date"
        )

    last_included_date = (
        end_date - timedelta(days=1)
    )

    return (
        (
            last_included_date.year
            - start_date.year
        )
        * 12
        + (
            last_included_date.month
            - start_date.month
        )
        + 1
    )


def _recurrence_min_occurrences(
    *,
    start_date: date,
    end_date: date,
) -> int:
    """
    Deterministic recurrence policy owned by Sherlock Home.

    A requested range touching one or two calendar months requires two
    matching occurrences. A range touching three or more calendar months
    requires at least three matching occurrences.

    The model cannot override this threshold.
    """
    month_span = _calendar_month_span(
        start_date=start_date,
        end_date=end_date,
    )

    if month_span <= 2:
        return 2

    return 3


def _financial_evidence(
    result: object,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    serialized = to_json_safe(
        result
    )

    if not isinstance(
        serialized,
        dict,
    ):
        raise TypeError(
            "financial tool result must "
            "serialize to an object"
        )

    evidence = {
        "currency": FINANCIAL_CURRENCY,
        **serialized,
    }

    if metadata:
        evidence.update(
            to_json_safe(metadata)
        )

    return evidence


def run_monthly_spending(
    session: Session,
    arguments: dict[str, Any],
) -> object:
    _reject_unknown_arguments(
        arguments,
        allowed={
            "year",
            "month",
        },
    )

    result = get_monthly_spending(
        session,
        year=_required_int(
            arguments,
            "year",
        ),
        month=_required_int(
            arguments,
            "month",
        ),
    )

    return _financial_evidence(
        result
    )


def run_category_spending(
    session: Session,
    arguments: dict[str, Any],
) -> object:
    _reject_unknown_arguments(
        arguments,
        allowed={
            "year",
            "month",
        },
    )

    result = get_category_spending(
        session,
        year=_required_int(
            arguments,
            "year",
        ),
        month=_required_int(
            arguments,
            "month",
        ),
    )

    return _financial_evidence(
        result
    )


def run_spending_comparison(
    session: Session,
    arguments: dict[str, Any],
) -> object:
    allowed = {
        "base_year",
        "base_month",
        "comparison_year",
        "comparison_month",
    }

    _reject_unknown_arguments(
        arguments,
        allowed=allowed,
    )

    result = compare_monthly_spending(
        session,
        base_year=_required_int(
            arguments,
            "base_year",
        ),
        base_month=_required_int(
            arguments,
            "base_month",
        ),
        comparison_year=_required_int(
            arguments,
            "comparison_year",
        ),
        comparison_month=_required_int(
            arguments,
            "comparison_month",
        ),
    )

    return _financial_evidence(
        result
    )


def run_recurring_expenses(
    session: Session,
    arguments: dict[str, Any],
) -> object:
    # min_occurrences is intentionally not accepted from the model.
    # It is derived by deterministic server-owned policy.
    allowed = {
        "start_date",
        "end_date",
        "min_interval_days",
        "max_interval_days",
        "amount_tolerance",
    }

    _reject_unknown_arguments(
        arguments,
        allowed=allowed,
    )

    start_date = _required_date(
        arguments,
        "start_date",
    )
    end_date = _required_date(
        arguments,
        "end_date",
    )

    min_occurrences = (
        _recurrence_min_occurrences(
            start_date=start_date,
            end_date=end_date,
        )
    )

    min_interval_days = (
        _optional_int(
            arguments,
            "min_interval_days",
            20,
        )
    )
    max_interval_days = (
        _optional_int(
            arguments,
            "max_interval_days",
            40,
        )
    )
    amount_tolerance = (
        _optional_decimal(
            arguments,
            "amount_tolerance",
            Decimal("0.10"),
        )
    )

    result = find_recurring_expenses(
        session,
        start_date=start_date,
        end_date=end_date,
        min_occurrences=min_occurrences,
        min_interval_days=(
            min_interval_days
        ),
        max_interval_days=(
            max_interval_days
        ),
        amount_tolerance=(
            amount_tolerance
        ),
    )

    return _financial_evidence(
        result,
        metadata={
            "recurrence_policy": {
                "min_occurrences": (
                    min_occurrences
                ),
                "calendar_month_span": (
                    _calendar_month_span(
                        start_date=start_date,
                        end_date=end_date,
                    )
                ),
                "min_interval_days": (
                    min_interval_days
                ),
                "max_interval_days": (
                    max_interval_days
                ),
                "amount_tolerance": (
                    amount_tolerance
                ),
            }
        },
    )


def run_cash_flow(
    session: Session,
    arguments: dict[str, Any],
) -> object:
    _reject_unknown_arguments(
        arguments,
        allowed={
            "start_date",
            "end_date",
        },
    )

    result = get_cash_flow(
        session,
        start_date=_required_date(
            arguments,
            "start_date",
        ),
        end_date=_required_date(
            arguments,
            "end_date",
        ),
    )

    return _financial_evidence(
        result
    )


def run_spending_anomalies(
    session: Session,
    arguments: dict[str, Any],
) -> object:
    allowed = {
        "start_date",
        "end_date",
        "min_history",
        "threshold_multiplier",
    }

    _reject_unknown_arguments(
        arguments,
        allowed=allowed,
    )

    min_history = _optional_int(
        arguments,
        "min_history",
        3,
    )
    threshold_multiplier = (
        _optional_decimal(
            arguments,
            "threshold_multiplier",
            Decimal("2.00"),
        )
    )

    result = detect_spending_anomalies(
        session,
        start_date=_required_date(
            arguments,
            "start_date",
        ),
        end_date=_required_date(
            arguments,
            "end_date",
        ),
        min_history=min_history,
        threshold_multiplier=(
            threshold_multiplier
        ),
    )

    # SpendingAnomaly already contains deterministic baseline_amount,
    # threshold_amount, and baseline_count. The metadata below makes the
    # active policy explicit to the responder and future API consumers.
    return _financial_evidence(
        result,
        metadata={
            "anomaly_policy": {
                "min_history": min_history,
                "threshold_multiplier": (
                    threshold_multiplier
                ),
                "explanation_fields": [
                    "baseline_amount",
                    "threshold_amount",
                    "baseline_count",
                ],
            }
        },
    )
