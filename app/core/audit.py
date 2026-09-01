import json
import sys
from datetime import datetime, timezone

from app.core.security import SecurityViolation


def log_security_event(violation: SecurityViolation) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "SECURITY_EVENT",
        "rule": violation.rule_id,
        "severity": violation.severity.value,
        "action": "blocked",
        "reason": violation.reason,
    }

    print(
        json.dumps(event, separators=(",", ":")),
        file=sys.stdout,
        flush=True,
    )
