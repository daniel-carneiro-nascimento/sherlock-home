from __future__ import annotations

from datetime import date
from decimal import Decimal

import scripts.seed_synthetic_financial_data as seed


def test_seed_contains_two_fourteen_day_windows():
    dates = [
        row["date"]
        for row in seed.TRANSACTIONS
    ]

    june_dates = [
        value
        for value in dates
        if value.month == 6
    ]

    july_dates = [
        value
        for value in dates
        if value.month == 7
    ]

    assert min(june_dates) == date(2026, 6, 1)
    assert max(june_dates) == date(2026, 6, 14)
    assert min(july_dates) == date(2026, 7, 1)
    assert max(july_dates) == date(2026, 7, 14)


def test_seed_uses_decimal_money():
    assert all(
        isinstance(row["amount"], Decimal)
        for row in seed.TRANSACTIONS
    )


def test_expenses_are_negative_and_income_positive():
    for row in seed.TRANSACTIONS:
        if row["transaction_type"] == "expense":
            assert row["amount"] < Decimal("0")
        elif row["transaction_type"] == "income":
            assert row["amount"] > Decimal("0")


def test_seed_contains_multiple_financial_categories():
    categories = {
        row["category"]
        for row in seed.TRANSACTIONS
        if row["category"] is not None
    }

    assert {
        "food",
        "groceries",
        "transport",
        "utilities",
        "health",
        "shopping",
        "housing",
        "leisure",
    }.issubset(categories)


def test_seed_contains_income_expense_and_transfer():
    types = {
        row["transaction_type"]
        for row in seed.TRANSACTIONS
    }

    assert types == {
        "income",
        "expense",
        "transfer",
    }


def test_fingerprints_are_unique():
    fingerprints = [
        seed._fingerprint(index, row)
        for index, row in enumerate(
            seed.TRANSACTIONS,
            start=1,
        )
    ]

    assert len(fingerprints) == len(
        set(fingerprints)
    )
