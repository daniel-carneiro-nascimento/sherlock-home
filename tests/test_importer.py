from pathlib import Path

from sqlalchemy import delete

from app.db.database import SessionLocal
from app.ingestion.importer import import_statement
from app.ingestion.santander_pdf import parse_statement
from app.models.transaction import Transaction


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "santander_statement.txt"
)


def test_import_is_idempotent():
    text = FIXTURE.read_text(encoding="utf-8")
    statement = parse_statement(text)

    with SessionLocal() as session:
        session.execute(delete(Transaction))
        session.commit()

        inserted, skipped = import_statement(
            session,
            statement,
        )

        assert inserted == 4
        assert skipped == 0

        inserted, skipped = import_statement(
            session,
            statement,
        )

        assert inserted == 0
        assert skipped == 4

        session.execute(delete(Transaction))
        session.commit()
