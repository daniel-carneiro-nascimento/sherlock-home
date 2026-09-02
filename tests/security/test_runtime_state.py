import pytest

from app.core.runtime_state import (
    RuntimeCompromisedError,
    ensure_runtime_safe,
    runtime_security_state,
)
from app.core.security import SecurityViolation, Severity
from app.core.security_enforcer import (
    CriticalSecurityPolicyError,
    SecurityPolicyError,
    enforce,
)


@pytest.fixture(autouse=True)
def reset_runtime_security_state():
    """
    Ensure every test starts and ends with a clean runtime state.
    """

    runtime_security_state.compromised = False
    runtime_security_state.reason = None
    runtime_security_state.rule_id = None

    yield

    runtime_security_state.compromised = False
    runtime_security_state.reason = None
    runtime_security_state.rule_id = None


def test_runtime_state_starts_clean():
    assert runtime_security_state.compromised is False
    assert runtime_security_state.reason is None
    assert runtime_security_state.rule_id is None


def test_runtime_allows_operations_when_clean():
    ensure_runtime_safe()


def test_runtime_blocks_operations_when_compromised():
    runtime_security_state.compromised = True
    runtime_security_state.rule_id = "SH-TEST-CRITICAL"
    runtime_security_state.reason = "test_compromise"

    with pytest.raises(RuntimeCompromisedError):
        ensure_runtime_safe()


def test_normal_violation_does_not_compromise_runtime():
    violation = SecurityViolation(
        rule_id="SH-TEST-001",
        severity=Severity.WARNING,
        reason="normal_policy_violation",
        shutdown_required=False,
    )

    with pytest.raises(SecurityPolicyError):
        enforce(violation)

    assert runtime_security_state.compromised is False
    assert runtime_security_state.reason is None
    assert runtime_security_state.rule_id is None


def test_critical_violation_marks_runtime_compromised():
    violation = SecurityViolation(
        rule_id="SH-TEST-002",
        severity=Severity.CRITICAL,
        reason="critical_boundary_violation",
        shutdown_required=True,
    )

    with pytest.raises(CriticalSecurityPolicyError):
        enforce(violation)

    assert runtime_security_state.compromised is True
    assert runtime_security_state.reason == "critical_boundary_violation"
    assert runtime_security_state.rule_id == "SH-TEST-002"


def test_enforce_none_keeps_runtime_clean():
    enforce(None)

    assert runtime_security_state.compromised is False
    assert runtime_security_state.reason is None
    assert runtime_security_state.rule_id is None
