from datetime import date
from decimal import Decimal
import re

import pytest

from app.ingestion.merchant_normalization import (
    extract_merchant_from_description,
    normalize_merchant_name,
    normalize_statement_merchants,
    normalize_transaction_merchant,
)
from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.rules.merchant_aliases import (
    MerchantAliasRule,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "merchant   test",
            "MERCHANT TEST",
        ),
        (
            "  company test  ",
            "COMPANY TEST",
        ),
        (
            "Foo Bar Ltda",
            "FOO BAR LTDA",
        ),
    ],
)
def test_normalize_merchant_name(
    raw: str,
    expected: str,
):
    assert normalize_merchant_name(raw) == expected


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        (
            "COMPRA CARTAO DEB MC 09/06 MERCHANT TEST",
            "MERCHANT TEST",
        ),
        (
            "PAGAMENTO DE BOLETO COMPANY TEST",
            "COMPANY TEST",
        ),
        (
            "PIX ENVIADO Pix Marketplace MERCHANT TEST",
            "MERCHANT TEST",
        ),
        (
            "PIX RECEBIDO COMPANY TEST",
            "COMPANY TEST",
        ),
    ],
)
def test_extract_known_merchant_patterns(
    description: str,
    expected: str,
):
    assert (
        extract_merchant_from_description(description)
        == expected
    )


@pytest.mark.parametrize(
    "description",
    [
        "",
        "TRANSFERENCIA INTERNA",
        "SALDO DO DIA",
        "OPERACAO DESCONHECIDA",
    ],
)
def test_unknown_patterns_do_not_invent_merchant(
    description: str,
):
    assert (
        extract_merchant_from_description(description)
        is None
    )


def test_transaction_enrichment_preserves_financial_data():
    transaction = CanonicalTransaction(
        transaction_date=date(2026, 6, 9),
        amount=Decimal("-23.50"),
        original_description=(
            "PAGAMENTO DE BOLETO COMPANY TEST"
        ),
        document="000001",
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        merchant=None,
        category=None,
        transaction_type="expense",
    )

    enriched = normalize_transaction_merchant(
        transaction
    )

    assert enriched.merchant == "COMPANY TEST"

    assert (
        enriched.transaction_date
        == transaction.transaction_date
    )
    assert enriched.amount == transaction.amount
    assert (
        enriched.original_description
        == transaction.original_description
    )
    assert enriched.document == transaction.document
    assert (
        enriched.statement_month
        == transaction.statement_month
    )
    assert enriched.source == transaction.source
    assert (
        enriched.source_type
        == transaction.source_type
    )
    assert (
        enriched.source_account
        == transaction.source_account
    )
    assert enriched.category == transaction.category
    assert (
        enriched.transaction_type
        == transaction.transaction_type
    )


def test_transaction_merchant_alias_is_applied():
    rules = (
        MerchantAliasRule(
            canonical_name="SYNTHETIC MARKET",
            pattern=re.compile(
                r"^SYNTHETIC MARKET(?:\s+\*\d+)?$",
                re.IGNORECASE,
            ),
            priority=10,
        ),
    )

    transaction = CanonicalTransaction(
        transaction_date=date(2026, 6, 9),
        amount=Decimal("-50.00"),
        original_description=(
            "PAGAMENTO DE BOLETO SYNTHETIC MARKET *1234"
        ),
        document="000001",
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        merchant=None,
        category=None,
        transaction_type="expense",
    )

    enriched = normalize_transaction_merchant(
        transaction,
        alias_rules=rules,
    )

    assert enriched.merchant == "SYNTHETIC MARKET"


def test_unmatched_alias_preserves_extracted_merchant():
    rules = (
        MerchantAliasRule(
            canonical_name="OTHER COMPANY",
            pattern=re.compile(
                r"^OTHER COMPANY ALT$",
                re.IGNORECASE,
            ),
            priority=10,
        ),
    )

    transaction = CanonicalTransaction(
        transaction_date=date(2026, 6, 9),
        amount=Decimal("-50.00"),
        original_description=(
            "PAGAMENTO DE BOLETO SYNTHETIC COMPANY"
        ),
        document="000001",
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        merchant=None,
        category=None,
        transaction_type="expense",
    )

    enriched = normalize_transaction_merchant(
        transaction,
        alias_rules=rules,
    )

    assert enriched.merchant == "SYNTHETIC COMPANY"


def test_statement_merchant_normalization():
    transactions = [
        CanonicalTransaction(
            transaction_date=date(2026, 6, 9),
            amount=Decimal("-10.00"),
            original_description=(
                "PAGAMENTO DE BOLETO COMPANY TEST"
            ),
            document=None,
            statement_month=date(2026, 6, 1),
            source="santander",
            source_type="bank_statement",
            source_account="synthetic-account",
            merchant=None,
            category=None,
            transaction_type="expense",
        ),
        CanonicalTransaction(
            transaction_date=date(2026, 6, 10),
            amount=Decimal("-20.00"),
            original_description=(
                "OPERACAO DESCONHECIDA"
            ),
            document=None,
            statement_month=date(2026, 6, 1),
            source="santander",
            source_type="bank_statement",
            source_account="synthetic-account",
            merchant=None,
            category=None,
            transaction_type="expense",
        ),
    ]

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=transactions,
    )

    normalized = normalize_statement_merchants(
        statement
    )

    assert len(normalized.transactions) == 2

    assert (
        normalized.transactions[0].merchant
        == "COMPANY TEST"
    )
    assert (
        normalized.transactions[1].merchant
        is None
    )

    assert (
        normalized.statement_month
        == statement.statement_month
    )
    assert normalized.source == statement.source
    assert (
        normalized.source_type
        == statement.source_type
    )
    assert (
        normalized.source_account
        == statement.source_account
    )


def test_statement_alias_rules_are_applied_to_all_transactions():
    rules = (
        MerchantAliasRule(
            canonical_name="SYNTHETIC MARKET",
            pattern=re.compile(
                r"^SYNTHETIC MARKET(?:\s+\*\d+)?$",
                re.IGNORECASE,
            ),
            priority=10,
        ),
    )

    transactions = [
        CanonicalTransaction(
            transaction_date=date(2026, 6, 9),
            amount=Decimal("-10.00"),
            original_description=(
                "PAGAMENTO DE BOLETO SYNTHETIC MARKET *1111"
            ),
            document=None,
            statement_month=date(2026, 6, 1),
            source="santander",
            source_type="bank_statement",
            source_account="synthetic-account",
            merchant=None,
            category=None,
            transaction_type="expense",
        ),
        CanonicalTransaction(
            transaction_date=date(2026, 6, 10),
            amount=Decimal("-20.00"),
            original_description=(
                "PIX RECEBIDO SYNTHETIC MARKET *2222"
            ),
            document=None,
            statement_month=date(2026, 6, 1),
            source="santander",
            source_type="bank_statement",
            source_account="synthetic-account",
            merchant=None,
            category=None,
            transaction_type="income",
        ),
    ]

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=transactions,
    )

    normalized = normalize_statement_merchants(
        statement,
        alias_rules=rules,
    )

    assert [
        transaction.merchant
        for transaction in normalized.transactions
    ] == [
        "SYNTHETIC MARKET",
        "SYNTHETIC MARKET",
    ]

    assert [
        transaction.transaction_type
        for transaction in normalized.transactions
    ] == [
        "expense",
        "income",
    ]
