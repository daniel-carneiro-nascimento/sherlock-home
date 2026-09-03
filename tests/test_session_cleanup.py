from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_session import UserSession
from app.services.auth import (
    REVOKED_SESSION_RETENTION,
    cleanup_sessions,
    create_session,
    create_user,
    revoke_session,
    utcnow,
)


PASSWORD = "correct-horse-battery-staple"


def test_cleanup_removes_expired_sessions(
    db_session: Session,
):
    user = create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    created = create_session(
        db_session,
        user_id=user.id,
    )

    created.session.expires_at = (
        utcnow() - timedelta(seconds=1)
    )
    db_session.commit()

    deleted = cleanup_sessions(db_session)

    assert deleted == 1
    assert db_session.scalar(
        select(UserSession)
    ) is None


def test_cleanup_keeps_recent_revoked_sessions(
    db_session: Session,
):
    user = create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    created = create_session(
        db_session,
        user_id=user.id,
    )

    revoke_session(
        db_session,
        created.session,
    )

    deleted = cleanup_sessions(db_session)

    assert deleted == 0
    assert db_session.scalar(
        select(UserSession)
    ) is not None


def test_cleanup_removes_old_revoked_sessions(
    db_session: Session,
):
    user = create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    created = create_session(
        db_session,
        user_id=user.id,
    )

    created.session.revoked_at = (
        utcnow()
        - REVOKED_SESSION_RETENTION
        - timedelta(seconds=1)
    )
    db_session.commit()

    deleted = cleanup_sessions(db_session)

    assert deleted == 1
    assert db_session.scalar(
        select(UserSession)
    ) is None
