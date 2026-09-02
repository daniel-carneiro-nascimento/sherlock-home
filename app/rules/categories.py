import re
from dataclasses import dataclass
from enum import StrEnum


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


CATEGORY_RULES: tuple[CategoryRule, ...] = (
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
            r"\b("
            r"MARKET|"
            r"MERCADO|"
            r"SUPERMERCADO|"
            r"GROCERY"
            r")\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=100,
    ),

    CategoryRule(
        category=ExpenseCategory.FOOD,
        pattern=re.compile(
            r"\b("
            r"RESTAURANT|"
            r"RESTAURANTE|"
            r"CAFE|"
            r"CAFÉ|"
            r"PIZZA|"
            r"FOOD"
            r")\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=110,
    ),

    CategoryRule(
        category=ExpenseCategory.TRANSPORT,
        pattern=re.compile(
            r"\b("
            r"TRANSPORT|"
            r"TAXI|"
            r"UBER|"
            r"METRO|"
            r"METRÔ|"
            r"BUS|"
            r"PARKING|"
            r"COMBUSTIVEL|"
            r"COMBUSTÍVEL"
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
            r"ELECTRIC|"
            r"ENERGY|"
            r"WATER|"
            r"INTERNET|"
            r"TELECOM|"
            r"GAS DE COZINHA|"
            r"GÁS DE COZINHA"
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
            r"PHARMACY|"
            r"FARMACIA|"
            r"FARMÁCIA|"
            r"CLINIC|"
            r"CLINICA|"
            r"CLÍNICA|"
            r"HOSPITAL"
            r")\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=140,
    ),

    CategoryRule(
        category=ExpenseCategory.SHOPPING,
        pattern=re.compile(
            r"\b("
            r"STORE|"
            r"SHOP|"
            r"LOJA"
            r")\b",
            re.IGNORECASE,
        ),
        field=CategoryRuleField.MERCHANT,
        priority=150,
    ),
)


def get_category_rules() -> tuple[CategoryRule, ...]:
    return tuple(
        sorted(
            CATEGORY_RULES,
            key=lambda rule: rule.priority,
        )
    ) 
