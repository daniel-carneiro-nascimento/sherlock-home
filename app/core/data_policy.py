from enum import Enum

from app.core.security import SecurityViolation, Severity


class DataClassification(str, Enum):
    PUBLIC = "public"
    PROJECT = "project"
    PERSONAL = "personal"
    FINANCIAL = "financial"
    SECRET = "secret"


# Explicit data-processing permissions.
#
# Key:
#   (scheme, host, port)
#
# Value:
#   data classifications that endpoint may receive.
APPROVED_DATA_DESTINATIONS = {
    ("http", "127.0.0.1", 11434): {
        DataClassification.PUBLIC,
        DataClassification.PROJECT,
        DataClassification.PERSONAL,
        DataClassification.FINANCIAL,
    },
    ("http", "localhost", 11434): {
        DataClassification.PUBLIC,
        DataClassification.PROJECT,
        DataClassification.PERSONAL,
        DataClassification.FINANCIAL,
    },
}


def validate_data_egress(
    scheme: str,
    host: str,
    port: int | None,
    classification: DataClassification,
) -> SecurityViolation | None:

    # Secrets must never enter LLM context,
    # even when inference is local.
    if classification == DataClassification.SECRET:
        return SecurityViolation(
            rule_id="SH-SECRET-001",
            severity=Severity.CRITICAL,
            reason="secret_data_not_allowed_in_llm_context",
            shutdown_required=False,
        )

    destination = (scheme, host, port)

    allowed_classes = APPROVED_DATA_DESTINATIONS.get(destination)

    if allowed_classes is None:
        return SecurityViolation(
            rule_id="SH-DATA-001",
            severity=Severity.CRITICAL,
            reason="protected_data_destination_not_approved",
            shutdown_required=False,
        )

    if classification not in allowed_classes:
        return SecurityViolation(
            rule_id="SH-DATA-001",
            severity=Severity.CRITICAL,
            reason="data_classification_not_allowed_for_destination",
            shutdown_required=False,
        )

    return None
