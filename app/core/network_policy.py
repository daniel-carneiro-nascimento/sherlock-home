from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.security import SecurityViolation, Severity


@dataclass(frozen=True)
class ApprovedEndpoint:
    scheme: str
    host: str
    port: int | None


APPROVED_ENDPOINTS = {
    ApprovedEndpoint(
        scheme="http",
        host="127.0.0.1",
        port=11434,
    ),
    ApprovedEndpoint(
        scheme="http",
        host="localhost",
        port=11434,
    ),
}


def validate_endpoint(url: str) -> SecurityViolation | None:
    parsed = urlparse(url)

    endpoint = ApprovedEndpoint(
        scheme=parsed.scheme,
        host=parsed.hostname or "",
        port=parsed.port,
    )

    if endpoint not in APPROVED_ENDPOINTS:
        return SecurityViolation(
            rule_id="SH-NET-001",
            severity=Severity.CRITICAL,
            reason="unauthorized_network_destination",
            shutdown_required=False,
        )

    return None
