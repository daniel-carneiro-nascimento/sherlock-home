import re
from dataclasses import dataclass
from enum import StrEnum


class TransactionType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class TransactionTypeRuleField(StrEnum):
    DESCRIPTION = "description"


@dataclass(frozen=True)
class TransactionTypeRule:
    transaction_type: TransactionType
    pattern: re.Pattern[str]
    field: TransactionTypeRuleField
    priority: int


TRANSACTION_TYPE_RULES: tuple[TransactionTypeRule, ...] = (
    TransactionTypeRule(
        transaction_type=TransactionType.INCOME,
        pattern=re.compile(
            r"\b("
            r"SALARIO|"
            r"SALÁRIO|"
            r"SALARY|"
            r"PAYROLL"
            r")\b",
            re.IGNORECASE,
        ),
        field=TransactionTypeRuleField.DESCRIPTION,
        priority=10,
    ),
    TransactionTypeRule(
        transaction_type=TransactionType.TRANSFER,
        pattern=re.compile(
            r"\bTRANSFERENCIA INTERNA\b",
            re.IGNORECASE,
        ),
        field=TransactionTypeRuleField.DESCRIPTION,
        priority=20,
    ),
)


def get_transaction_type_rules(
) -> tuple[TransactionTypeRule, ...]:
    return tuple(
        sorted(
            TRANSACTION_TYPE_RULES,
            key=lambda rule: rule.priority,
        )
    )
