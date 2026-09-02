from datetime import date
from decimal import Decimal
import re

import pytest

from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.ingestion.transaction_typing import (
    classify_statement_transactions,
    classify_transaction,
    classify_transaction_type,
)
from app.rules.transaction_types import (
    TransactionType,
    TransactionTypeRule,
    TransactionTypeRuleField,
)


def make_transaction(
    *,
    amount: Decimal,
    description: str = "SYNTHETIC TRANSACTION",
) -> CanonicalTransaction:
    return CanonicalTransaction(
        transaction_date=date(2026, 6, 9),
        amount=amount,
        original_description=description,
        document="000001",
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        merchant=None,
        category=None,
        transaction_type=None,
    )


@pytest.mark.parametrize(
    ("description", "amount", "expected"),
    [
        (
            "CREDITO SALARIO",
            Decimal("1000.00"),
            "income",
        ),
        (
            "CREDITO SALÁRIO",
            Decimal("1000.00"),
            "income",
        ),
        (
            "TRANSFERENCIA INTERNA",
            Decimal("-500.00"),
            "transfer",
        ),
    ],
)
def test_explicit_transaction_type_rules(
    description: str,
    amount: Decimal,
    expected: str,
):
    transaction = make_transaction(
        amount=amount,
        description=description,
    )

    assert (
        classify_transaction_type(transaction)
        == expected
    )


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (
            Decimal("-1.00"),
            "expense",
        ),
        (
            Decimal("-999.99"),
            "expense",
        ),
        (
            Decimal("1.00"),
            "income",
        ),
        (
            Decimal("5000.00"),
            "income",
        ),
    ],
)
def test_amount_fallback_classification(
    amount: Decimal,
    expected: str,
):
    transaction = make_transaction(
        amount=amount,
    )

    assert (
        classify_transaction_type(transaction)
        == expected
    )


def test_explicit_rule_overrides_amount_sign():
    transaction = make_transaction(
        amount=Decimal("-1000.00"),
        description="TRANSFERENCIA INTERNA",
    )

    assert (
        classify_transaction_type(transaction)
        == "transfer"
    )


def test_classification_preserves_transaction_data():
    transaction = make_transaction(
        amount=Decimal("-123.45"),
    )

    classified = classify_transaction(
        transaction
    )

    assert classified.transaction_type == "expense"

    assert classified.amount == transaction.amount
    assert (
        classified.original_description
        == transaction.original_description
    )
    assert classified.document == transaction.document
    assert classified.source == transaction.source
    assert (
        classified.source_account
        == transaction.source_account
    )


def test_statement_transaction_typing():
    transactions = [
        make_transaction(
            amount=Decimal("-10.00"),
        ),
        make_transaction(
            amount=Decimal("1000.00"),
            description="CREDITO SALARIO",
        ),
        make_transaction(
            amount=Decimal("-100.00"),
            description="TRANSFERENCIA INTERNA",
        ),
    ]

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=transactions,
    )

    classified = classify_statement_transactions(
        statement
    )

    assert [
        transaction.transaction_type
        for transaction in classified.transactions
    ] == [
        "expense",
        "income",
        "transfer",
    ]


def test_custom_transaction_type_rule():
    rules = (
        TransactionTypeRule(
            transaction_type=TransactionType.TRANSFER,
            pattern=re.compile(
                r"CUSTOM TRANSFER",
                re.IGNORECASE,
            ),
            field=TransactionTypeRuleField.DESCRIPTION,
            priority=10,
        ),
    )

    transaction = make_transaction(
        amount=Decimal("-50.00"),
        description="CUSTOM TRANSFER",
    )

    assert (
        classify_transaction_type(
            transaction,
            rules=rules,
        )
        == "transfer"
    )
