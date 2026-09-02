import re

from app.core.security import SecurityViolation, Severity


SECRET_PATTERNS = {
    "credit_card": re.compile(
        r"\b(?:\d[ -]*?){13,19}\b"
    ),
    "api_key_generic": re.compile(
        r"\b(?:api[_-]?key|apikey|token|secret)\s*[:=]\s*[A-Za-z0-9_\-]{12,}\b",
        re.IGNORECASE,
    ),
    "bearer_token": re.compile(
        r"\bBearer\s+[A-Za-z0-9._\-]{12,}\b",
        re.IGNORECASE,
    ),
    "private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "password_assignment": re.compile(
        r"\b(?:password|passwd|pwd)\s*[:=]\s*\S+",
        re.IGNORECASE,
    ),
}


def detect_secret(text: str) -> SecurityViolation | None:
    for secret_type, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            return SecurityViolation(
                rule_id="SH-SECRET-001",
                severity=Severity.CRITICAL,
                reason=f"detected_{secret_type}",
                shutdown_required=False,
            )

    return None
