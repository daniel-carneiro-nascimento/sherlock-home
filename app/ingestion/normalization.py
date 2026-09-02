from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.ingestion.santander_pdf import (
    ParsedStatement,
    ParsedTransaction,
)


@dataclass(frozen=True)
class CanonicalTransaction:
    transaction_date: date
    amount: Decimal
    original_description: str
    document: str | None
    statement_month: date

    source: str
    source_type: str
    source_account: str | None = None


@dataclass(frozen=True)
class CanonicalStatement:
    statement_month: date
    source: str
    source_type: str
    source_account: str | None
    transactions: list[CanonicalTransaction]


def normalize_description(
    description: str,
) -> str:
    return " ".join(
        description.split()
    ).strip()


def normalize_santander_transaction(
    transaction: ParsedTransaction,
    *,
    statement_month: date,
    source_account: str | None = None,
) -> CanonicalTransaction:
    return CanonicalTransaction(
        transaction_date=transaction.date,
        amount=transaction.amount,
        original_description=normalize_description(
            transaction.description
        ),
        document=transaction.document,
        statement_month=statement_month,
        source="santander",
        source_type="bank_statement",
        source_account=source_account,
    )


def normalize_santander_statement(
    statement: ParsedStatement,
    *,
    source_account: str | None = None,
) -> CanonicalStatement:
    transactions = [
        normalize_santander_transaction(
            transaction,
            statement_month=statement.statement_month,
            source_account=source_account,
        )
        for transaction in statement.transactions
    ]

    return CanonicalStatement(
        statement_month=statement.statement_month,
        source="santander",
        source_type="bank_statement",
        source_account=source_account,
        transactions=transactions,
    ) 
