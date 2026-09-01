from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SecurityViolation:
    rule_id: str
    severity: Severity
    reason: str
    shutdown_required: bool = False


class SecurityPolicy:
    """
    Deterministic security policy for Sherlock Home.

    This layer must not depend on LLM judgment.
    """

    APPROVED_LOCAL_HOSTS = {
        "127.0.0.1",
        "localhost",
    }

    APPROVED_MODELS = {
        "qwen3:14b",
        "qwen3:4b",
    }

    def validate_model(self, model: str) -> SecurityViolation | None:
        if model not in self.APPROVED_MODELS:
            return SecurityViolation(
                rule_id="SH-AI-001",
                severity=Severity.CRITICAL,
                reason="unauthorized_ai_model",
                shutdown_required=False,
            )

        return None

    def validate_destination(self, host: str) -> SecurityViolation | None:
        if host not in self.APPROVED_LOCAL_HOSTS:
            return SecurityViolation(
                rule_id="SH-NET-001",
                severity=Severity.CRITICAL,
                reason="unauthorized_network_destination",
                shutdown_required=True,
            )

        return None


security_policy = SecurityPolicy()
