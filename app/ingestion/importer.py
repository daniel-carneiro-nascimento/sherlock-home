from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.fingerprint import (
    build_transaction_fingerprint,
)
from app.ingestion.normalization import (
    CanonicalStatement,
)
from app.models.transaction import Transaction


def import_statement(
    session: Session,
    statement: CanonicalStatement,
) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    occurrence_counter: dict[
        tuple,
        int,
    ] = defaultdict(int)

    for tx in statement.transactions:
        signature = (
            tx.transaction_date,
            tx.amount,
            tx.original_description,
            tx.document or "",
            tx.statement_month,
            tx.source,
            tx.source_type,
            tx.source_account or "",
        )

        occurrence_counter[signature] += 1

        occurrence = occurrence_counter[
            signature
        ]

        fingerprint = (
            build_transaction_fingerprint(
                transaction=tx,
                occurrence=occurrence,
            )
        )

        existing = session.scalar(
            select(Transaction.id).where(
                Transaction.fingerprint
                == fingerprint
            )
        )

        if existing is not None:
            skipped += 1
            continue

        transaction = Transaction(
            date=tx.transaction_date,
            amount=tx.amount,
            original_description=(
                tx.original_description
            ),
            statement_month=(
                tx.statement_month
            ),
            fingerprint=fingerprint,
        )

        session.add(transaction)
        inserted += 1

    session.commit()

    return inserted, skipped 
