from sqlalchemy.orm import Session

from app.models.category_rule import (
    CategoryRuleModel,
)
from app.services.category_rules import (
    load_category_rules_from_db,
)


def test_category_rule_can_be_loaded_from_db(
    db_session: Session,
):
    db_session.add(
        CategoryRuleModel(
            category="leisure",
            field="merchant",
            pattern=r"\bSYNTHETIC CINEMA\b",
            priority=5,
            enabled=True,
        )
    )
    db_session.commit()

    rules = load_category_rules_from_db(
        db_session,
        include_defaults=False,
    )

    assert len(rules) == 1
    assert rules[0].category.value == "leisure"
    assert rules[0].field.value == "merchant"
    assert rules[0].priority == 5
