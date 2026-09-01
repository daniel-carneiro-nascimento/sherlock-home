import os
import signal

from app.core.audit import log_security_event
from app.core.security import SecurityViolation


class SecurityPolicyError(RuntimeError):
    pass


def enforce(violation: SecurityViolation | None) -> None:
    if violation is None:
        return

    log_security_event(violation)

    if violation.shutdown_required:
        # For now raise an exception instead of killing the process.
        #
        # Actual process shutdown should only be enabled after
        # lifecycle handling and tests are in place.
        raise SecurityPolicyError(
            f"Critical security policy violation: {violation.rule_id}"
        )

    raise SecurityPolicyError(
        f"Security policy violation: {violation.rule_id}"
    )
