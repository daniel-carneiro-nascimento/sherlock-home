import logging

from sqlalchemy.orm import Session

from app.models.api_audit_event import ApiAuditEvent


logger = logging.getLogger(
    "sherlock_home.config_audit"
)


def record_config_change(
    session: Session,
    *,
    actor_user_id: int,
    resource_type: str,
    action: str,
    resource_public_id: str,
) -> ApiAuditEvent:
    """
    Add a sanitized configuration audit event to the current transaction.

    This function deliberately does not commit. The caller commits the
    configuration mutation and its audit event atomically.
    """
    event = ApiAuditEvent(
        actor_user_id=actor_user_id,
        event_type="config_change",
        resource_type=resource_type,
        action=action,
        resource_public_id=resource_public_id,
        outcome="success",
    )

    session.add(event)
    session.flush()
    session.refresh(event)

    logger.info(
        "CONFIG_AUDIT event_id=%s actor_user_id=%s "
        "resource_type=%s action=%s resource_public_id=%s outcome=success",
        event.public_id,
        actor_user_id,
        resource_type,
        action,
        resource_public_id,
    )

    return event
