from datetime import date
from decimal import Decimal

import pytest

from app.ingestion.normalization import (
    normalize_description,
    normalize_santander_transaction,
)
from app.ingestion.santander_pdf import (
    ParsedTransaction,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "PIX   ENVIADO   TEST",
            "PIX ENVIADO TEST",
        ),
        (
            "  COMPRA    TEST  ",
            "COMPRA TEST",
        ),
        (
            "PAGAMENTO TEST",
            "PAGAMENTO TEST",
        ),
    ],
)
def test_normalize_description(
    raw: str,
    expected: str,
):
    assert (
        normalize_description(raw)
        == expected
    )


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("-1.00"),
        Decimal("-999.99"),
        Decimal("100.00"),
        Decimal("123456.78"),
    ],
)
def test_normalization_preserves_amount(
    amount: Decimal,
):
    parsed = ParsedTransaction(
        date=date(2026, 6, 11),
        description="MERCHANT   TEST",
        document=None,
        amount=amount,
        balance=None,
    )

    normalized = normalize_santander_transaction(
        parsed,
        statement_month=date(2026, 6, 1),
        source_account="synthetic-account",
    )

    assert normalized.amount == amount


def test_normalization_sets_source_metadata():
    parsed = ParsedTransaction(
        date=date(2026, 6, 11),
        description="MERCHANT TEST",
        document="000001",
        amount=Decimal("-10.00"),
        balance=None,
    )

    normalized = normalize_santander_transaction(
        parsed,
        statement_month=date(2026, 6, 1),
        source_account="synthetic-account",
    )

    assert normalized.source == "santander"
    assert normalized.source_type == "bank_statement"
    assert normalized.source_account == "synthetic-account"


def test_normalization_preserves_document():
    parsed = ParsedTransaction(
        date=date(2026, 6, 11),
        description="MERCHANT TEST",
        document="000001",
        amount=Decimal("-10.00"),
        balance=None,
    )

    normalized = normalize_santander_transaction(
        parsed,
        statement_month=date(2026, 6, 1),
    )

    assert normalized.document == "000001"
