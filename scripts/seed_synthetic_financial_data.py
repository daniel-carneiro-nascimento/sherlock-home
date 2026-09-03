from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, inspect, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.transaction import Transaction


SYNTHETIC_PREFIX = "SHERLOCK_SYNTH_2026_"

# Two synthetic 14-day windows:
#   2026-06-01 .. 2026-06-14
#   2026-07-01 .. 2026-07-14
#
# Amount convention follows Sherlock Home's current financial-analysis layer:
# expenses are negative, income is positive, transfers are signed according to
# direction.
TRANSACTIONS: tuple[dict[str, Any], ...] = (
    # ----------------------------
    # June 2026
    # ----------------------------
    {
        "date": date(2026, 6, 1),
        "description": "SALARIO EMPRESA ACME",
        "amount": Decimal("7200.00"),
        "merchant": "ACME EMPLOYER",
        "transaction_type": "income",
        "category": None,
    },
    {
        "date": date(2026, 6, 1),
        "description": "ALUGUEL RESIDENCIAL",
        "amount": Decimal("-1850.00"),
        "merchant": "LANDLORD",
        "transaction_type": "expense",
        "category": "housing",
    },
    {
        "date": date(2026, 6, 2),
        "description": "SUPERMERCADO CENTRAL",
        "amount": Decimal("-286.40"),
        "merchant": "SUPERMERCADO CENTRAL",
        "transaction_type": "expense",
        "category": "groceries",
    },
    {
        "date": date(2026, 6, 2),
        "description": "CAFE DO BAIRRO",
        "amount": Decimal("-18.90"),
        "merchant": "CAFE DO BAIRRO",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 6, 3),
        "description": "UBER TRIP",
        "amount": Decimal("-42.70"),
        "merchant": "UBER",
        "transaction_type": "expense",
        "category": "transport",
    },
    {
        "date": date(2026, 6, 3),
        "description": "FARMACIA POPULAR",
        "amount": Decimal("-73.55"),
        "merchant": "FARMACIA POPULAR",
        "transaction_type": "expense",
        "category": "health",
    },
    {
        "date": date(2026, 6, 4),
        "description": "CONTA ENERGIA",
        "amount": Decimal("-214.80"),
        "merchant": "ENERGIA RIO",
        "transaction_type": "expense",
        "category": "utilities",
    },
    {
        "date": date(2026, 6, 4),
        "description": "STREAMING VIDEO",
        "amount": Decimal("-39.90"),
        "merchant": "STREAMFLIX",
        "transaction_type": "expense",
        "category": "leisure",
    },
    {
        "date": date(2026, 6, 5),
        "description": "CAFE DO BAIRRO",
        "amount": Decimal("-20.50"),
        "merchant": "CAFE DO BAIRRO",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 6, 5),
        "description": "RESTAURANTE SABOR",
        "amount": Decimal("-96.30"),
        "merchant": "RESTAURANTE SABOR",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 6, 6),
        "description": "LOJA ONLINE",
        "amount": Decimal("-329.99"),
        "merchant": "MARKETPLACE ONLINE",
        "transaction_type": "expense",
        "category": "shopping",
    },
    {
        "date": date(2026, 6, 7),
        "description": "POSTO COMBUSTIVEL",
        "amount": Decimal("-210.00"),
        "merchant": "POSTO CENTRAL",
        "transaction_type": "expense",
        "category": "transport",
    },
    {
        "date": date(2026, 6, 8),
        "description": "INTERNET FIBRA",
        "amount": Decimal("-119.90"),
        "merchant": "FIBRA NET",
        "transaction_type": "expense",
        "category": "utilities",
    },
    {
        "date": date(2026, 6, 8),
        "description": "CAFE DO BAIRRO",
        "amount": Decimal("-19.40"),
        "merchant": "CAFE DO BAIRRO",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 6, 9),
        "description": "SUPERMERCADO CENTRAL",
        "amount": Decimal("-198.65"),
        "merchant": "SUPERMERCADO CENTRAL",
        "transaction_type": "expense",
        "category": "groceries",
    },
    {
        "date": date(2026, 6, 10),
        "description": "TRANSFERENCIA RESERVA",
        "amount": Decimal("-500.00"),
        "merchant": None,
        "transaction_type": "transfer",
        "category": None,
    },
    {
        "date": date(2026, 6, 11),
        "description": "ACADEMIA MENSALIDADE",
        "amount": Decimal("-109.90"),
        "merchant": "ACADEMIA FORTE",
        "transaction_type": "expense",
        "category": "health",
    },
    {
        "date": date(2026, 6, 12),
        "description": "RESTAURANTE SABOR",
        "amount": Decimal("-118.00"),
        "merchant": "RESTAURANTE SABOR",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 6, 13),
        "description": "CINEMA",
        "amount": Decimal("-72.00"),
        "merchant": "CINE CENTER",
        "transaction_type": "expense",
        "category": "leisure",
    },
    {
        "date": date(2026, 6, 14),
        "description": "SUPERMERCADO CENTRAL",
        "amount": Decimal("-254.10"),
        "merchant": "SUPERMERCADO CENTRAL",
        "transaction_type": "expense",
        "category": "groceries",
    },

    # ----------------------------
    # July 2026
    # ----------------------------
    {
        "date": date(2026, 7, 1),
        "description": "SALARIO EMPRESA ACME",
        "amount": Decimal("7200.00"),
        "merchant": "ACME EMPLOYER",
        "transaction_type": "income",
        "category": None,
    },
    {
        "date": date(2026, 7, 1),
        "description": "ALUGUEL RESIDENCIAL",
        "amount": Decimal("-1850.00"),
        "merchant": "LANDLORD",
        "transaction_type": "expense",
        "category": "housing",
    },
    {
        "date": date(2026, 7, 2),
        "description": "SUPERMERCADO CENTRAL",
        "amount": Decimal("-312.70"),
        "merchant": "SUPERMERCADO CENTRAL",
        "transaction_type": "expense",
        "category": "groceries",
    },
    {
        "date": date(2026, 7, 2),
        "description": "CAFE DO BAIRRO",
        "amount": Decimal("-19.10"),
        "merchant": "CAFE DO BAIRRO",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 7, 3),
        "description": "UBER TRIP",
        "amount": Decimal("-55.20"),
        "merchant": "UBER",
        "transaction_type": "expense",
        "category": "transport",
    },
    {
        "date": date(2026, 7, 4),
        "description": "CONTA ENERGIA",
        "amount": Decimal("-238.45"),
        "merchant": "ENERGIA RIO",
        "transaction_type": "expense",
        "category": "utilities",
    },
    {
        "date": date(2026, 7, 4),
        "description": "STREAMING VIDEO",
        "amount": Decimal("-39.90"),
        "merchant": "STREAMFLIX",
        "transaction_type": "expense",
        "category": "leisure",
    },
    {
        "date": date(2026, 7, 5),
        "description": "CAFE DO BAIRRO",
        "amount": Decimal("-21.30"),
        "merchant": "CAFE DO BAIRRO",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 7, 5),
        "description": "RESTAURANTE SABOR",
        "amount": Decimal("-132.80"),
        "merchant": "RESTAURANTE SABOR",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 7, 6),
        "description": "LOJA ONLINE",
        "amount": Decimal("-649.90"),
        "merchant": "MARKETPLACE ONLINE",
        "transaction_type": "expense",
        "category": "shopping",
    },
    {
        "date": date(2026, 7, 7),
        "description": "POSTO COMBUSTIVEL",
        "amount": Decimal("-225.00"),
        "merchant": "POSTO CENTRAL",
        "transaction_type": "expense",
        "category": "transport",
    },
    {
        "date": date(2026, 7, 8),
        "description": "INTERNET FIBRA",
        "amount": Decimal("-119.90"),
        "merchant": "FIBRA NET",
        "transaction_type": "expense",
        "category": "utilities",
    },
    {
        "date": date(2026, 7, 8),
        "description": "CAFE DO BAIRRO",
        "amount": Decimal("-84.90"),
        "merchant": "CAFE DO BAIRRO",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 7, 9),
        "description": "SUPERMERCADO CENTRAL",
        "amount": Decimal("-221.15"),
        "merchant": "SUPERMERCADO CENTRAL",
        "transaction_type": "expense",
        "category": "groceries",
    },
    {
        "date": date(2026, 7, 10),
        "description": "TRANSFERENCIA RESERVA",
        "amount": Decimal("-500.00"),
        "merchant": None,
        "transaction_type": "transfer",
        "category": None,
    },
    {
        "date": date(2026, 7, 11),
        "description": "ACADEMIA MENSALIDADE",
        "amount": Decimal("-109.90"),
        "merchant": "ACADEMIA FORTE",
        "transaction_type": "expense",
        "category": "health",
    },
    {
        "date": date(2026, 7, 12),
        "description": "RESTAURANTE SABOR",
        "amount": Decimal("-155.60"),
        "merchant": "RESTAURANTE SABOR",
        "transaction_type": "expense",
        "category": "food",
    },
    {
        "date": date(2026, 7, 13),
        "description": "CINEMA",
        "amount": Decimal("-98.00"),
        "merchant": "CINE CENTER",
        "transaction_type": "expense",
        "category": "leisure",
    },
    {
        "date": date(2026, 7, 14),
        "description": "SUPERMERCADO CENTRAL",
        "amount": Decimal("-287.30"),
        "merchant": "SUPERMERCADO CENTRAL",
        "transaction_type": "expense",
        "category": "groceries",
    },
)


def _fingerprint(index: int, row: dict[str, Any]) -> str:
    payload = (
        f"{SYNTHETIC_PREFIX}{index}|"
        f"{row['date'].isoformat()}|"
        f"{row['amount']}|"
        f"{row['description']}"
    )
    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def _column_python_type(column) -> type | None:
    try:
        return column.type.python_type
    except (AttributeError, NotImplementedError):
        return None


def _statement_month_value(column, transaction_date: date):
    month_date = transaction_date.replace(day=1)
    python_type = _column_python_type(column)

    if python_type is date:
        return month_date

    if python_type is str:
        return month_date.strftime("%Y-%m")

    return month_date


def _synthetic_value_for_column(
    column,
    *,
    index: int,
    row: dict[str, Any],
):
    name = column.name
    transaction_date = row["date"]

    known = {
        "date": transaction_date,
        "original_description": row["description"],
        "description": row["description"],
        "amount": row["amount"],
        "merchant": row["merchant"],
        "transaction_type": row["transaction_type"],
        "category": row["category"],
        "card": None,
        "installment_current": None,
        "installment_total": None,
        "fingerprint": _fingerprint(index, row),
        "source": "synthetic",
        "source_type": "seed",
        "source_account": "synthetic-checking",
        "document": f"SYNTH-{index:03d}",
        "document_number": f"SYNTH-{index:03d}",
    }

    if name == "statement_month":
        return _statement_month_value(
            column,
            transaction_date,
        )

    return known.get(name)


def _build_transaction(
    *,
    index: int,
    row: dict[str, Any],
) -> Transaction:
    mapper = inspect(Transaction)
    kwargs: dict[str, Any] = {}
    unsupported_required: list[str] = []

    for column in mapper.columns:
        if column.primary_key:
            continue

        if (
            column.server_default is not None
            or column.default is not None
        ):
            continue

        value = _synthetic_value_for_column(
            column,
            index=index,
            row=row,
        )

        if value is not None:
            kwargs[column.name] = value
            continue

        if column.nullable:
            continue

        # Known fields that are intentionally nullable in the synthetic
        # dataset should not reach this branch on the current schema.
        unsupported_required.append(
            column.name
        )

    if unsupported_required:
        raise RuntimeError(
            "Seeder does not know how to populate required "
            "Transaction column(s): "
            + ", ".join(
                sorted(unsupported_required)
            )
        )

    # Explicitly set optional known fields when they exist, including None.
    column_names = {
        column.name
        for column in mapper.columns
    }

    for optional_name in (
        "merchant",
        "category",
        "card",
        "installment_current",
        "installment_total",
    ):
        if optional_name in column_names:
            kwargs[optional_name] = (
                _synthetic_value_for_column(
                    mapper.columns[optional_name],
                    index=index,
                    row=row,
                )
            )

    return Transaction(**kwargs)


def seed(session: Session) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    for index, row in enumerate(
        TRANSACTIONS,
        start=1,
    ):
        fingerprint = _fingerprint(
            index,
            row,
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

        session.add(
            _build_transaction(
                index=index,
                row=row,
            )
        )
        inserted += 1

    session.commit()
    return inserted, skipped


def clear(session: Session) -> int:
    fingerprints = [
        _fingerprint(index, row)
        for index, row in enumerate(
            TRANSACTIONS,
            start=1,
        )
    ]

    result = session.execute(
        delete(Transaction).where(
            Transaction.fingerprint.in_(
                fingerprints
            )
        )
    )
    session.commit()
    return int(
        result.rowcount or 0
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Insert deterministic synthetic June/July 2026 "
            "financial transactions into the normal Sherlock "
            "Home database without using the PDF ingestion path."
        )
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help=(
            "Delete only transactions created by this seeder."
        ),
    )

    args = parser.parse_args()

    try:
        with SessionLocal() as session:
            if args.clear:
                deleted = clear(session)
                print(
                    "Synthetic transactions deleted: "
                    f"{deleted}"
                )
                return 0

            inserted, skipped = seed(
                session
            )
    except Exception as exc:
        print(
            "Synthetic seed failed.",
            file=sys.stderr,
        )
        print(
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        f"Synthetic transactions inserted: {inserted}"
    )
    print(
        f"Synthetic transactions skipped:  {skipped}"
    )
    print(
        f"Synthetic transactions total:    {len(TRANSACTIONS)}"
    )
    print(
        "Periods: 2026-06-01..2026-06-14 and "
        "2026-07-01..2026-07-14"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
