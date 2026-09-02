import re
from dataclasses import replace

from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)


WHITESPACE_RE = re.compile(r"\s+")


def normalize_merchant_name(value: str) -> str:
    value = WHITESPACE_RE.sub(" ", value).strip()

    return value.upper()


def extract_merchant_from_description(
    description: str,
) -> str | None:
    normalized = WHITESPACE_RE.sub(
        " ",
        description,
    ).strip()

    if not normalized:
        return None

    patterns = [
        # Santander debit-card style:
        #
        # COMPRA CARTAO DEB MC 09/06 MERCHANT TEST
        re.compile(
            r"^COMPRA CARTAO DEB(?:\s+\S+)?"
            r"(?:\s+\d{2}/\d{2})?\s+(.+)$",
            re.IGNORECASE,
        ),

        # Boleto payment:
        #
        # PAGAMENTO DE BOLETO COMPANY TEST
        re.compile(
            r"^PAGAMENTO DE BOLETO\s+(.+)$",
            re.IGNORECASE,
        ),

        # PIX sent:
        #
        # PIX ENVIADO Pix Marketplace MERCHANT TEST
        re.compile(
            r"^PIX ENVIADO"
            r"(?:\s+Pix Marketplace)?"
            r"\s+(.+)$",
            re.IGNORECASE,
        ),

        # PIX received:
        #
        # PIX RECEBIDO COMPANY TEST
        re.compile(
            r"^PIX RECEBIDO\s+(.+)$",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        match = pattern.match(normalized)

        if not match:
            continue

        merchant = match.group(1).strip()

        if merchant:
            return normalize_merchant_name(
                merchant
            )

    return None


def normalize_transaction_merchant(
    transaction: CanonicalTransaction,
) -> CanonicalTransaction:
    merchant = extract_merchant_from_description(
        transaction.original_description
    )

    return replace(
        transaction,
        merchant=merchant,
    )


def normalize_statement_merchants(
    statement: CanonicalStatement,
) -> CanonicalStatement:
    transactions = [
        normalize_transaction_merchant(
            transaction
        )
        for transaction in statement.transactions
    ]

    return replace(
        statement,
        transactions=transactions,
    ) 
