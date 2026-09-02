from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.importer import import_statement
from app.ingestion.santander_pdf import (
    parse_statement,
)
from app.models.transaction import Transaction
from app.services.financial_pipeline import (
    prepare_santander_statement,
)


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

    statement = prepare_santander_statement(
        db_session,
        parsed,
        source_account="synthetic-account",
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

    expected_transaction_types = [
        transaction.transaction_type
        for transaction in statement.transactions
    ]

    stored_transaction_types = [
        transaction.transaction_type
        for transaction in stored_transactions
    ]

    assert (
        stored_transaction_types
        == expected_transaction_types
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
