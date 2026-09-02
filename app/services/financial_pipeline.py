from sqlalchemy.orm import Session

from app.ingestion.expense_categorization import (
    categorize_statement_expenses,
)
from app.ingestion.merchant_normalization import (
    normalize_statement_merchants,
)
from app.ingestion.normalization import (
    CanonicalStatement,
    normalize_santander_statement,
)
from app.ingestion.santander_pdf import ParsedStatement
from app.ingestion.transaction_typing import (
    classify_statement_transactions,
)
from app.services.category_rules import (
    load_category_rules_from_db,
)
from app.services.merchant_aliases import (
    load_merchant_aliases_from_db,
)


def enrich_canonical_statement(
    session: Session,
    statement: CanonicalStatement,
) -> CanonicalStatement:
    """
    Apply runtime financial enrichment using deterministic
    configuration persisted in PostgreSQL.
    """
    merchant_aliases = load_merchant_aliases_from_db(
        session
    )

    statement = normalize_statement_merchants(
        statement,
        alias_rules=merchant_aliases,
    )

    statement = classify_statement_transactions(
        statement
    )

    category_rules = load_category_rules_from_db(
        session,
        include_defaults=True,
    )

    statement = categorize_statement_expenses(
        statement,
        rules=category_rules,
    )

    return statement


def prepare_santander_statement(
    session: Session,
    statement: ParsedStatement,
    *,
    source_account: str | None = None,
) -> CanonicalStatement:
    """
    Convert Santander parser output into the canonical model
    and apply the complete deterministic runtime enrichment
    pipeline.
    """
    canonical = normalize_santander_statement(
        statement,
        source_account=source_account,
    )

    return enrich_canonical_statement(
        session,
        canonical,
    )
