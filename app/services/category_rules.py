import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category_rule import (
    CategoryRuleModel,
)
from app.rules.categories import (
    CategoryRule,
    CategoryRuleField,
    ExpenseCategory,
    get_category_rules,
    sort_category_rules,
)


def load_category_rules_from_db(
    session: Session,
    *,
    include_defaults: bool = True,
) -> tuple[CategoryRule, ...]:
    rules: list[CategoryRule] = []

    if include_defaults:
        rules.extend(
            get_category_rules()
        )

    rows = session.scalars(
        select(CategoryRuleModel)
        .where(
            CategoryRuleModel.enabled.is_(True)
        )
        .order_by(
            CategoryRuleModel.priority
        )
    ).all()

    for row in rows:
        rules.append(
            CategoryRule(
                category=ExpenseCategory(
                    row.category
                ),
                pattern=re.compile(
                    row.pattern,
                    re.IGNORECASE,
                ),
                field=CategoryRuleField(
                    row.field
                ),
                priority=row.priority,
            )
        )

    return sort_category_rules(
        tuple(rules)
    )
