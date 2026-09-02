from app.rules.transaction_types import (
    TRANSACTION_TYPE_RULES,
    TransactionType,
    get_transaction_type_rules,
)


def test_transaction_type_values_are_unique():
    values = [
        transaction_type.value
        for transaction_type in TransactionType
    ]

    assert len(values) == len(set(values))


def test_transaction_type_rule_priorities_are_unique():
    priorities = [
        rule.priority
        for rule in TRANSACTION_TYPE_RULES
    ]

    assert len(priorities) == len(
        set(priorities)
    )


def test_transaction_type_rules_are_sorted():
    rules = get_transaction_type_rules()

    priorities = [
        rule.priority
        for rule in rules
    ]

    assert priorities == sorted(priorities)


def test_transaction_type_taxonomy():
    assert {
        transaction_type.value
        for transaction_type in TransactionType
    } == {
        "expense",
        "income",
        "transfer",
    }
