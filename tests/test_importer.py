from pathlib import Path

from sqlalchemy import delete, select

from app.db.database import SessionLocal
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


def test_import_is_idempotent():
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

    expected_count = len(
        statement.transactions
    )

    assert expected_count > 0

    with SessionLocal() as session:
        session.execute(
            delete(Transaction)
        )
        session.commit()

        inserted, skipped = import_statement(
            session,
            statement,
        )

        assert inserted == expected_count
        assert skipped == 0

        stored_transactions = session.scalars(
            select(Transaction)
        ).all()

        assert (
            len(stored_transactions)
            == expected_count
        )

        expected_merchants = [
            tx.merchant
            for tx in statement.transactions
        ]

        stored_merchants = [
            tx.merchant
            for tx in stored_transactions
        ]

        assert (
            stored_merchants
            == expected_merchants
        )

        inserted, skipped = import_statement(
            session,
            statement,
        )

        assert inserted == 0
        assert skipped == expected_count

        session.execute(
            delete(Transaction)
        )
        session.commit() 
