from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.financial_analysis import (
    CategorySpendingResult,
    CashFlowResult,
    MonthlySpendingResult,
    RecurringExpensesResult,
    SpendingAnomaliesResult,
    SpendingComparisonResult,
    compare_monthly_spending,
    detect_spending_anomalies,
    find_recurring_expenses,
    get_cash_flow,
    get_category_spending,
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
    description: str | None = None,
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
            description
            or f"SYNTHETIC {fingerprint}"
        ),
        fingerprint=fingerprint,
    )


# ---------------------------------------------------------------------------
# Monthly spending
# ---------------------------------------------------------------------------


def test_monthly_spending_sums_expenses(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 5),
                amount=Decimal("-10.25"),
                transaction_type="expense",
                fingerprint="monthly-expense-1",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 20),
                amount=Decimal("-20.35"),
                transaction_type="expense",
                fingerprint="monthly-expense-2",
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
    assert result.total == Decimal("30.60")


def test_monthly_spending_excludes_income_and_transfer(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 5),
                amount=Decimal("-50.00"),
                transaction_type="expense",
                fingerprint="monthly-expense",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 6),
                amount=Decimal("500.00"),
                transaction_type="income",
                fingerprint="monthly-income",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 7),
                amount=Decimal("-200.00"),
                transaction_type="transfer",
                fingerprint="monthly-transfer",
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
    assert result.total == Decimal("50.00")


def test_monthly_spending_excludes_adjacent_months(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 5, 31),
                amount=Decimal("-100.00"),
                transaction_type="expense",
                fingerprint="monthly-may",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 1),
                amount=Decimal("-20.00"),
                transaction_type="expense",
                fingerprint="monthly-june-start",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 30),
                amount=Decimal("-30.00"),
                transaction_type="expense",
                fingerprint="monthly-june-end",
            ),
            make_transaction(
                transaction_date=date(2026, 7, 1),
                amount=Decimal("-200.00"),
                transaction_type="expense",
                fingerprint="monthly-july",
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
    assert result.total == Decimal("50.00")


def test_monthly_spending_empty_month_returns_zero(
    db_session: Session,
):
    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.transaction_count == 0
    assert result.total == Decimal("0.00")


def test_monthly_spending_returns_month_bounds(
    db_session: Session,
):
    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.start_date == date(2026, 6, 1)
    assert result.end_date == date(2026, 7, 1)


def test_monthly_spending_handles_december_boundary(
    db_session: Session,
):
    result = get_monthly_spending(
        db_session,
        year=2026,
        month=12,
    )

    assert result.start_date == date(2026, 12, 1)
    assert result.end_date == date(2027, 1, 1)


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
        match="month must be between 1 and 12",
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
                transaction_date=date(2026, 6, 1),
                amount=Decimal("-0.10"),
                transaction_type="expense",
                fingerprint="monthly-decimal-1",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 2),
                amount=Decimal("-0.20"),
                transaction_type="expense",
                fingerprint="monthly-decimal-2",
            ),
        ]
    )
    db_session.commit()

    result = get_monthly_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.total == Decimal("0.30")


# ---------------------------------------------------------------------------
# Category spending
# ---------------------------------------------------------------------------


def test_category_spending_groups_expenses(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 5),
                amount=Decimal("-10.00"),
                transaction_type="expense",
                category="food",
                fingerprint="category-food-1",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 6),
                amount=Decimal("-20.00"),
                transaction_type="expense",
                category="food",
                fingerprint="category-food-2",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 7),
                amount=Decimal("-15.00"),
                transaction_type="expense",
                category="transport",
                fingerprint="category-transport",
            ),
        ]
    )
    db_session.commit()

    result = get_category_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert isinstance(
        result,
        CategorySpendingResult,
    )
    assert result.transaction_count == 3
    assert result.total == Decimal("45.00")

    by_category = {
        item.category: item
        for item in result.categories
    }

    assert (
        by_category["food"].transaction_count
        == 2
    )
    assert (
        by_category["food"].total
        == Decimal("30.00")
    )
    assert (
        by_category["transport"].total
        == Decimal("15.00")
    )


def test_category_spending_preserves_uncategorized_expenses(
    db_session: Session,
):
    db_session.add(
        make_transaction(
            transaction_date=date(2026, 6, 3),
            amount=Decimal("-12.50"),
            transaction_type="expense",
            category=None,
            fingerprint="category-uncategorized",
        )
    )
    db_session.commit()

    result = get_category_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert len(result.categories) == 1
    assert result.categories[0].category is None
    assert (
        result.categories[0].total
        == Decimal("12.50")
    )


def test_category_spending_is_sorted_by_total_descending(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 1),
                amount=Decimal("-10.00"),
                transaction_type="expense",
                category="food",
                fingerprint="category-order-food",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 2),
                amount=Decimal("-50.00"),
                transaction_type="expense",
                category="transport",
                fingerprint="category-order-transport",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 3),
                amount=Decimal("-25.00"),
                transaction_type="expense",
                category="shopping",
                fingerprint="category-order-shopping",
            ),
        ]
    )
    db_session.commit()

    result = get_category_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert [
        item.category
        for item in result.categories
    ] == [
        "transport",
        "shopping",
        "food",
    ]


def test_category_spending_empty_month(
    db_session: Session,
):
    result = get_category_spending(
        db_session,
        year=2026,
        month=6,
    )

    assert result.transaction_count == 0
    assert result.total == Decimal("0.00")
    assert result.categories == []


# ---------------------------------------------------------------------------
# Spending comparison
# ---------------------------------------------------------------------------


def test_spending_comparison_reuses_monthly_semantics(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 1),
                amount=Decimal("-150.00"),
                transaction_type="expense",
                fingerprint="compare-june",
            ),
            make_transaction(
                transaction_date=date(2026, 5, 1),
                amount=Decimal("-100.00"),
                transaction_type="expense",
                fingerprint="compare-may",
            ),
        ]
    )
    db_session.commit()

    result = compare_monthly_spending(
        db_session,
        base_year=2026,
        base_month=6,
        comparison_year=2026,
        comparison_month=5,
    )

    assert isinstance(
        result,
        SpendingComparisonResult,
    )
    assert result.base.total == Decimal("150.00")
    assert (
        result.comparison.total
        == Decimal("100.00")
    )
    assert (
        result.absolute_difference
        == Decimal("50.00")
    )
    assert (
        result.percentage_difference
        == Decimal("50.00")
    )


def test_spending_comparison_can_be_negative(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 1),
                amount=Decimal("-80.00"),
                transaction_type="expense",
                fingerprint="compare-lower-base",
            ),
            make_transaction(
                transaction_date=date(2026, 5, 1),
                amount=Decimal("-100.00"),
                transaction_type="expense",
                fingerprint="compare-higher-reference",
            ),
        ]
    )
    db_session.commit()

    result = compare_monthly_spending(
        db_session,
        base_year=2026,
        base_month=6,
        comparison_year=2026,
        comparison_month=5,
    )

    assert (
        result.absolute_difference
        == Decimal("-20.00")
    )
    assert (
        result.percentage_difference
        == Decimal("-20.00")
    )


def test_spending_comparison_zero_reference_has_no_percentage(
    db_session: Session,
):
    db_session.add(
        make_transaction(
            transaction_date=date(2026, 6, 1),
            amount=Decimal("-50.00"),
            transaction_type="expense",
            fingerprint="compare-zero-reference",
        )
    )
    db_session.commit()

    result = compare_monthly_spending(
        db_session,
        base_year=2026,
        base_month=6,
        comparison_year=2026,
        comparison_month=5,
    )

    assert result.base.total == Decimal("50.00")
    assert result.comparison.total == Decimal("0.00")
    assert result.percentage_difference is None


# ---------------------------------------------------------------------------
# Recurring expenses
# ---------------------------------------------------------------------------


def test_recurring_expenses_detect_monthly_merchant_pattern(
    db_session: Session,
):
    for index, transaction_date in enumerate(
        [
            date(2026, 1, 10),
            date(2026, 2, 10),
            date(2026, 3, 10),
        ],
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("-49.90"),
                transaction_type="expense",
                merchant="SYNTHETIC STREAM",
                category="leisure",
                fingerprint=f"recurring-merchant-{index}",
            )
        )

    db_session.commit()

    result = find_recurring_expenses(
        db_session,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 1),
    )

    assert isinstance(
        result,
        RecurringExpensesResult,
    )
    assert len(result.candidates) == 1

    candidate = result.candidates[0]

    assert candidate.key == "SYNTHETIC STREAM"
    assert candidate.match_basis == "merchant"
    assert candidate.transaction_count == 3
    assert (
        candidate.average_amount
        == Decimal("49.90")
    )


def test_recurring_expenses_falls_back_to_description(
    db_session: Session,
):
    for index, transaction_date in enumerate(
        [
            date(2026, 1, 5),
            date(2026, 2, 5),
            date(2026, 3, 5),
        ],
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("-30.00"),
                transaction_type="expense",
                merchant=None,
                description="  synthetic   service  ",
                fingerprint=f"recurring-description-{index}",
            )
        )

    db_session.commit()

    result = find_recurring_expenses(
        db_session,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 1),
    )

    assert len(result.candidates) == 1
    assert (
        result.candidates[0].key
        == "SYNTHETIC SERVICE"
    )
    assert (
        result.candidates[0].match_basis
        == "description"
    )


def test_recurring_expenses_reject_irregular_intervals(
    db_session: Session,
):
    for index, transaction_date in enumerate(
        [
            date(2026, 1, 1),
            date(2026, 1, 5),
            date(2026, 3, 20),
        ],
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("-20.00"),
                transaction_type="expense",
                merchant="SYNTHETIC IRREGULAR",
                fingerprint=f"recurring-irregular-{index}",
            )
        )

    db_session.commit()

    result = find_recurring_expenses(
        db_session,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 1),
    )

    assert result.candidates == []


def test_recurring_expenses_reject_amount_variation_beyond_tolerance(
    db_session: Session,
):
    amounts = [
        Decimal("-10.00"),
        Decimal("-10.00"),
        Decimal("-30.00"),
    ]

    dates = [
        date(2026, 1, 10),
        date(2026, 2, 10),
        date(2026, 3, 10),
    ]

    for index, (
        transaction_date,
        amount,
    ) in enumerate(
        zip(dates, amounts),
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=amount,
                transaction_type="expense",
                merchant="SYNTHETIC VARIABLE",
                fingerprint=f"recurring-variable-{index}",
            )
        )

    db_session.commit()

    result = find_recurring_expenses(
        db_session,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 1),
        amount_tolerance=Decimal("0.10"),
    )

    assert result.candidates == []


def test_recurring_expenses_excludes_income_and_transfer(
    db_session: Session,
):
    for index, transaction_date in enumerate(
        [
            date(2026, 1, 10),
            date(2026, 2, 10),
            date(2026, 3, 10),
        ],
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("100.00"),
                transaction_type="income",
                merchant="SYNTHETIC INCOME",
                fingerprint=f"recurring-income-{index}",
            )
        )

        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("-100.00"),
                transaction_type="transfer",
                merchant="SYNTHETIC TRANSFER",
                fingerprint=f"recurring-transfer-{index}",
            )
        )

    db_session.commit()

    result = find_recurring_expenses(
        db_session,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 4, 1),
    )

    assert result.candidates == []


@pytest.mark.parametrize(
    (
        "kwargs",
        "message",
    ),
    [
        (
            {
                "min_occurrences": 1,
            },
            "min_occurrences must be at least 2",
        ),
        (
            {
                "min_interval_days": 0,
            },
            "min_interval_days must be positive",
        ),
        (
            {
                "min_interval_days": 40,
                "max_interval_days": 20,
            },
            "max_interval_days must be greater",
        ),
        (
            {
                "amount_tolerance": Decimal("-0.01"),
            },
            "amount_tolerance must not be negative",
        ),
    ],
)
def test_recurring_expenses_validates_configuration(
    db_session: Session,
    kwargs: dict,
    message: str,
):
    with pytest.raises(
        ValueError,
        match=message,
    ):
        find_recurring_expenses(
            db_session,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 4, 1),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Cash flow
# ---------------------------------------------------------------------------


def test_cash_flow_separates_income_expense_and_transfer(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 1),
                amount=Decimal("1000.00"),
                transaction_type="income",
                fingerprint="cash-income",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 2),
                amount=Decimal("-250.00"),
                transaction_type="expense",
                fingerprint="cash-expense",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 3),
                amount=Decimal("-500.00"),
                transaction_type="transfer",
                fingerprint="cash-transfer",
            ),
        ]
    )
    db_session.commit()

    result = get_cash_flow(
        db_session,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
    )

    assert isinstance(
        result,
        CashFlowResult,
    )
    assert result.income_count == 1
    assert result.expense_count == 1
    assert result.transfer_count == 1
    assert (
        result.income_total
        == Decimal("1000.00")
    )
    assert (
        result.expense_total
        == Decimal("250.00")
    )
    assert (
        result.net_cash_flow
        == Decimal("750.00")
    )


def test_cash_flow_can_be_negative(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 6, 1),
                amount=Decimal("100.00"),
                transaction_type="income",
                fingerprint="cash-negative-income",
            ),
            make_transaction(
                transaction_date=date(2026, 6, 2),
                amount=Decimal("-300.00"),
                transaction_type="expense",
                fingerprint="cash-negative-expense",
            ),
        ]
    )
    db_session.commit()

    result = get_cash_flow(
        db_session,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
    )

    assert (
        result.net_cash_flow
        == Decimal("-200.00")
    )


def test_cash_flow_empty_period_returns_zero(
    db_session: Session,
):
    result = get_cash_flow(
        db_session,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 7, 1),
    )

    assert result.income_count == 0
    assert result.expense_count == 0
    assert result.transfer_count == 0
    assert result.income_total == Decimal("0.00")
    assert result.expense_total == Decimal("0.00")
    assert result.net_cash_flow == Decimal("0.00")


# ---------------------------------------------------------------------------
# Deterministic anomaly detection
# ---------------------------------------------------------------------------


def test_anomaly_detection_uses_merchant_history(
    db_session: Session,
):
    for index, transaction_date in enumerate(
        [
            date(2026, 1, 1),
            date(2026, 2, 1),
            date(2026, 3, 1),
        ],
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("-20.00"),
                transaction_type="expense",
                merchant="SYNTHETIC SHOP",
                category="shopping",
                fingerprint=f"anomaly-history-{index}",
            )
        )

    db_session.add(
        make_transaction(
            transaction_date=date(2026, 4, 1),
            amount=Decimal("-50.00"),
            transaction_type="expense",
            merchant="SYNTHETIC SHOP",
            category="shopping",
            fingerprint="anomaly-current",
        )
    )
    db_session.commit()

    result = detect_spending_anomalies(
        db_session,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 5, 1),
        min_history=3,
        threshold_multiplier=Decimal("2.00"),
    )

    assert isinstance(
        result,
        SpendingAnomaliesResult,
    )
    assert len(result.anomalies) == 1

    anomaly = result.anomalies[0]

    assert anomaly.match_basis == "merchant"
    assert anomaly.baseline_count == 3
    assert (
        anomaly.baseline_amount
        == Decimal("20.00")
    )
    assert (
        anomaly.threshold_amount
        == Decimal("40.0000")
    )
    assert anomaly.amount == Decimal("50.00")


def test_anomaly_detection_falls_back_to_category(
    db_session: Session,
):
    for index, transaction_date in enumerate(
        [
            date(2026, 1, 1),
            date(2026, 2, 1),
            date(2026, 3, 1),
        ],
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("-10.00"),
                transaction_type="expense",
                merchant=None,
                category="food",
                fingerprint=f"anomaly-category-history-{index}",
            )
        )

    db_session.add(
        make_transaction(
            transaction_date=date(2026, 4, 1),
            amount=Decimal("-25.00"),
            transaction_type="expense",
            merchant=None,
            category="food",
            fingerprint="anomaly-category-current",
        )
    )
    db_session.commit()

    result = detect_spending_anomalies(
        db_session,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 5, 1),
    )

    assert len(result.anomalies) == 1
    assert (
        result.anomalies[0].match_basis
        == "category"
    )


def test_anomaly_detection_does_not_flag_normal_expense(
    db_session: Session,
):
    for index, transaction_date in enumerate(
        [
            date(2026, 1, 1),
            date(2026, 2, 1),
            date(2026, 3, 1),
        ],
        start=1,
    ):
        db_session.add(
            make_transaction(
                transaction_date=transaction_date,
                amount=Decimal("-20.00"),
                transaction_type="expense",
                merchant="SYNTHETIC NORMAL",
                fingerprint=f"anomaly-normal-history-{index}",
            )
        )

    db_session.add(
        make_transaction(
            transaction_date=date(2026, 4, 1),
            amount=Decimal("-25.00"),
            transaction_type="expense",
            merchant="SYNTHETIC NORMAL",
            fingerprint="anomaly-normal-current",
        )
    )
    db_session.commit()

    result = detect_spending_anomalies(
        db_session,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 5, 1),
    )

    assert result.anomalies == []


def test_anomaly_detection_requires_enough_history(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(2026, 3, 1),
                amount=Decimal("-10.00"),
                transaction_type="expense",
                merchant="SYNTHETIC NEW",
                fingerprint="anomaly-short-history",
            ),
            make_transaction(
                transaction_date=date(2026, 4, 1),
                amount=Decimal("-1000.00"),
                transaction_type="expense",
                merchant="SYNTHETIC NEW",
                fingerprint="anomaly-short-current",
            ),
        ]
    )
    db_session.commit()

    result = detect_spending_anomalies(
        db_session,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 5, 1),
        min_history=3,
    )

    assert result.anomalies == []


def test_anomaly_detection_ignores_uncategorized_without_merchant(
    db_session: Session,
):
    db_session.add(
        make_transaction(
            transaction_date=date(2026, 4, 1),
            amount=Decimal("-1000.00"),
            transaction_type="expense",
            merchant=None,
            category=None,
            fingerprint="anomaly-no-basis",
        )
    )
    db_session.commit()

    result = detect_spending_anomalies(
        db_session,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 5, 1),
    )

    assert result.anomalies == []


@pytest.mark.parametrize(
    (
        "kwargs",
        "message",
    ),
    [
        (
            {
                "min_history": 0,
            },
            "min_history must be at least 1",
        ),
        (
            {
                "threshold_multiplier": Decimal("0"),
            },
            "threshold_multiplier must be positive",
        ),
    ],
)
def test_anomaly_detection_validates_configuration(
    db_session: Session,
    kwargs: dict,
    message: str,
):
    with pytest.raises(
        ValueError,
        match=message,
    ):
        detect_spending_anomalies(
            db_session,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 5, 1),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Shared range validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "function_name",
    [
        "recurring",
        "cash_flow",
        "anomaly",
    ],
)
def test_range_based_tools_reject_invalid_range(
    db_session: Session,
    function_name: str,
):
    start_date = date(2026, 6, 1)
    end_date = date(2026, 6, 1)

    with pytest.raises(
        ValueError,
        match="end_date must be after start_date",
    ):
        if function_name == "recurring":
            find_recurring_expenses(
                db_session,
                start_date=start_date,
                end_date=end_date,
            )
        elif function_name == "cash_flow":
            get_cash_flow(
                db_session,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            detect_spending_anomalies(
                db_session,
                start_date=start_date,
                end_date=end_date,
            )
