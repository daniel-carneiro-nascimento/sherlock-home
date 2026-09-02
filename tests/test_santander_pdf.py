from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.ingestion.santander_pdf import (
    parse_brazilian_decimal,
    parse_statement,
)


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "santander_statement.txt"
)


def test_parse_statement_period():
    text = FIXTURE.read_text(encoding="utf-8")

    statement = parse_statement(text)

    assert statement.statement_month == date(2026, 6, 1)


def test_parse_transactions_structure():
    text = FIXTURE.read_text(encoding="utf-8")

    statement = parse_statement(text)

    assert len(statement.transactions) == 4

    for tx in statement.transactions:
        assert isinstance(tx.date, date)
        assert isinstance(tx.amount, Decimal)

        assert tx.description.strip()
        assert tx.amount != Decimal("0")

    dates = [
        tx.date
        for tx in statement.transactions
    ]

    assert dates == [
        date(2026, 6, 9),
        date(2026, 6, 10),
        date(2026, 6, 11),
        date(2026, 6, 11),
    ]


def test_multiline_description_is_joined():
    text = FIXTURE.read_text(encoding="utf-8")

    statement = parse_statement(text)

    tx = statement.transactions[-1]

    assert (
        "MERCHANT TEST CONTINUATION"
        in tx.description
    )


def test_transaction_can_inherit_previous_date():
    text = FIXTURE.read_text(encoding="utf-8")

    statement = parse_statement(text)

    first_same_day = statement.transactions[2]
    second_same_day = statement.transactions[3]

    assert first_same_day.date == second_same_day.date


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "23,50-",
            Decimal("-23.50"),
        ),
        (
            "79,52-",
            Decimal("-79.52"),
        ),
        (
            "500,00",
            Decimal("500.00"),
        ),
        (
            "1.250,00",
            Decimal("1250.00"),
        ),
        (
            "1.234,56-",
            Decimal("-1234.56"),
        ),
        (
            "9.999,99-",
            Decimal("-9999.99"),
        ),
        (
            "1.234.567,89",
            Decimal("1234567.89"),
        ),
    ],
)
def test_parse_brazilian_decimal(
    raw: str,
    expected: Decimal,
):
    assert (
        parse_brazilian_decimal(raw)
        == expected
    )


@pytest.mark.parametrize(
    (
        "movement",
        "balance",
        "expected_amount",
        "expected_balance",
    ),
    [
        (
            "23,50-",
            "79,52-",
            Decimal("-23.50"),
            Decimal("-79.52"),
        ),
        (
            "500,00",
            "1.250,00",
            Decimal("500.00"),
            Decimal("1250.00"),
        ),
        (
            "1.234,56-",
            "9.999,99-",
            Decimal("-1234.56"),
            Decimal("-9999.99"),
        ),
    ],
)
def test_parse_transaction_with_arbitrary_values(
    movement: str,
    balance: str,
    expected_amount: Decimal,
    expected_balance: Decimal,
):
    text = f"""
EXTRATO CONSOLIDADO INTELIGENTE
junho/2026

Movimentação
Data        Descrição                    Nº Documento       Movimento (R$)       Saldo (R$)
09/06       MERCHANT TEST                000001             {movement}           {balance}

Conta Corrente    Bloqueio    Bloqueado
"""

    statement = parse_statement(text)

    assert len(statement.transactions) == 1

    tx = statement.transactions[0]

    assert tx.amount == expected_amount
    assert tx.balance == expected_balance 
