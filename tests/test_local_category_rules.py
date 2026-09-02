from pathlib import Path

import pytest

from app.rules.categories import (
    ExpenseCategory,
    build_category_rules,
    load_local_category_rules,
)


def write_rules(
    path: Path,
    content: str,
) -> Path:
    path.write_text(
        content,
        encoding="utf-8",
    )
    return path


def test_missing_local_rule_file_returns_no_rules(
    tmp_path: Path,
):
    path = tmp_path / "missing.yaml"

    assert (
        load_local_category_rules(path)
        == ()
    )


def test_empty_local_rule_file_returns_no_rules(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        "",
    )

    assert (
        load_local_category_rules(path)
        == ()
    )


def test_local_rules_are_loaded_and_sorted(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: leisure
    field: merchant
    pattern: "\\\\bSYNTHETIC CINEMA\\\\b"
    priority: 20
  - category: food
    field: merchant
    pattern: "\\\\bSYNTHETIC BAKERY\\\\b"
    priority: 10
""",
    )

    rules = load_local_category_rules(path)

    assert [
        rule.priority
        for rule in rules
    ] == [
        10,
        20,
    ]

    assert [
        rule.category
        for rule in rules
    ] == [
        ExpenseCategory.FOOD,
        ExpenseCategory.LEISURE,
    ]


def test_unknown_local_category_is_rejected(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: invalid
    field: merchant
    pattern: TEST
    priority: 10
""",
    )

    with pytest.raises(
        ValueError,
        match="Unknown expense category",
    ):
        load_local_category_rules(path)


def test_unknown_local_field_is_rejected(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: food
    field: invalid
    pattern: TEST
    priority: 10
""",
    )

    with pytest.raises(
        ValueError,
        match="Unknown category rule field",
    ):
        load_local_category_rules(path)


def test_invalid_regex_is_rejected(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: food
    field: merchant
    pattern: "["
    priority: 10
""",
    )

    with pytest.raises(
        ValueError,
        match="Invalid category rule regex",
    ):
        load_local_category_rules(path)


def test_duplicate_local_priorities_are_rejected(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: food
    field: merchant
    pattern: TEST A
    priority: 10
  - category: leisure
    field: merchant
    pattern: TEST B
    priority: 10
""",
    )

    with pytest.raises(
        ValueError,
        match="priorities must be unique",
    ):
        load_local_category_rules(path)


def test_local_rule_can_override_default_by_priority(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: leisure
    field: merchant
    pattern: "\\\\bTEST RESTAURANT\\\\b"
    priority: 5
""",
    )

    rules = build_category_rules(
        local_rules_path=path,
        include_defaults=True,
    )

    assert rules[0].priority == 5
    assert rules[0].category == ExpenseCategory.LEISURE


def test_local_rule_priority_collision_with_default_is_rejected(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: leisure
    field: merchant
    pattern: TEST
    priority: 110
""",
    )

    with pytest.raises(
        ValueError,
        match="priorities must be unique",
    ):
        build_category_rules(
            local_rules_path=path,
            include_defaults=True,
        )


def test_defaults_can_be_disabled(
    tmp_path: Path,
):
    path = write_rules(
        tmp_path / "rules.yaml",
        """
rules:
  - category: leisure
    field: merchant
    pattern: TEST
    priority: 10
""",
    )

    rules = build_category_rules(
        local_rules_path=path,
        include_defaults=False,
    )

    assert len(rules) == 1
    assert rules[0].category == ExpenseCategory.LEISURE
