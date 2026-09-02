from dataclasses import replace
from pathlib import Path

from app.ingestion.normalization import (
    CanonicalStatement,
    CanonicalTransaction,
)
from app.rules.categories import (
    CategoryRule,
    CategoryRuleField,
    build_category_rules,
    sort_category_rules,
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
    local_rules_path: str | Path | None = None,
) -> str | None:
    if transaction.transaction_type != "expense":
        return None

    if rules is not None and local_rules_path is not None:
        raise ValueError(
            "Use either explicit rules or local_rules_path, not both."
        )

    if rules is not None:
        active_rules = sort_category_rules(
            rules
        )
    else:
        active_rules = build_category_rules(
            local_rules_path=local_rules_path,
            include_defaults=True,
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
    local_rules_path: str | Path | None = None,
) -> CanonicalTransaction:
    category = categorize_transaction(
        transaction,
        rules=rules,
        local_rules_path=local_rules_path,
    )

    return replace(
        transaction,
        category=category,
    )


def categorize_statement_expenses(
    statement: CanonicalStatement,
    *,
    rules: tuple[CategoryRule, ...] | None = None,
    local_rules_path: str | Path | None = None,
) -> CanonicalStatement:
    transactions = [
        categorize_transaction_expense(
            transaction,
            rules=rules,
            local_rules_path=local_rules_path,
        )
        for transaction in statement.transactions
    ]

    return replace(
        statement,
        transactions=transactions,
    )
