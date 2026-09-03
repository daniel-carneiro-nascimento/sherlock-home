import secrets


CATEGORY_RULE_PREFIX = "cr_"
MERCHANT_ALIAS_PREFIX = "ma_"
AUDIT_EVENT_PREFIX = "ae_"

# 18 random bytes = 144 bits of entropy before URL-safe encoding.
_PUBLIC_ID_RANDOM_BYTES = 18


def _generate_public_id(prefix: str) -> str:
    return prefix + secrets.token_urlsafe(_PUBLIC_ID_RANDOM_BYTES)


def generate_category_rule_id() -> str:
    return _generate_public_id(CATEGORY_RULE_PREFIX)


def generate_merchant_alias_id() -> str:
    return _generate_public_id(MERCHANT_ALIAS_PREFIX)


def generate_audit_event_id() -> str:
    return _generate_public_id(AUDIT_EVENT_PREFIX)


def is_category_rule_id(value: str) -> bool:
    return value.startswith(CATEGORY_RULE_PREFIX)


def is_merchant_alias_id(value: str) -> bool:
    return value.startswith(MERCHANT_ALIAS_PREFIX)


def is_audit_event_id(value: str) -> bool:
    return value.startswith(AUDIT_EVENT_PREFIX)
