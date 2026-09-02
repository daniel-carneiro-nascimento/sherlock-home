from dataclasses import replace

from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.rules.categories import (
    CategoryRule,
    CategoryRuleField,
    get_category_rules,
)


def get_rule_value(
    transaction: CanonicalTransaction,
    rule: CategoryRule,
) -> str | None:
    if rule.field == CategoryRuleField.MERCHANT:
        return transaction.merchant

    if rule.field == CategoryRuleField.DESCRIPTION:
        return transaction.original_description

    raise ValueError(
        f"Unsupported category rule field: {rule.field}"
    )


def categorize_transaction(
    transaction: CanonicalTransaction,
    *,
    rules: tuple[CategoryRule, ...] | None = None,
) -> str | None:
    if transaction.transaction_type != "expense":
        return None

    active_rules = (
        get_category_rules()
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
            return rule.category.value

    return None

def categorize_transaction_expense(
    transaction: CanonicalTransaction,
    *,
    rules: tuple[CategoryRule, ...] | None = None,
) -> CanonicalTransaction:
    category = categorize_transaction(
        transaction,
        rules=rules,
    )

    return replace(
        transaction,
        category=category,
    )


def categorize_statement_expenses(
    statement: CanonicalStatement,
    *,
    rules: tuple[CategoryRule, ...] | None = None,
) -> CanonicalStatement:
    transactions = [
        categorize_transaction_expense(
            transaction,
            rules=rules,
        )
        for transaction in statement.transactions
    ]

    return replace(
        statement,
        transactions=transactions,
    ) 
