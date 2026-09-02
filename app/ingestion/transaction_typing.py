from dataclasses import replace

from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.rules.transaction_types import (
    TransactionType,
    TransactionTypeRule,
    TransactionTypeRuleField,
    get_transaction_type_rules,
)


def get_rule_value(
    transaction: CanonicalTransaction,
    rule: TransactionTypeRule,
) -> str | None:
    if rule.field == TransactionTypeRuleField.DESCRIPTION:
        return transaction.original_description

    raise ValueError(
        f"Unsupported transaction type rule field: {rule.field}"
    )


def classify_transaction_type(
    transaction: CanonicalTransaction,
    *,
    rules: tuple[TransactionTypeRule, ...] | None = None,
) -> str:
    active_rules = (
        get_transaction_type_rules()
        if rules is None
        else tuple(
            sorted(
                rules,
                key=lambda rule: rule.priority,
            )
        )
    )

    for rule in active_rules:
        value = get_rule_value(
            transaction,
            rule,
        )

        if not value:
            continue

        if rule.pattern.search(value):
            return rule.transaction_type.value

    if transaction.amount < 0:
        return TransactionType.EXPENSE.value

    return TransactionType.INCOME.value


def classify_transaction(
    transaction: CanonicalTransaction,
    *,
    rules: tuple[TransactionTypeRule, ...] | None = None,
) -> CanonicalTransaction:
    transaction_type = classify_transaction_type(
        transaction,
        rules=rules,
    )

    return replace(
        transaction,
        transaction_type=transaction_type,
    )


def classify_statement_transactions(
    statement: CanonicalStatement,
    *,
    rules: tuple[TransactionTypeRule, ...] | None = None,
) -> CanonicalStatement:
    transactions = [
        classify_transaction(
            transaction,
            rules=rules,
        )
        for transaction in statement.transactions
    ]

    return replace(
        statement,
        transactions=transactions,
    )
