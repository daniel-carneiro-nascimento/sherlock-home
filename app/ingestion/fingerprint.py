import hashlib

from app.ingestion.normalization import (
    CanonicalTransaction,
)


def build_transaction_fingerprint(
    *,
    transaction: CanonicalTransaction,
    occurrence: int,
) -> str:
    canonical = "|".join(
        [
            transaction.transaction_date.isoformat(),
            format(transaction.amount, "f"),
            transaction.original_description,
            transaction.document or "",
            transaction.statement_month.isoformat(),
            transaction.source,
            transaction.source_type,
            transaction.source_account or "",
            str(occurrence),
        ]
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
