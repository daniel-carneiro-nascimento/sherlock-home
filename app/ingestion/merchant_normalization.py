import re
from dataclasses import replace

from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.rules.merchant_aliases import (
    MerchantAliasRule,
    get_merchant_alias_rules,
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


def resolve_merchant_alias(
    merchant: str,
    *,
    rules: tuple[MerchantAliasRule, ...] | None = None,
) -> str:
    normalized = normalize_merchant_name(
        merchant
    )

    active_rules = (
        get_merchant_alias_rules()
        if rules is None
        else tuple(
            sorted(
                rules,
                key=lambda rule: rule.priority,
            )
        )
    )

    for rule in active_rules:
        if rule.pattern.search(normalized):
            return normalize_merchant_name(
                rule.canonical_name
            )

    return normalized


def normalize_transaction_merchant(
    transaction: CanonicalTransaction,
    *,
    alias_rules: tuple[MerchantAliasRule, ...] | None = None,
) -> CanonicalTransaction:
    merchant = extract_merchant_from_description(
        transaction.original_description
    )

    if merchant is not None:
        merchant = resolve_merchant_alias(
            merchant,
            rules=alias_rules,
        )

    return replace(
        transaction,
        merchant=merchant,
    )


def normalize_statement_merchants(
    statement: CanonicalStatement,
    *,
    alias_rules: tuple[MerchantAliasRule, ...] | None = None,
) -> CanonicalStatement:
    transactions = [
        normalize_transaction_merchant(
            transaction,
            alias_rules=alias_rules,
        )
        for transaction in statement.transactions
    ]

    return replace(
        statement,
        transactions=transactions,
    )
