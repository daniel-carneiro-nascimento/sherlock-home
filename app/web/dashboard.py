from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.duplicate_charge_analysis import (
    detect_duplicate_charges,
)
from app.services.financial_analysis import (
    compare_monthly_spending,
    detect_spending_anomalies,
    find_recurring_expenses,
    get_cash_flow,
    get_category_spending,
    get_monthly_spending,
)


@dataclass(frozen=True)
class DashboardPeriod:
    year: int
    month: int
    start_date: date
    end_date: date
    previous_year: int
    previous_month: int


@dataclass(frozen=True)
class DashboardViewModel:
    period: DashboardPeriod
    spending_total: Decimal
    transaction_count: int
    income_total: Decimal
    expense_total: Decimal
    net_cash_flow: Decimal
    comparison_percent: Decimal | None
    comparison_difference: Decimal
    categories: tuple[tuple[str, Decimal], ...]
    recurring: tuple[dict[str, object], ...]
    anomalies: tuple[dict[str, object], ...]
    duplicates: tuple[dict[str, object], ...]


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _period_for_latest_transaction(
    session: Session,
) -> DashboardPeriod:
    latest = session.scalar(
        select(func.max(Transaction.date))
    )

    if latest is None:
        today = date.today()
        year = today.year
        month = today.month
    else:
        year = latest.year
        month = latest.month

    next_year, next_month = _next_month(
        year,
        month,
    )
    previous_year, previous_month = (
        _previous_month(
            year,
            month,
        )
    )

    return DashboardPeriod(
        year=year,
        month=month,
        start_date=date(
            year,
            month,
            1,
        ),
        end_date=date(
            next_year,
            next_month,
            1,
        ),
        previous_year=previous_year,
        previous_month=previous_month,
    )


def build_dashboard(
    session: Session,
) -> DashboardViewModel:
    """
    Build the first server-rendered dashboard from the latest month
    available in the local transaction database.

    Current backend data is still single-household. User/account scoping
    belongs to the later household data model and must not be simulated here.
    """
    period = _period_for_latest_transaction(
        session
    )

    spending = get_monthly_spending(
        session,
        year=period.year,
        month=period.month,
    )

    categories = get_category_spending(
        session,
        year=period.year,
        month=period.month,
    )

    cash_flow = get_cash_flow(
        session,
        start_date=period.start_date,
        end_date=period.end_date,
    )

    comparison = compare_monthly_spending(
        session,
        base_year=period.year,
        base_month=period.month,
        comparison_year=(
            period.previous_year
        ),
        comparison_month=(
            period.previous_month
        ),
    )

    recurrence_start = date(
        period.previous_year,
        period.previous_month,
        1,
    )

    recurring_result = (
        find_recurring_expenses(
            session,
            start_date=recurrence_start,
            end_date=period.end_date,
            min_occurrences=2,
        )
    )

    anomalies_result = (
        detect_spending_anomalies(
            session,
            start_date=period.start_date,
            end_date=period.end_date,
        )
    )

    duplicates_result = (
        detect_duplicate_charges(
            session,
            start_date=period.start_date,
            end_date=period.end_date,
        )
    )

    recurring = tuple(
        {
            "name": candidate.key,
            "count": (
                candidate.transaction_count
            ),
            "average_amount": (
                candidate.average_amount
            ),
            "interval_days": (
                candidate.average_interval_days
            ),
        }
        for candidate
        in recurring_result.candidates[:5]
    )

    anomalies = tuple(
        {
            "merchant": (
                item.merchant
                or item.category
                or "Despesa"
            ),
            "amount": item.amount,
            "baseline": (
                item.baseline_amount
            ),
            "threshold": (
                item.threshold_amount
            ),
            "baseline_count": (
                item.baseline_count
            ),
            "date": (
                item.transaction_date
            ),
        }
        for item
        in anomalies_result.anomalies[:5]
    )

    duplicates = tuple(
        {
            "merchant": item.merchant,
            "amount": item.amount,
            "date": (
                item.transaction_date
            ),
            "occurrences": (
                item.occurrences
            ),
        }
        for item
        in duplicates_result.candidates[:5]
    )

    category_rows = tuple(
        (
            item.category
            or "Sem categoria",
            item.total,
        )
        for item in categories.categories
    )

    return DashboardViewModel(
        period=period,
        spending_total=spending.total,
        transaction_count=(
            spending.transaction_count
        ),
        income_total=(
            cash_flow.income_total
        ),
        expense_total=(
            cash_flow.expense_total
        ),
        net_cash_flow=(
            cash_flow.net_cash_flow
        ),
        comparison_percent=(
            comparison.percentage_difference
        ),
        comparison_difference=(
            comparison.absolute_difference
        ),
        categories=category_rows,
        recurring=recurring,
        anomalies=anomalies,
        duplicates=duplicates,
    )
