from datetime import date
from decimal import Decimal
from pathlib import Path

from app.ingestion.santander_pdf import (
    parse_brazilian_decimal,
    parse_statement,
)


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "santander_statement.txt"
)


def test_parse_positive_brazilian_decimal():
    assert parse_brazilian_decimal(
        "2.689,52"
    ) == Decimal("2689.52")


def test_parse_negative_brazilian_decimal():
    assert parse_brazilian_decimal(
        "4.121,13-"
    ) == Decimal("-4121.13")


def test_parse_statement_period():
    text = FIXTURE.read_text(encoding="utf-8")

    statement = parse_statement(text)

    assert statement.statement_month == date(2026, 6, 1)


def test_parse_transactions():
    text = FIXTURE.read_text(encoding="utf-8")

    statement = parse_statement(text)

    assert len(statement.transactions) == 4

    tx1 = statement.transactions[0]

    assert tx1.date == date(2026, 6, 9)
    assert tx1.amount == Decimal("-23.50")
    assert tx1.balance == Decimal("-4079.52")

    tx2 = statement.transactions[1]

    assert tx2.date == date(2026, 6, 10)
    assert tx2.amount == Decimal("-139.90")

    tx3 = statement.transactions[2]

    assert tx3.date == date(2026, 6, 11)
    assert tx3.amount == Decimal("-298.00")

    tx4 = statement.transactions[3]

    assert tx4.date == date(2026, 6, 11)
    assert tx4.amount == Decimal("-149.29")

    assert (
        "MERCHANT TEST CONTINUATION"
        in tx4.description
    )
