from app.core.audit import log_security_event
from app.core.runtime_state import runtime_security_state
from app.core.security import SecurityViolation
from app.core.shutdown import request_shutdown


class SecurityPolicyError(RuntimeError):
    pass


class CriticalSecurityPolicyError(SecurityPolicyError):
    pass


def enforce(violation: SecurityViolation | None) -> None:
    if violation is None:
        return

    log_security_event(violation)

    if violation.shutdown_required:
        runtime_security_state.compromised = True
        runtime_security_state.reason = violation.reason
        runtime_security_state.rule_id = violation.rule_id

        request_shutdown()

        raise CriticalSecurityPolicyError(
            f"Critical security policy violation: {violation.rule_id}"
        )

    raise SecurityPolicyError(
        f"Security policy violation: {violation.rule_id}"
    ) 
