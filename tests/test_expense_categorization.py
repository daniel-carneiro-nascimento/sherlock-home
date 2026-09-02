from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
import re

import pytest

from app.ingestion.expense_categorization import (
    categorize_statement_expenses,
    categorize_transaction,
    categorize_transaction_expense,
)
from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.rules.categories import (
    CategoryRule,
    CategoryRuleField,
    ExpenseCategory,
)


def make_transaction(
    *,
    merchant: str | None = None,
    description: str = "SYNTHETIC TRANSACTION",
    amount: Decimal = Decimal("-10.00"),
    transaction_type: str = "expense",
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
        merchant=merchant,
        category=None,
        transaction_type=transaction_type,
    )


@pytest.mark.parametrize(
    ("merchant", "expected"),
    [
        ("TEST RESTAURANT", "food"),
        ("SYNTHETIC SUPERMERCADO", "groceries"),
        ("TEST TAXI", "transport"),
        ("POSTO COMBUSTIVEL", "transport"),
        ("POSTO COMBUSTÍVEL", "transport"),
        ("TEST INTERNET", "utilities"),
        ("FORNECEDOR GAS DE COZINHA", "utilities"),
        ("FORNECEDOR GÁS DE COZINHA", "utilities"),
        ("TEST PHARMACY", "health"),
        ("SYNTHETIC STORE", "shopping"),
    ],
)
def test_known_merchants_are_categorized(
    merchant: str,
    expected: str,
):
    transaction = make_transaction(
        merchant=merchant,
    )

    assert (
        categorize_transaction(transaction)
        == expected
    )


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("PAGAMENTO ALUGUEL", "housing"),
        ("PAGAMENTO RENT", "housing"),
        ("PARCELA FINANCIAMENTO", "financing"),
        ("DESPESA LAZER", "leisure"),
        ("PAGAMENTO IMPOSTO", "taxes"),
        ("PAGAMENTO IMPOSTOS", "taxes"),
    ],
)
def test_expense_description_rules(
    description: str,
    expected: str,
):
    transaction = make_transaction(
        merchant=None,
        description=description,
    )

    assert (
        categorize_transaction(transaction)
        == expected
    )


@pytest.mark.parametrize(
    "merchant",
    [
        None,
        "",
        "UNKNOWN MERCHANT",
        "SYNTHETIC COMPANY",
    ],
)
def test_unknown_merchant_does_not_invent_category(
    merchant: str | None,
):
    transaction = make_transaction(
        merchant=merchant,
    )

    assert (
        categorize_transaction(transaction)
        is None
    )


@pytest.mark.parametrize(
    ("transaction_type", "merchant", "description"),
    [
        (
            "income",
            "TEST RESTAURANT",
            "CREDITO SALARIO",
        ),
        (
            "transfer",
            "SYNTHETIC SUPERMERCADO",
            "TRANSFERENCIA INTERNA",
        ),
    ],
)
def test_non_expense_transaction_is_not_categorized(
    transaction_type: str,
    merchant: str,
    description: str,
):
    transaction = make_transaction(
        merchant=merchant,
        description=description,
        transaction_type=transaction_type,
    )

    assert categorize_transaction(transaction) is None


def test_categorization_preserves_transaction_data():
    transaction = make_transaction(
        merchant="TEST RESTAURANT",
        amount=Decimal("-123.45"),
    )

    categorized = categorize_transaction_expense(
        transaction
    )

    assert categorized.category == "food"
    assert categorized.transaction_date == transaction.transaction_date
    assert categorized.amount == transaction.amount
    assert categorized.original_description == transaction.original_description
    assert categorized.document == transaction.document
    assert categorized.statement_month == transaction.statement_month
    assert categorized.source == transaction.source
    assert categorized.source_type == transaction.source_type
    assert categorized.source_account == transaction.source_account
    assert categorized.merchant == transaction.merchant
    assert categorized.transaction_type == transaction.transaction_type


def test_statement_categorization():
    transactions = [
        make_transaction(merchant="TEST RESTAURANT"),
        make_transaction(merchant="UNKNOWN COMPANY"),
        make_transaction(
            merchant=None,
            description="PAGAMENTO ALUGUEL",
        ),
        make_transaction(
            merchant=None,
            description="PARCELA FINANCIAMENTO",
        ),
        make_transaction(
            merchant=None,
            description="PAGAMENTO IMPOSTOS",
        ),
        make_transaction(
            merchant="TEST RESTAURANT",
            description="CREDITO SALARIO",
            amount=Decimal("1000.00"),
            transaction_type="income",
        ),
        make_transaction(
            merchant="SYNTHETIC SUPERMERCADO",
            description="TRANSFERENCIA INTERNA",
            transaction_type="transfer",
        ),
    ]

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=transactions,
    )

    categorized = categorize_statement_expenses(
        statement
    )

    assert [
        transaction.category
        for transaction in categorized.transactions
    ] == [
        "food",
        None,
        "housing",
        "financing",
        "taxes",
        None,
        None,
    ]


def test_custom_rules_can_be_injected():
    rules = (
        CategoryRule(
            category=ExpenseCategory.SHOPPING,
            pattern=re.compile(
                r"\bCUSTOM MERCHANT\b",
                re.IGNORECASE,
            ),
            field=CategoryRuleField.MERCHANT,
            priority=10,
        ),
    )

    transaction = make_transaction(
        merchant="CUSTOM MERCHANT",
    )

    assert (
        categorize_transaction(
            transaction,
            rules=rules,
        )
        == "shopping"
    )


def test_rule_priority_is_deterministic():
    rules = (
        CategoryRule(
            category=ExpenseCategory.SHOPPING,
            pattern=re.compile(
                r"TEST",
                re.IGNORECASE,
            ),
            field=CategoryRuleField.MERCHANT,
            priority=200,
        ),
        CategoryRule(
            category=ExpenseCategory.FOOD,
            pattern=re.compile(
                r"TEST",
                re.IGNORECASE,
            ),
            field=CategoryRuleField.MERCHANT,
            priority=10,
        ),
    )

    transaction = make_transaction(
        merchant="TEST MERCHANT",
    )

    assert (
        categorize_transaction(
            transaction,
            rules=rules,
        )
        == "food"
    )


def test_description_rule_has_priority_over_merchant_rule():
    transaction = make_transaction(
        merchant="TEST RESTAURANT",
        description="PAGAMENTO IMPOSTOS",
    )

    assert categorize_transaction(transaction) == "taxes"


def test_categorization_does_not_modify_transaction_type():
    transaction = make_transaction(
        merchant="TEST RESTAURANT",
        transaction_type="expense",
    )

    categorized = categorize_transaction_expense(
        transaction
    )

    assert categorized.category == "food"
    assert categorized.transaction_type == "expense"


def test_income_remains_uncategorized_after_enrichment():
    transaction = make_transaction(
        merchant="TEST RESTAURANT",
        amount=Decimal("1000.00"),
        transaction_type="income",
    )

    categorized = categorize_transaction_expense(
        transaction
    )

    assert categorized.category is None
    assert categorized.transaction_type == "income"


def test_transfer_remains_uncategorized_after_enrichment():
    transaction = make_transaction(
        merchant="TEST RESTAURANT",
        transaction_type="transfer",
    )

    categorized = categorize_transaction_expense(
        transaction
    )

    assert categorized.category is None
    assert categorized.transaction_type == "transfer"


def test_local_rule_file_can_override_default_category(
    tmp_path: Path,
):
    rules_file = tmp_path / "categories.yaml"
    rules_file.write_text(
        """
rules:
  - category: leisure
    field: merchant
    pattern: "\\\\bTEST RESTAURANT\\\\b"
    priority: 5
""",
        encoding="utf-8",
    )

    transaction = make_transaction(
        merchant="TEST RESTAURANT",
    )

    assert (
        categorize_transaction(
            transaction,
            local_rules_path=rules_file,
        )
        == "leisure"
    )


def test_local_rule_file_applies_to_statement(
    tmp_path: Path,
):
    rules_file = tmp_path / "categories.yaml"
    rules_file.write_text(
        """
rules:
  - category: leisure
    field: merchant
    pattern: "\\\\bSYNTHETIC CINEMA\\\\b"
    priority: 5
""",
        encoding="utf-8",
    )

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=[
            make_transaction(
                merchant="SYNTHETIC CINEMA"
            ),
            make_transaction(
                merchant="TEST RESTAURANT"
            ),
        ],
    )

    categorized = categorize_statement_expenses(
        statement,
        local_rules_path=rules_file,
    )

    assert [
        transaction.category
        for transaction in categorized.transactions
    ] == [
        "leisure",
        "food",
    ]


def test_rules_and_local_rules_path_are_mutually_exclusive(
    tmp_path: Path,
):
    rules_file = tmp_path / "categories.yaml"
    rules_file.write_text(
        "rules: []\n",
        encoding="utf-8",
    )

    rules = (
        CategoryRule(
            category=ExpenseCategory.FOOD,
            pattern=re.compile(r"TEST"),
            field=CategoryRuleField.MERCHANT,
            priority=10,
        ),
    )

    transaction = make_transaction(
        merchant="TEST"
    )

    with pytest.raises(
        ValueError,
        match="either explicit rules or local_rules_path",
    ):
        categorize_transaction(
            transaction,
            rules=rules,
            local_rules_path=rules_file,
        )
