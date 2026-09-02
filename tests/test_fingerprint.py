from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.ingestion.fingerprint import (
    build_transaction_fingerprint,
)
from app.ingestion.normalization import (
    CanonicalTransaction,
)


def make_transaction(
    *,
    amount: Decimal = Decimal("-10.00"),
    description: str = "MERCHANT TEST",
) -> CanonicalTransaction:
    return CanonicalTransaction(
        transaction_date=date(2026, 6, 11),
        amount=amount,
        original_description=description,
        document=None,
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
    )


def test_same_input_produces_same_fingerprint():
    tx = make_transaction()

    assert (
        build_transaction_fingerprint(
            transaction=tx,
            occurrence=1,
        )
        ==
        build_transaction_fingerprint(
            transaction=tx,
            occurrence=1,
        )
    )


def test_different_occurrence_changes_fingerprint():
    tx = make_transaction()

    assert (
        build_transaction_fingerprint(
            transaction=tx,
            occurrence=1,
        )
        !=
        build_transaction_fingerprint(
            transaction=tx,
            occurrence=2,
        )
    )


def test_different_amount_changes_fingerprint():
    tx1 = make_transaction(
        amount=Decimal("-10.00")
    )

    tx2 = make_transaction(
        amount=Decimal("-20.00")
    )

    assert (
        build_transaction_fingerprint(
            transaction=tx1,
            occurrence=1,
        )
        !=
        build_transaction_fingerprint(
            transaction=tx2,
            occurrence=1,
        )
    )


def test_different_source_account_changes_fingerprint():
    tx1 = make_transaction()

    tx2 = replace(
        tx1,
        source_account="another-account",
    )

    assert (
        build_transaction_fingerprint(
            transaction=tx1,
            occurrence=1,
        )
        !=
        build_transaction_fingerprint(
            transaction=tx2,
            occurrence=1,
        )
    ) 
