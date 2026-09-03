from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


ZERO = Decimal("0.00")


@dataclass(frozen=True)
class MonthlySpendingResult:
    year: int
    month: int
    start_date: date
    end_date: date
    transaction_count: int
    total: Decimal


def _month_bounds(
    *,
    year: int,
    month: int,
) -> tuple[date, date]:
    if not 1 <= month <= 12:
        raise ValueError(
            "month must be between 1 and 12"
        )

    start_date = date(
        year,
        month,
        1,
    )

    if month == 12:
        end_date = date(
            year + 1,
            1,
            1,
        )
    else:
        end_date = date(
            year,
            month + 1,
            1,
        )

    return start_date, end_date


def get_monthly_spending(
    session: Session,
    *,
    year: int,
    month: int,
) -> MonthlySpendingResult:
    start_date, end_date = _month_bounds(
        year=year,
        month=month,
    )

    statement = (
        select(
            func.count(Transaction.id),
            func.coalesce(
                func.sum(Transaction.amount),
                ZERO,
            ),
        )
        .where(
            Transaction.transaction_type
            == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
    )

    transaction_count, raw_total = (
        session.execute(statement).one()
    )

    signed_total = Decimal(raw_total)

    # Persisted bank movements currently preserve their
    # source sign convention:
    #
    # expense -> negative
    #
    # Analytical spending is exposed as a positive
    # magnitude.
    total = -signed_total

    if total == Decimal("-0.00"):
        total = ZERO

    return MonthlySpendingResult(
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date,
        transaction_count=transaction_count,
        total=total,
    )
