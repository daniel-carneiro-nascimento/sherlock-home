from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.fingerprint import build_transaction_fingerprint
from app.ingestion.santander_pdf import ParsedStatement
from app.models.transaction import Transaction


def import_statement(
    session: Session,
    statement: ParsedStatement,
) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    occurrence_counter: dict[tuple, int] = defaultdict(int)

    for parsed_tx in statement.transactions:
        signature = (
            parsed_tx.date,
            parsed_tx.amount,
            " ".join(parsed_tx.description.split()),
            parsed_tx.document or "",
            statement.statement_month,
        )

        occurrence_counter[signature] += 1
        occurrence = occurrence_counter[signature]

        fingerprint = build_transaction_fingerprint(
            tx_date=parsed_tx.date,
            amount=parsed_tx.amount,
            description=parsed_tx.description,
            document=parsed_tx.document,
            statement_month=statement.statement_month,
            occurrence=occurrence,
        )

        existing = session.scalar(
            select(Transaction.id).where(
                Transaction.fingerprint == fingerprint
            )
        )

        if existing is not None:
            skipped += 1
            continue

        transaction = Transaction(
            date=parsed_tx.date,
            amount=parsed_tx.amount,
            original_description=parsed_tx.description,
            statement_month=statement.statement_month,
            fingerprint=fingerprint,
        )

        session.add(transaction)
        inserted += 1

    session.commit()

    return inserted, skipped
