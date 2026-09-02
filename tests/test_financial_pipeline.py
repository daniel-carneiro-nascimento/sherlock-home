from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.ingestion.santander_pdf import (
    ParsedStatement,
    ParsedTransaction,
)
from app.models.category_rule import (
    CategoryRuleModel,
)
from app.models.merchant_alias import (
    MerchantAliasModel,
)
from app.services.financial_pipeline import (
    enrich_canonical_statement,
    prepare_santander_statement,
)


def test_runtime_pipeline_uses_database_merchant_aliases(
    db_session: Session,
):
    db_session.add(
        MerchantAliasModel(
            canonical_name="SYNTHETIC MARKET",
            pattern=(
                r"^SYNTHETIC MARKET"
                r"(?:\s+\*\d+)?$"
            ),
            priority=10,
            enabled=True,
        )
    )
    db_session.commit()

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=[
            CanonicalTransaction(
                transaction_date=date(2026, 6, 9),
                amount=Decimal("-50.00"),
                original_description=(
                    "PAGAMENTO DE BOLETO "
                    "SYNTHETIC MARKET *1234"
                ),
                document="000001",
                statement_month=date(2026, 6, 1),
                source="santander",
                source_type="bank_statement",
                source_account="synthetic-account",
                merchant=None,
                category=None,
                transaction_type=None,
            )
        ],
    )

    enriched = enrich_canonical_statement(
        db_session,
        statement,
    )

    transaction = enriched.transactions[0]

    assert transaction.merchant == "SYNTHETIC MARKET"
    assert transaction.transaction_type == "expense"


def test_runtime_pipeline_uses_database_category_rules(
    db_session: Session,
):
    db_session.add(
        CategoryRuleModel(
            category="leisure",
            field="merchant",
            pattern=r"\bSYNTHETIC CINEMA\b",
            priority=5,
            enabled=True,
        )
    )
    db_session.commit()

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=[
            CanonicalTransaction(
                transaction_date=date(2026, 6, 9),
                amount=Decimal("-40.00"),
                original_description=(
                    "PAGAMENTO DE BOLETO "
                    "SYNTHETIC CINEMA"
                ),
                document="000001",
                statement_month=date(2026, 6, 1),
                source="santander",
                source_type="bank_statement",
                source_account="synthetic-account",
                merchant=None,
                category=None,
                transaction_type=None,
            )
        ],
    )

    enriched = enrich_canonical_statement(
        db_session,
        statement,
    )

    transaction = enriched.transactions[0]

    assert transaction.merchant == "SYNTHETIC CINEMA"
    assert transaction.transaction_type == "expense"
    assert transaction.category == "leisure"


def test_database_category_rule_can_override_default(
    db_session: Session,
):
    db_session.add(
        CategoryRuleModel(
            category="leisure",
            field="merchant",
            pattern=r"\bTEST RESTAURANT\b",
            priority=5,
            enabled=True,
        )
    )
    db_session.commit()

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=[
            CanonicalTransaction(
                transaction_date=date(2026, 6, 9),
                amount=Decimal("-30.00"),
                original_description=(
                    "PAGAMENTO DE BOLETO "
                    "TEST RESTAURANT"
                ),
                document="000001",
                statement_month=date(2026, 6, 1),
                source="santander",
                source_type="bank_statement",
                source_account="synthetic-account",
                merchant=None,
                category=None,
                transaction_type=None,
            )
        ],
    )

    enriched = enrich_canonical_statement(
        db_session,
        statement,
    )

    transaction = enriched.transactions[0]

    assert transaction.merchant == "TEST RESTAURANT"
    assert transaction.transaction_type == "expense"
    assert transaction.category == "leisure"


def test_disabled_database_rules_are_ignored(
    db_session: Session,
):
    db_session.add(
        CategoryRuleModel(
            category="leisure",
            field="merchant",
            pattern=r"\bTEST RESTAURANT\b",
            priority=5,
            enabled=False,
        )
    )
    db_session.commit()

    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=[
            CanonicalTransaction(
                transaction_date=date(2026, 6, 9),
                amount=Decimal("-30.00"),
                original_description=(
                    "PAGAMENTO DE BOLETO "
                    "TEST RESTAURANT"
                ),
                document="000001",
                statement_month=date(2026, 6, 1),
                source="santander",
                source_type="bank_statement",
                source_account="synthetic-account",
                merchant=None,
                category=None,
                transaction_type=None,
            )
        ],
    )

    enriched = enrich_canonical_statement(
        db_session,
        statement,
    )

    assert enriched.transactions[0].category == "food"


def test_prepare_santander_statement_runs_complete_pipeline(
    db_session: Session,
):
    db_session.add(
        MerchantAliasModel(
            canonical_name="SYNTHETIC MARKET",
            pattern=(
                r"^SYNTHETIC MARKET"
                r"(?:\s+\*\d+)?$"
            ),
            priority=10,
            enabled=True,
        )
    )

    db_session.add(
        CategoryRuleModel(
            category="groceries",
            field="merchant",
            pattern=r"\bSYNTHETIC MARKET\b",
            priority=5,
            enabled=True,
        )
    )

    db_session.commit()

    parsed = ParsedStatement(
        statement_month=date(2026, 6, 1),
        transactions=[
            ParsedTransaction(
                date=date(2026, 6, 9),
                description=(
                    "PAGAMENTO DE BOLETO "
                    "SYNTHETIC MARKET *1234"
                ),
                document="000001",
                amount=Decimal("-75.00"),
                balance=None,
            )
        ],
    )

    prepared = prepare_santander_statement(
        db_session,
        parsed,
        source_account="synthetic-account",
    )

    transaction = prepared.transactions[0]

    assert transaction.merchant == "SYNTHETIC MARKET"
    assert transaction.transaction_type == "expense"
    assert transaction.category == "groceries"

    assert transaction.amount == Decimal("-75.00")
    assert transaction.source == "santander"
    assert transaction.source_type == "bank_statement"
    assert transaction.source_account == "synthetic-account"


def test_income_remains_uncategorized_in_runtime_pipeline(
    db_session: Session,
):
    statement = CanonicalStatement(
        statement_month=date(2026, 6, 1),
        source="santander",
        source_type="bank_statement",
        source_account="synthetic-account",
        transactions=[
            CanonicalTransaction(
                transaction_date=date(2026, 6, 9),
                amount=Decimal("1000.00"),
                original_description="CREDITO SALARIO",
                document="000001",
                statement_month=date(2026, 6, 1),
                source="santander",
                source_type="bank_statement",
                source_account="synthetic-account",
                merchant=None,
                category=None,
                transaction_type=None,
            )
        ],
    )

    enriched = enrich_canonical_statement(
        db_session,
        statement,
    )

    transaction = enriched.transactions[0]

    assert transaction.transaction_type == "income"
    assert transaction.category is None
