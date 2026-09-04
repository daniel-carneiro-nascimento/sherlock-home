from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


@dataclass(frozen=True)
class DuplicateChargeCandidate:
    transaction_date: date
    merchant: str
    description: str
    category: str | None
    amount: Decimal
    occurrences: int
    transaction_ids: tuple[int, ...]


@dataclass(frozen=True)
class DuplicateChargesResult:
    start_date: date
    end_date: date
    candidates: list[DuplicateChargeCandidate]


def _validate_date_range(
    *,
    start_date: date,
    end_date: date,
) -> None:
    if end_date <= start_date:
        raise ValueError(
            "end_date must be after start_date"
        )


def _normalize_text(
    value: str,
) -> str:
    return " ".join(
        value.upper().split()
    )


def detect_duplicate_charges(
    session: Session,
    *,
    start_date: date,
    end_date: date,
) -> DuplicateChargesResult:
    """
    Detect exact duplicate-looking expense charges.

    A candidate requires two or more distinct persisted transactions with:
    - the same transaction date;
    - the same normalized merchant;
    - the same signed amount;
    - the same normalized original description.

    Fingerprint is intentionally NOT part of the comparison. Fingerprints
    identify persisted/imported transactions for idempotency; duplicate-charge
    analysis asks whether distinct persisted transactions look financially
    equivalent.
    """
    _validate_date_range(
        start_date=start_date,
        end_date=end_date,
    )

    transactions = session.scalars(
        select(Transaction)
        .where(
            Transaction.transaction_type
            == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .order_by(
            Transaction.date,
            Transaction.id,
        )
    ).all()

    groups: dict[
        tuple[date, str, Decimal, str],
        list[Transaction],
    ] = defaultdict(list)

    for transaction in transactions:
        if not transaction.merchant:
            continue

        merchant_key = _normalize_text(
            transaction.merchant
        )
        description_key = _normalize_text(
            transaction.original_description
        )

        if (
            not merchant_key
            or not description_key
        ):
            continue

        key = (
            transaction.date,
            merchant_key,
            Decimal(transaction.amount),
            description_key,
        )

        groups[key].append(
            transaction
        )

    candidates: list[
        DuplicateChargeCandidate
    ] = []

    for (
        transaction_date,
        merchant_key,
        signed_amount,
        description_key,
    ), group in groups.items():
        if len(group) < 2:
            continue

        ordered = sorted(
            group,
            key=lambda transaction: (
                transaction.id
            ),
        )

        categories = {
            transaction.category
            for transaction in ordered
        }

        category = (
            next(iter(categories))
            if len(categories) == 1
            else None
        )

        candidates.append(
            DuplicateChargeCandidate(
                transaction_date=(
                    transaction_date
                ),
                merchant=merchant_key,
                description=description_key,
                category=category,
                amount=abs(
                    signed_amount
                ),
                occurrences=len(
                    ordered
                ),
                transaction_ids=tuple(
                    transaction.id
                    for transaction
                    in ordered
                ),
            )
        )

    candidates.sort(
        key=lambda candidate: (
            candidate.transaction_date,
            candidate.merchant,
            candidate.amount,
            candidate.transaction_ids,
        )
    )

    return DuplicateChargesResult(
        start_date=start_date,
        end_date=end_date,
        candidates=candidates,
    )
