import re

from app.core.security import SecurityViolation, Severity


POLICY_BYPASS_PATTERNS = {
    "ignore_instructions": re.compile(
        r"\b(ignore|disregard|forget)\s+"
        r"(all\s+)?"
        r"(previous|prior|system|security)\s+"
        r"((system|security)\s+)?"
        r"(instructions?|rules?|policies?)\b",
        re.IGNORECASE,
    ),

    "disable_security": re.compile(
        r"\b(disable|turn\s+off|remove|deactivate)\s+"
        r"(the\s+)?(security|policy|security\s+policy|security\s+controls?)\b",
        re.IGNORECASE,
    ),

    "bypass_security": re.compile(
        r"\b(bypass|circumvent|override|evade)\s+"
        r"(the\s+)?(security|policy|security\s+policy|security\s+controls?)\b",
        re.IGNORECASE,
    ),

    "rules_do_not_apply": re.compile(
        r"\b(pretend|assume|act\s+as\s+if)\b.*"
        r"\b(rules?|policies?|restrictions?)\b.*"
        r"\b(do\s+not|don't|dont)\s+apply\b",
        re.IGNORECASE,
    ),

    "system_prompt_extraction": re.compile(
        r"\b(reveal|show|print|dump|expose)\b.*"
        r"\b(system\s+prompt|hidden\s+instructions?|internal\s+instructions?)\b",
        re.IGNORECASE,
    ),

    "security_rule_override": re.compile(
        r"\b(ignore|override|disable|bypass)\b.*"
        r"\bSH-[A-Z]+-\d{3}\b",
        re.IGNORECASE,
    ),
}


def detect_policy_bypass(text: str) -> SecurityViolation | None:
    for bypass_type, pattern in POLICY_BYPASS_PATTERNS.items():
        if pattern.search(text):
            return SecurityViolation(
                rule_id="SH-POLICY-001",
                severity=Severity.WARNING,
                reason=f"detected_{bypass_type}",
                shutdown_required=False,
            )

    return None
