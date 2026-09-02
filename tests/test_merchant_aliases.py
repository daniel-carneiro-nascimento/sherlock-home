import re

from app.ingestion.merchant_normalization import (
    resolve_merchant_alias,
)
from app.rules.merchant_aliases import (
    MERCHANT_ALIAS_RULES,
    MerchantAliasRule,
    get_merchant_alias_rules,
)


def test_default_alias_registry_is_explicitly_empty():
    assert MERCHANT_ALIAS_RULES == ()
    assert get_merchant_alias_rules() == ()


def test_unknown_merchant_is_preserved():
    merchant = "SYNTHETIC COMPANY"

    assert (
        resolve_merchant_alias(merchant)
        == "SYNTHETIC COMPANY"
    )


def test_alias_rule_maps_variant_to_canonical_name():
    rules = (
        MerchantAliasRule(
            canonical_name="SYNTHETIC MARKET",
            pattern=re.compile(
                r"^SYNTHETIC MARKET(?:\s+\*\d+)?$",
                re.IGNORECASE,
            ),
            priority=10,
        ),
    )

    assert (
        resolve_merchant_alias(
            "synthetic market *1234",
            rules=rules,
        )
        == "SYNTHETIC MARKET"
    )


def test_alias_canonical_name_is_normalized():
    rules = (
        MerchantAliasRule(
            canonical_name="  Synthetic   Market  ",
            pattern=re.compile(
                r"^SYNTHETIC MARKET ALT$",
                re.IGNORECASE,
            ),
            priority=10,
        ),
    )

    assert (
        resolve_merchant_alias(
            "SYNTHETIC MARKET ALT",
            rules=rules,
        )
        == "SYNTHETIC MARKET"
    )


def test_alias_rule_priority_is_deterministic():
    rules = (
        MerchantAliasRule(
            canonical_name="LOW PRIORITY RESULT",
            pattern=re.compile(
                r"SYNTHETIC",
                re.IGNORECASE,
            ),
            priority=200,
        ),
        MerchantAliasRule(
            canonical_name="HIGH PRIORITY RESULT",
            pattern=re.compile(
                r"SYNTHETIC",
                re.IGNORECASE,
            ),
            priority=10,
        ),
    )

    assert (
        resolve_merchant_alias(
            "SYNTHETIC MERCHANT",
            rules=rules,
        )
        == "HIGH PRIORITY RESULT"
    )


def test_alias_resolution_is_idempotent():
    rules = (
        MerchantAliasRule(
            canonical_name="SYNTHETIC MARKET",
            pattern=re.compile(
                r"^SYNTHETIC MARKET(?:\s+\*\d+)?$",
                re.IGNORECASE,
            ),
            priority=10,
        ),
    )

    first = resolve_merchant_alias(
        "SYNTHETIC MARKET *1234",
        rules=rules,
    )

    second = resolve_merchant_alias(
        first,
        rules=rules,
    )

    assert first == "SYNTHETIC MARKET"
    assert second == first
