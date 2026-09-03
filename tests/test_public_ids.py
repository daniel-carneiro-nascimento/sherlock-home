from app.core.public_ids import (
    AUDIT_EVENT_PREFIX,
    CATEGORY_RULE_PREFIX,
    MERCHANT_ALIAS_PREFIX,
    generate_audit_event_id,
    generate_category_rule_id,
    generate_merchant_alias_id,
    is_audit_event_id,
    is_category_rule_id,
    is_merchant_alias_id,
)


def test_category_rule_id_has_expected_prefix():
    value = generate_category_rule_id()

    assert value.startswith(CATEGORY_RULE_PREFIX)
    assert is_category_rule_id(value)
    assert not is_merchant_alias_id(value)
    assert not is_audit_event_id(value)


def test_merchant_alias_id_has_expected_prefix():
    value = generate_merchant_alias_id()

    assert value.startswith(MERCHANT_ALIAS_PREFIX)
    assert is_merchant_alias_id(value)
    assert not is_category_rule_id(value)
    assert not is_audit_event_id(value)


def test_audit_event_id_has_expected_prefix():
    value = generate_audit_event_id()

    assert value.startswith(AUDIT_EVENT_PREFIX)
    assert is_audit_event_id(value)
    assert not is_category_rule_id(value)
    assert not is_merchant_alias_id(value)


def test_generated_public_ids_are_not_equal():
    assert (
        generate_category_rule_id()
        != generate_category_rule_id()
    )

    assert (
        generate_merchant_alias_id()
        != generate_merchant_alias_id()
    )

    assert (
        generate_audit_event_id()
        != generate_audit_event_id()
    )
