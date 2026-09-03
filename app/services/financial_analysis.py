from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


ZERO = Decimal("0.00")
PERCENT_QUANTUM = Decimal("0.01")


@dataclass(frozen=True)
class MonthlySpendingResult:
    year: int
    month: int
    start_date: date
    end_date: date
    transaction_count: int
    total: Decimal


@dataclass(frozen=True)
class CategorySpendingItem:
    category: str | None
    transaction_count: int
    total: Decimal


@dataclass(frozen=True)
class CategorySpendingResult:
    year: int
    month: int
    start_date: date
    end_date: date
    transaction_count: int
    total: Decimal
    categories: list[CategorySpendingItem]


@dataclass(frozen=True)
class SpendingComparisonResult:
    base: MonthlySpendingResult
    comparison: MonthlySpendingResult
    absolute_difference: Decimal
    percentage_difference: Decimal | None


@dataclass(frozen=True)
class RecurringExpenseCandidate:
    key: str
    match_basis: Literal["merchant", "description"]
    transaction_count: int
    first_date: date
    last_date: date
    average_amount: Decimal
    average_interval_days: Decimal


@dataclass(frozen=True)
class RecurringExpensesResult:
    start_date: date
    end_date: date
    candidates: list[RecurringExpenseCandidate]


@dataclass(frozen=True)
class CashFlowResult:
    start_date: date
    end_date: date
    income_count: int
    expense_count: int
    transfer_count: int
    income_total: Decimal
    expense_total: Decimal
    net_cash_flow: Decimal


@dataclass(frozen=True)
class SpendingAnomaly:
    transaction_id: int
    transaction_date: date
    merchant: str | None
    category: str | None
    amount: Decimal
    baseline_amount: Decimal
    threshold_amount: Decimal
    baseline_count: int
    match_basis: Literal["merchant", "category"]


@dataclass(frozen=True)
class SpendingAnomaliesResult:
    start_date: date
    end_date: date
    anomalies: list[SpendingAnomaly]


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


def _validate_date_range(
    *,
    start_date: date,
    end_date: date,
) -> None:
    if end_date <= start_date:
        raise ValueError(
            "end_date must be after start_date"
        )


def _spending_magnitude(
    signed_total: Decimal,
) -> Decimal:
    total = -signed_total

    if total == Decimal("-0.00"):
        return ZERO

    return total


def _amount_magnitude(
    amount: Decimal,
) -> Decimal:
    return abs(amount)


def _normalize_description_key(
    value: str,
) -> str:
    return " ".join(value.upper().split())


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

    total = _spending_magnitude(
        Decimal(raw_total)
    )

    return MonthlySpendingResult(
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date,
        transaction_count=transaction_count,
        total=total,
    )


def get_category_spending(
    session: Session,
    *,
    year: int,
    month: int,
) -> CategorySpendingResult:
    start_date, end_date = _month_bounds(
        year=year,
        month=month,
    )

    statement = (
        select(
            Transaction.category,
            func.count(Transaction.id),
            func.sum(Transaction.amount),
        )
        .where(
            Transaction.transaction_type
            == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .group_by(
            Transaction.category
        )
    )

    rows = session.execute(
        statement
    ).all()

    categories = [
        CategorySpendingItem(
            category=category,
            transaction_count=transaction_count,
            total=_spending_magnitude(
                Decimal(raw_total)
            ),
        )
        for (
            category,
            transaction_count,
            raw_total,
        ) in rows
    ]

    categories.sort(
        key=lambda item: (
            -item.total,
            item.category or "",
        )
    )

    transaction_count = sum(
        item.transaction_count
        for item in categories
    )

    total = sum(
        (
            item.total
            for item in categories
        ),
        ZERO,
    )

    return CategorySpendingResult(
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date,
        transaction_count=transaction_count,
        total=total,
        categories=categories,
    )


def compare_monthly_spending(
    session: Session,
    *,
    base_year: int,
    base_month: int,
    comparison_year: int,
    comparison_month: int,
) -> SpendingComparisonResult:
    base = get_monthly_spending(
        session,
        year=base_year,
        month=base_month,
    )

    comparison = get_monthly_spending(
        session,
        year=comparison_year,
        month=comparison_month,
    )

    absolute_difference = (
        base.total - comparison.total
    )

    if comparison.total == ZERO:
        percentage_difference = None
    else:
        percentage_difference = (
            (
                absolute_difference
                / comparison.total
            )
            * Decimal("100")
        ).quantize(
            PERCENT_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

    return SpendingComparisonResult(
        base=base,
        comparison=comparison,
        absolute_difference=absolute_difference,
        percentage_difference=percentage_difference,
    )


def find_recurring_expenses(
    session: Session,
    *,
    start_date: date,
    end_date: date,
    min_occurrences: int = 3,
    min_interval_days: int = 20,
    max_interval_days: int = 40,
    amount_tolerance: Decimal = Decimal(
        "0.10"
    ),
) -> RecurringExpensesResult:
    _validate_date_range(
        start_date=start_date,
        end_date=end_date,
    )

    if min_occurrences < 2:
        raise ValueError(
            "min_occurrences must be at least 2"
        )

    if min_interval_days < 1:
        raise ValueError(
            "min_interval_days must be positive"
        )

    if max_interval_days < min_interval_days:
        raise ValueError(
            "max_interval_days must be greater than "
            "or equal to min_interval_days"
        )

    if amount_tolerance < ZERO:
        raise ValueError(
            "amount_tolerance must not be negative"
        )

    transactions = session.scalars(
        select(Transaction)
        .where(
            Transaction.transaction_type
            == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .order_by(
            Transaction.date,
            Transaction.id,
        )
    ).all()

    groups: dict[
        tuple[str, str],
        list[Transaction],
    ] = defaultdict(list)

    for transaction in transactions:
        if transaction.merchant:
            basis = "merchant"
            key = transaction.merchant
        else:
            basis = "description"
            key = _normalize_description_key(
                transaction.original_description
            )

        if not key:
            continue

        groups[(basis, key)].append(
            transaction
        )

    candidates: list[
        RecurringExpenseCandidate
    ] = []

    for (
        basis,
        key,
    ), group in groups.items():
        if len(group) < min_occurrences:
            continue

        ordered = sorted(
            group,
            key=lambda transaction: (
                transaction.date,
                transaction.id,
            ),
        )

        intervals = [
            (
                ordered[index].date
                - ordered[index - 1].date
            ).days
            for index in range(
                1,
                len(ordered),
            )
        ]

        if not all(
            min_interval_days
            <= interval
            <= max_interval_days
            for interval in intervals
        ):
            continue

        amounts = [
            _amount_magnitude(
                Decimal(transaction.amount)
            )
            for transaction in ordered
        ]

        average_amount = (
            sum(amounts, ZERO)
            / Decimal(len(amounts))
        )

        if average_amount == ZERO:
            continue

        max_difference = (
            average_amount
            * amount_tolerance
        )

        if not all(
            abs(
                amount - average_amount
            )
            <= max_difference
            for amount in amounts
        ):
            continue

        average_interval_days = (
            Decimal(
                sum(intervals)
            )
            / Decimal(
                len(intervals)
            )
        )

        candidates.append(
            RecurringExpenseCandidate(
                key=key,
                match_basis=basis,
                transaction_count=len(
                    ordered
                ),
                first_date=ordered[0].date,
                last_date=ordered[-1].date,
                average_amount=average_amount,
                average_interval_days=(
                    average_interval_days
                ),
            )
        )

    candidates.sort(
        key=lambda candidate: (
            -candidate.average_amount,
            candidate.key,
        )
    )

    return RecurringExpensesResult(
        start_date=start_date,
        end_date=end_date,
        candidates=candidates,
    )


def get_cash_flow(
    session: Session,
    *,
    start_date: date,
    end_date: date,
) -> CashFlowResult:
    _validate_date_range(
        start_date=start_date,
        end_date=end_date,
    )

    rows = session.execute(
        select(
            Transaction.transaction_type,
            func.count(Transaction.id),
            func.coalesce(
                func.sum(Transaction.amount),
                ZERO,
            ),
        )
        .where(
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.transaction_type.in_(
                (
                    "income",
                    "expense",
                    "transfer",
                )
            ),
        )
        .group_by(
            Transaction.transaction_type
        )
    ).all()

    counts = {
        "income": 0,
        "expense": 0,
        "transfer": 0,
    }

    totals = {
        "income": ZERO,
        "expense": ZERO,
        "transfer": ZERO,
    }

    for (
        transaction_type,
        transaction_count,
        raw_total,
    ) in rows:
        counts[transaction_type] = (
            transaction_count
        )
        totals[transaction_type] = Decimal(
            raw_total
        )

    income_total = totals["income"]

    expense_total = _spending_magnitude(
        totals["expense"]
    )

    net_cash_flow = (
        income_total - expense_total
    )

    return CashFlowResult(
        start_date=start_date,
        end_date=end_date,
        income_count=counts["income"],
        expense_count=counts["expense"],
        transfer_count=counts["transfer"],
        income_total=income_total,
        expense_total=expense_total,
        net_cash_flow=net_cash_flow,
    )


def detect_spending_anomalies(
    session: Session,
    *,
    start_date: date,
    end_date: date,
    min_history: int = 3,
    threshold_multiplier: Decimal = Decimal(
        "2.00"
    ),
) -> SpendingAnomaliesResult:
    _validate_date_range(
        start_date=start_date,
        end_date=end_date,
    )

    if min_history < 1:
        raise ValueError(
            "min_history must be at least 1"
        )

    if threshold_multiplier <= ZERO:
        raise ValueError(
            "threshold_multiplier must be positive"
        )

    candidates = session.scalars(
        select(Transaction)
        .where(
            Transaction.transaction_type
            == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .order_by(
            Transaction.date,
            Transaction.id,
        )
    ).all()

    anomalies: list[SpendingAnomaly] = []

    for transaction in candidates:
        if transaction.merchant:
            match_basis = "merchant"

            history_query = (
                select(Transaction.amount)
                .where(
                    Transaction.transaction_type
                    == "expense",
                    Transaction.merchant
                    == transaction.merchant,
                    Transaction.date
                    < transaction.date,
                )
            )
        elif transaction.category:
            match_basis = "category"

            history_query = (
                select(Transaction.amount)
                .where(
                    Transaction.transaction_type
                    == "expense",
                    Transaction.category
                    == transaction.category,
                    Transaction.date
                    < transaction.date,
                )
            )
        else:
            continue

        history = [
            _amount_magnitude(
                Decimal(amount)
            )
            for amount in session.scalars(
                history_query
            ).all()
        ]

        if len(history) < min_history:
            continue

        baseline_amount = (
            sum(history, ZERO)
            / Decimal(len(history))
        )

        threshold_amount = (
            baseline_amount
            * threshold_multiplier
        )

        amount = _amount_magnitude(
            Decimal(transaction.amount)
        )

        if amount < threshold_amount:
            continue

        anomalies.append(
            SpendingAnomaly(
                transaction_id=transaction.id,
                transaction_date=transaction.date,
                merchant=transaction.merchant,
                category=transaction.category,
                amount=amount,
                baseline_amount=baseline_amount,
                threshold_amount=(
                    threshold_amount
                ),
                baseline_count=len(history),
                match_basis=match_basis,
            )
        )

    anomalies.sort(
        key=lambda anomaly: (
            anomaly.transaction_date,
            anomaly.transaction_id,
        )
    )

    return SpendingAnomaliesResult(
        start_date=start_date,
        end_date=end_date,
        anomalies=anomalies,
    )
