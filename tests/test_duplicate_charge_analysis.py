from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import (
    Transaction,
)
from app.services.duplicate_charge_analysis import (
    DuplicateChargesResult,
    detect_duplicate_charges,
)


def make_transaction(
    *,
    transaction_date: date,
    amount: Decimal,
    fingerprint: str,
    merchant: str | None,
    description: str,
    transaction_type: str = "expense",
    category: str | None = "auto",
) -> Transaction:
    return Transaction(
        date=transaction_date,
        amount=amount,
        transaction_type=(
            transaction_type
        ),
        category=category,
        merchant=merchant,
        statement_month=date(
            transaction_date.year,
            transaction_date.month,
            1,
        ),
        original_description=(
            description
        ),
        fingerprint=fingerprint,
    )


def test_detects_exact_duplicate_with_different_fingerprints(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=(
                    date(2026, 7, 15)
                ),
                amount=Decimal(
                    "-349.90"
                ),
                fingerprint=(
                    "duplicate-a"
                ),
                merchant=(
                    "OFICINA CENTRAL"
                ),
                description=(
                    "PAGAMENTO OFICINA CENTRAL"
                ),
            ),
            make_transaction(
                transaction_date=(
                    date(2026, 7, 15)
                ),
                amount=Decimal(
                    "-349.90"
                ),
                fingerprint=(
                    "duplicate-b"
                ),
                merchant=(
                    "OFICINA CENTRAL"
                ),
                description=(
                    "PAGAMENTO OFICINA CENTRAL"
                ),
            ),
        ]
    )
    db_session.commit()

    result = detect_duplicate_charges(
        db_session,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
    )

    assert isinstance(
        result,
        DuplicateChargesResult,
    )

    assert len(
        result.candidates
    ) == 1

    candidate = (
        result.candidates[0]
    )

    assert candidate.merchant == (
        "OFICINA CENTRAL"
    )
    assert candidate.amount == Decimal(
        "349.90"
    )
    assert candidate.occurrences == 2
    assert len(
        candidate.transaction_ids
    ) == 2


def test_fingerprint_is_not_duplicate_matching_criterion(
    db_session: Session,
):
    first = make_transaction(
        transaction_date=date(
            2026,
            7,
            15,
        ),
        amount=Decimal("-20.00"),
        fingerprint="financial-a",
        merchant="MERCHANT",
        description="PAYMENT",
    )
    second = make_transaction(
        transaction_date=date(
            2026,
            7,
            15,
        ),
        amount=Decimal("-20.00"),
        fingerprint="financial-b",
        merchant="MERCHANT",
        description="PAYMENT",
    )

    db_session.add_all(
        [
            first,
            second,
        ]
    )
    db_session.commit()

    result = detect_duplicate_charges(
        db_session,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
    )

    assert len(
        result.candidates
    ) == 1


def test_different_amount_is_not_exact_duplicate(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    15,
                ),
                amount=Decimal(
                    "-100.00"
                ),
                fingerprint="amount-a",
                merchant="MERCHANT",
                description="PAYMENT",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    15,
                ),
                amount=Decimal(
                    "-101.00"
                ),
                fingerprint="amount-b",
                merchant="MERCHANT",
                description="PAYMENT",
            ),
        ]
    )
    db_session.commit()

    result = detect_duplicate_charges(
        db_session,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
    )

    assert result.candidates == []


def test_different_date_is_not_exact_duplicate(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    15,
                ),
                amount=Decimal(
                    "-100.00"
                ),
                fingerprint="date-a",
                merchant="MERCHANT",
                description="PAYMENT",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    16,
                ),
                amount=Decimal(
                    "-100.00"
                ),
                fingerprint="date-b",
                merchant="MERCHANT",
                description="PAYMENT",
            ),
        ]
    )
    db_session.commit()

    result = detect_duplicate_charges(
        db_session,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
    )

    assert result.candidates == []


def test_income_is_not_duplicate_charge(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    15,
                ),
                amount=Decimal(
                    "100.00"
                ),
                fingerprint="income-a",
                merchant="EMPLOYER",
                description="PAYMENT",
                transaction_type="income",
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    15,
                ),
                amount=Decimal(
                    "100.00"
                ),
                fingerprint="income-b",
                merchant="EMPLOYER",
                description="PAYMENT",
                transaction_type="income",
            ),
        ]
    )
    db_session.commit()

    result = detect_duplicate_charges(
        db_session,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
    )

    assert result.candidates == []


def test_description_and_merchant_are_normalized(
    db_session: Session,
):
    db_session.add_all(
        [
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    15,
                ),
                amount=Decimal(
                    "-50.00"
                ),
                fingerprint="normalize-a",
                merchant="Loja Central",
                description=(
                    "Pagamento   Loja Central"
                ),
            ),
            make_transaction(
                transaction_date=date(
                    2026,
                    7,
                    15,
                ),
                amount=Decimal(
                    "-50.00"
                ),
                fingerprint="normalize-b",
                merchant=" LOJA CENTRAL ",
                description=(
                    " pagamento loja central "
                ),
            ),
        ]
    )
    db_session.commit()

    result = detect_duplicate_charges(
        db_session,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
    )

    assert len(
        result.candidates
    ) == 1
