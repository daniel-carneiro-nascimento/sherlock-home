import hashlib
from datetime import date
from decimal import Decimal


def build_transaction_fingerprint(
    *,
    tx_date: date,
    amount: Decimal,
    description: str,
    document: str | None,
    statement_month: date,
    occurrence: int,
) -> str:
    canonical = "|".join(
        [
            tx_date.isoformat(),
            format(amount, "f"),
            " ".join(description.split()),
            document.strip() if document else "",
            statement_month.isoformat(),
            str(occurrence),
        ]
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()
