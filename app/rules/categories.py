import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import yaml


class ExpenseCategory(StrEnum):
    FOOD = "food"
    GROCERIES = "groceries"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    HEALTH = "health"
    SHOPPING = "shopping"
    HOUSING = "housing"
    FINANCING = "financing"
    LEISURE = "leisure"
    TAXES = "taxes"


class CategoryRuleField(StrEnum):
    MERCHANT = "merchant"
    DESCRIPTION = "description"


@dataclass(frozen=True)
class CategoryRule:
    category: ExpenseCategory
    pattern: re.Pattern[str]
    field: CategoryRuleField
    priority: int


DEFAULT_CATEGORY_RULES: tuple[CategoryRule, ...] = (
    CategoryRule(
        category=ExpenseCategory.HOUSING,
        pattern=re.compile(
            r"\b(RENT|ALUGUEL)\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.DESCRIPTION,
        priority=30,
    ),
    CategoryRule(
        category=ExpenseCategory.FINANCING,
        pattern=re.compile(
            r"\bFINANCIAMENTO\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.DESCRIPTION,
        priority=40,
    ),
    CategoryRule(
        category=ExpenseCategory.TAXES,
        pattern=re.compile(
            r"\b(IMPOSTO|IMPOSTOS)\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.DESCRIPTION,
        priority=50,
    ),
    CategoryRule(
        category=ExpenseCategory.LEISURE,
        pattern=re.compile(
            r"\bLAZER\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.DESCRIPTION,
        priority=60,
    ),
    CategoryRule(
        category=ExpenseCategory.GROCERIES,
        pattern=re.compile(
            r"\b(MARKET|MERCADO|SUPERMERCADO|GROCERY)\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=100,
    ),
    CategoryRule(
        category=ExpenseCategory.FOOD,
        pattern=re.compile(
            r"\b(RESTAURANT|RESTAURANTE|CAFE|CAFÉ|PIZZA|FOOD)\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=110,
    ),
    CategoryRule(
        category=ExpenseCategory.TRANSPORT,
        pattern=re.compile(
            r"\b("
            r"TRANSPORT|TAXI|UBER|METRO|METRÔ|BUS|PARKING|"
            r"COMBUSTIVEL|COMBUSTÍVEL"
            r")\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=120,
    ),
    CategoryRule(
        category=ExpenseCategory.UTILITIES,
        pattern=re.compile(
            r"\b("
            r"ELECTRIC|ENERGY|WATER|INTERNET|TELECOM|"
            r"GAS DE COZINHA|GÁS DE COZINHA"
            r")\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=130,
    ),
    CategoryRule(
        category=ExpenseCategory.HEALTH,
        pattern=re.compile(
            r"\b("
            r"PHARMACY|FARMACIA|FARMÁCIA|CLINIC|CLINICA|"
            r"CLÍNICA|HOSPITAL"
            r")\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=140,
    ),
    CategoryRule(
        category=ExpenseCategory.SHOPPING,
        pattern=re.compile(
            r"\b(STORE|SHOP|LOJA)\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=150,
    ),
)

# Backward-compatible public name.
CATEGORY_RULES = DEFAULT_CATEGORY_RULES


def validate_category_rules(
    rules: tuple[CategoryRule, ...],
) -> None:
    priorities = [rule.priority for rule in rules]

    if len(priorities) != len(set(priorities)):
        raise ValueError(
            "Category rule priorities must be unique."
        )

    for rule in rules:
        if rule.priority <= 0:
            raise ValueError(
                "Category rule priorities must be positive."
            )


def sort_category_rules(
    rules: tuple[CategoryRule, ...],
) -> tuple[CategoryRule, ...]:
    validate_category_rules(rules)

    return tuple(
        sorted(
            rules,
            key=lambda rule: rule.priority,
        )
    )


def get_category_rules() -> tuple[CategoryRule, ...]:
    return sort_category_rules(DEFAULT_CATEGORY_RULES)


def _parse_category_rule(
    raw: object,
) -> CategoryRule:
    if not isinstance(raw, dict):
        raise ValueError(
            "Each local category rule must be a mapping."
        )

    required = {
        "category",
        "field",
        "pattern",
        "priority",
    }

    missing = required.difference(raw)

    if missing:
        raise ValueError(
            "Local category rule is missing required keys: "
            + ", ".join(sorted(missing))
        )

    try:
        category = ExpenseCategory(
            str(raw["category"])
        )
    except ValueError as exc:
        raise ValueError(
            f"Unknown expense category: {raw['category']}"
        ) from exc

    try:
        field = CategoryRuleField(
            str(raw["field"])
        )
    except ValueError as exc:
        raise ValueError(
            f"Unknown category rule field: {raw['field']}"
        ) from exc

    pattern_value = str(raw["pattern"])

    if not pattern_value:
        raise ValueError(
            "Category rule pattern must not be empty."
        )

    try:
        priority = int(raw["priority"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Category rule priority must be an integer."
        ) from exc

    try:
        pattern = re.compile(
            pattern_value,
            re.IGNORECASE,
        )
    except re.error as exc:
        raise ValueError(
            f"Invalid category rule regex: {pattern_value}"
        ) from exc

    return CategoryRule(
        category=category,
        pattern=pattern,
        field=field,
        priority=priority,
    )


def load_local_category_rules(
    path: str | Path,
) -> tuple[CategoryRule, ...]:
    path = Path(path)

    if not path.exists():
        return ()

    payload = yaml.safe_load(
        path.read_text(
            encoding="utf-8",
        )
    )

    if payload is None:
        return ()

    if not isinstance(payload, dict):
        raise ValueError(
            "Local category rule file must contain a mapping."
        )

    raw_rules = payload.get("rules", [])

    if not isinstance(raw_rules, list):
        raise ValueError(
            "Local category rule file key 'rules' must be a list."
        )

    rules = tuple(
        _parse_category_rule(raw)
        for raw in raw_rules
    )

    return sort_category_rules(rules)


def build_category_rules(
    *,
    local_rules_path: str | Path | None = None,
    include_defaults: bool = True,
) -> tuple[CategoryRule, ...]:
    rules: list[CategoryRule] = []

    if include_defaults:
        rules.extend(
            DEFAULT_CATEGORY_RULES
        )

    if local_rules_path is not None:
        rules.extend(
            load_local_category_rules(
                local_rules_path
            )
        )

    return sort_category_rules(
        tuple(rules)
    )
