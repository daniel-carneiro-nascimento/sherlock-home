import pytest

from app.core.runtime_state import runtime_security_state
from app.core.security import SecurityViolation, Severity
from app.core.security_enforcer import (
    CriticalSecurityPolicyError,
    SecurityPolicyError,
    enforce,
)
from app.core.shutdown import (
    reset_shutdown_state,
    shutdown_requested,
)


@pytest.fixture(autouse=True)
def reset_security_and_shutdown_state():
    runtime_security_state.compromised = False
    runtime_security_state.reason = None
    runtime_security_state.rule_id = None

    reset_shutdown_state()

    yield

    runtime_security_state.compromised = False
    runtime_security_state.reason = None
    runtime_security_state.rule_id = None

    reset_shutdown_state()


def test_shutdown_not_requested_initially():
    assert shutdown_requested() is False


def test_normal_violation_does_not_request_shutdown():
    violation = SecurityViolation(
        rule_id="SH-TEST-001",
        severity=Severity.WARNING,
        reason="normal_violation",
        shutdown_required=False,
    )

    with pytest.raises(SecurityPolicyError):
        enforce(violation)

    assert shutdown_requested() is False


def test_critical_violation_requests_shutdown():
    violation = SecurityViolation(
        rule_id="SH-TEST-002",
        severity=Severity.CRITICAL,
        reason="critical_violation",
        shutdown_required=True,
    )

    with pytest.raises(CriticalSecurityPolicyError):
        enforce(violation)

    assert shutdown_requested() is True
    assert runtime_security_state.compromised is True
    assert runtime_security_state.rule_id == "SH-TEST-002"
    assert runtime_security_state.reason == "critical_violation"
