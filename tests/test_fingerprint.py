from datetime import date
from decimal import Decimal

from app.ingestion.fingerprint import (
    build_transaction_fingerprint,
)


def test_same_transaction_same_fingerprint():
    kwargs = {
        "tx_date": date(2026, 6, 11),
        "amount": Decimal("-149.29"),
        "description": "PIX ENVIADO MERCHANT TEST",
        "document": None,
        "statement_month": date(2026, 6, 1),
        "occurrence": 1,
    }

    assert (
        build_transaction_fingerprint(**kwargs)
        == build_transaction_fingerprint(**kwargs)
    )


def test_whitespace_does_not_change_fingerprint():
    common = {
        "tx_date": date(2026, 6, 11),
        "amount": Decimal("-149.29"),
        "document": None,
        "statement_month": date(2026, 6, 1),
        "occurrence": 1,
    }

    first = build_transaction_fingerprint(
        description="PIX   ENVIADO   TEST",
        **common,
    )

    second = build_transaction_fingerprint(
        description="PIX ENVIADO TEST",
        **common,
    )

    assert first == second


def test_occurrence_distinguishes_identical_transactions():
    common = {
        "tx_date": date(2026, 6, 11),
        "amount": Decimal("-50.00"),
        "description": "PIX ENVIADO TEST",
        "document": None,
        "statement_month": date(2026, 6, 1),
    }

    first = build_transaction_fingerprint(
        occurrence=1,
        **common,
    )

    second = build_transaction_fingerprint(
        occurrence=2,
        **common,
    )

    assert first != second
