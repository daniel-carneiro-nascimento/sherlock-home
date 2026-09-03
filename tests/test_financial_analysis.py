from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.financial_analysis import (
    MonthlySpendingResult,
    get_monthly_spending,
)


def make_transaction(
    *,
    transaction_date: date,
    amount: Decimal,
    transaction_type: str,
    fingerprint: str,
    category: str | None = None,
    merchant: str | None = None,
) -> Transaction:
    return Transaction(
        date=transaction_date,
        amount=amount,
        transaction_type=transaction_type,
        category=category,
        merchant=merchant,
        statement_month=date(
            transaction_date.year,
            transaction_date.month,
            1,
        ),
        original_description=(
            f"SYNTHETIC {fingerprint}"
        ),
        fingerprint=fingerprint,
    )


def test_monthly_spending_sums_expenses(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    5,
                ),
                amount=Decimal("-10.25"),
                transaction_type="expense",
                fingerprint="expense-1",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    20,
                ),
                amount=Decimal("-20.35"),
                transaction_type="expense",
                fingerprint="expense-2",
            ),
        ]
    )
    db_session.commit()

    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert isinstance(
        result,
        MonthlySpendingResult,
    )

    assert result.transaction_count == 2

    assert result.total == Decimal(
        "30.60"
    )


def test_monthly_spending_excludes_income(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    5,
                ),
                amount=Decimal("-50.00"),
                transaction_type="expense",
                fingerprint="expense-1",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    6,
                ),
                amount=Decimal("500.00"),
                transaction_type="income",
                fingerprint="income-1",
            ),
        ]
    )
    db_session.commit()

    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.transaction_count == 1
    assert result.total == Decimal(
        "50.00"
    )


def test_monthly_spending_excludes_transfers(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    5,
                ),
                amount=Decimal("-15.00"),
                transaction_type="expense",
                fingerprint="expense-1",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    8,
                ),
                amount=Decimal("-200.00"),
                transaction_type="transfer",
                fingerprint="transfer-1",
            ),
        ]
    )
    db_session.commit()

    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.transaction_count == 1
    assert result.total == Decimal(
        "15.00"
    )


def test_monthly_spending_excludes_adjacent_months(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    5,
                    31,
                ),
                amount=Decimal("-100.00"),
                transaction_type="expense",
                fingerprint="may",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    1,
                ),
                amount=Decimal("-20.00"),
                transaction_type="expense",
                fingerprint="june-start",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    30,
                ),
                amount=Decimal("-30.00"),
                transaction_type="expense",
                fingerprint="june-end",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    1,
                ),
                amount=Decimal("-200.00"),
                transaction_type="expense",
                fingerprint="july",
            ),
        ]
    )
    db_session.commit()

    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.transaction_count == 2
    assert result.total == Decimal(
        "50.00"
    )


def test_monthly_spending_empty_month_returns_zero(
    db_session: Session,
):
    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.transaction_count == 0

    assert result.total == Decimal(
        "0.00"
    )


def test_monthly_spending_returns_month_bounds(
    db_session: Session,
):
    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.start_date == date(
        2026,
        6,
        1,
    )

    assert result.end_date == date(
        2026,
        7,
        1,
    )


def test_monthly_spending_handles_december_boundary(
    db_session: Session,
):
    result = get_monthly_spending(
        db_session,
        year=2026,
        month=12,
    )

    assert result.start_date == date(
        2026,
        12,
        1,
    )

    assert result.end_date == date(
        2027,
        1,
        1,
    )


@pytest.mark.parametrize(
    "month",
    [
        0,
        13,
        -1,
    ],
)
def test_monthly_spending_rejects_invalid_month(
    db_session: Session,
    month: int,
):
    with pytest.raises(
        ValueError,
        match=(
            "month must be between 1 and 12"
        ),
    ):
        get_monthly_spending(
            db_session,
            year=2026,
            month=month,
        )


def test_monthly_spending_preserves_decimal_precision(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    1,
                ),
                amount=Decimal("-0.10"),
                transaction_type="expense",
                fingerprint="decimal-1",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    6,
                    2,
                ),
                amount=Decimal("-0.20"),
                transaction_type="expense",
                fingerprint="decimal-2",
            ),
        ]
    )
    db_session.commit()

    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.total == Decimal(
        "0.30"
    )
