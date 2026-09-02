import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MerchantAliasRule:
    canonical_name: str
    pattern: re.Pattern[str]
    priority: int


# The default registry is intentionally empty.
#
# Sherlock Home should not guess that two merchant strings represent the
# same business. Aliases are explicit deterministic rules and can be added
# later from reviewed local configuration or project-level rules.
MERCHANT_ALIAS_RULES: tuple[MerchantAliasRule, ...] = ()


def get_merchant_alias_rules() -> tuple[MerchantAliasRule, ...]:
    return tuple(
        sorted(
            MERCHANT_ALIAS_RULES,
            key=lambda rule: rule.priority,
        )
    )
