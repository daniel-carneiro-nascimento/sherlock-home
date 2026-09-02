from app.rules.categories import (
    CATEGORY_RULES,
    CategoryRuleField,
    ExpenseCategory,
    get_category_rules,
)


def test_category_values_are_unique():
    values = [
        category.value
        for category in ExpenseCategory
    ]

    assert len(values) == len(set(values))


def test_category_rule_priorities_are_unique():
    priorities = [
        rule.priority
        for rule in CATEGORY_RULES
    ]

    assert len(priorities) == len(
        set(priorities)
    )


def test_category_rules_are_returned_by_priority():
    rules = get_category_rules()

    priorities = [
        rule.priority
        for rule in rules
    ]

    assert priorities == sorted(priorities)


def test_every_category_has_at_least_one_rule():
    categories_with_rules = {
        rule.category
        for rule in CATEGORY_RULES
    }

    assert categories_with_rules == set(
        ExpenseCategory
    )


def test_all_rule_fields_are_valid():
    valid_fields = set(
        CategoryRuleField
    )

    for rule in CATEGORY_RULES:
        assert rule.field in valid_fields


def test_priorities_are_positive():
    for rule in CATEGORY_RULES:
        assert rule.priority > 0


def test_taxonomy_contains_expected_categories():
    expected = {
        "food",
        "groceries",
        "transport",
        "utilities",
        "health",
        "shopping",
        "housing",
        "financing",
        "leisure",
        "taxes",
    }

    actual = {
        category.value
        for category in ExpenseCategory
    }

    assert actual == expected
