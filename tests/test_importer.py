from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.expense_categorization import (
    categorize_statement_expenses,
)
from app.ingestion.importer import import_statement
from app.ingestion.merchant_normalization import (
    normalize_statement_merchants,
)
from app.ingestion.normalization import (
    normalize_santander_statement,
)
from app.ingestion.santander_pdf import (
    parse_statement,
)
from app.models.transaction import Transaction


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "santander_statement.txt"
)


def test_import_is_idempotent(
    db_session: Session,
):
    text = FIXTURE.read_text(
        encoding="utf-8"
    )

    parsed = parse_statement(text)

    statement = normalize_santander_statement(
        parsed,
        source_account="synthetic-account",
    )

    statement = normalize_statement_merchants(
        statement
    )

    statement = categorize_statement_expenses(
        statement
    )

    expected_count = len(
        statement.transactions
    )

    assert expected_count > 0

    inserted, skipped = import_statement(
        db_session,
        statement,
    )

    assert inserted == expected_count
    assert skipped == 0

    stored_transactions = db_session.scalars(
        select(Transaction).order_by(
            Transaction.id
        )
    ).all()

    assert (
        len(stored_transactions)
        == expected_count
    )

    expected_merchants = [
        transaction.merchant
        for transaction in statement.transactions
    ]

    stored_merchants = [
        transaction.merchant
        for transaction in stored_transactions
    ]

    assert (
        stored_merchants
        == expected_merchants
    )

    expected_categories = [
        transaction.category
        for transaction in statement.transactions
    ]

    stored_categories = [
        transaction.category
        for transaction in stored_transactions
    ]

    assert (
        stored_categories
        == expected_categories
    )

    inserted, skipped = import_statement(
        db_session,
        statement,
    )

    assert inserted == 0
    assert skipped == expected_count

    stored_transactions = db_session.scalars(
        select(Transaction)
    ).all()

    assert (
        len(stored_transactions)
        == expected_count
    ) 
