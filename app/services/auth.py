import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_session import UserSession


SESSION_TTL = timedelta(hours=8)
SESSION_IDLE_TIMEOUT = timedelta(minutes=30)
REVOKED_SESSION_RETENTION = timedelta(days=7)

_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

# Used only to make unknown-user login attempts perform Argon2 work.
_DUMMY_PASSWORD_HASH = _password_hasher.hash(
    "sherlock-home-dummy-password-not-a-real-credential"
)


@dataclass(frozen=True)
class CreatedSession:
    session_token: str
    csrf_token: str
    expires_at: datetime
    session: UserSession


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def hash_secret(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def validate_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError(
            "Password must contain at least 12 characters."
        )


def hash_password(password: str) -> str:
    validate_password(password)
    return _password_hasher.hash(password)


def verify_password(
    password_hash: str,
    password: str,
) -> bool:
    try:
        return _password_hasher.verify(
            password_hash,
            password,
        )
    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
    ):
        return False


def verify_unknown_user_password(
    password: str,
) -> None:
    """
    Spend comparable Argon2 work for unknown usernames.

    The result is deliberately ignored.
    """
    verify_password(
        _DUMMY_PASSWORD_HASH,
        password,
    )


def password_needs_rehash(
    password_hash: str,
) -> bool:
    try:
        return _password_hasher.check_needs_rehash(
            password_hash
        )
    except InvalidHashError:
        return True


def find_user_by_username(
    session: Session,
    username: str,
) -> User | None:
    return session.scalar(
        select(User).where(
            User.username
            == normalize_username(username)
        )
    )


def create_user(
    session: Session,
    *,
    username: str,
    password: str,
    role: str = "user",
    is_active: bool = True,
) -> User:
    normalized = normalize_username(username)

    if not normalized:
        raise ValueError(
            "Username must not be empty."
        )

    validate_password(password)

    if role not in {"admin", "user"}:
        raise ValueError(
            "Unsupported user role."
        )

    user = User(
        username=normalized,
        password_hash=hash_password(
            password
        ),
        role=role,
        is_active=is_active,
        failed_login_attempts=0,
        locked_until=None,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def create_initial_admin(
    session: Session,
    *,
    username: str,
    password: str,
) -> User:
    existing = session.scalar(
        select(User.id).limit(1)
    )

    if existing is not None:
        raise RuntimeError(
            "Admin bootstrap refused: a user already exists."
        )

    return create_user(
        session,
        username=username,
        password=password,
        role="admin",
        is_active=True,
    )


def record_login_failure(
    session: Session,
    user: User,
) -> None:
    """
    Keep a lightweight per-account failure counter for diagnostics.

    Authentication blocking is intentionally NOT driven by this counter.
    Blocking on username alone enables an attacker to lock out another user.
    Request blocking is handled by the source-aware LoginRateLimiter.
    """
    user.failed_login_attempts += 1
    user.locked_until = None
    session.commit()


def record_login_success(
    session: Session,
    user: User,
    *,
    password: str,
) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None

    if password_needs_rehash(
        user.password_hash
    ):
        user.password_hash = (
            hash_password(password)
        )

    session.commit()


def create_session(
    session: Session,
    *,
    user_id: int,
    ttl: timedelta = SESSION_TTL,
) -> CreatedSession:
    session_token = secrets.token_urlsafe(
        48
    )
    csrf_token = secrets.token_urlsafe(
        32
    )

    now = utcnow()
    expires_at = now + ttl

    db_session = UserSession(
        user_id=user_id,
        token_hash=hash_secret(
            session_token
        ),
        csrf_hash=hash_secret(
            csrf_token
        ),
        expires_at=expires_at,
        revoked_at=None,
        last_seen_at=now,
    )

    session.add(db_session)
    session.commit()
    session.refresh(db_session)

    return CreatedSession(
        session_token=session_token,
        csrf_token=csrf_token,
        expires_at=expires_at,
        session=db_session,
    )


def get_active_session(
    session: Session,
    *,
    raw_token: str,
    now: datetime | None = None,
) -> UserSession | None:
    now = now or utcnow()

    user_session = session.scalar(
        select(UserSession).where(
            UserSession.token_hash
            == hash_secret(raw_token)
        )
    )

    if user_session is None:
        return None

    if user_session.revoked_at is not None:
        return None

    if user_session.expires_at <= now:
        return None

    if (
        user_session.last_seen_at
        <= now - SESSION_IDLE_TIMEOUT
    ):
        return None

    user_session.last_seen_at = now
    session.commit()

    return user_session


def revoke_session(
    session: Session,
    user_session: UserSession,
    *,
    commit: bool = True,
) -> None:
    if user_session.revoked_at is None:
        user_session.revoked_at = utcnow()

    if commit:
        session.commit()


def revoke_all_user_sessions(
    session: Session,
    *,
    user_id: int,
) -> int:
    now = utcnow()

    result = session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    session.commit()

    return int(result.rowcount or 0)


def change_user_password(
    session: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> bool:
    if not verify_password(
        user.password_hash,
        current_password,
    ):
        return False

    validate_password(new_password)

    user.password_hash = hash_password(
        new_password
    )
    user.failed_login_attempts = 0
    user.locked_until = None

    now = utcnow()

    session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    session.commit()

    return True


def cleanup_sessions(
    session: Session,
    *,
    now: datetime | None = None,
    revoked_retention: timedelta = REVOKED_SESSION_RETENTION,
) -> int:
    now = now or utcnow()
    revoked_cutoff = now - revoked_retention

    result = session.execute(
        delete(UserSession).where(
            (
                UserSession.expires_at <= now
            )
            |
            (
                UserSession.revoked_at.is_not(None)
                & (
                    UserSession.revoked_at
                    <= revoked_cutoff
                )
            )
        )
    )

    session.commit()

    return int(result.rowcount or 0)


def verify_csrf(
    user_session: UserSession,
    raw_csrf_token: str,
) -> bool:
    expected = user_session.csrf_hash
    actual = hash_secret(
        raw_csrf_token
    )

    return secrets.compare_digest(
        expected,
        actual,
    )
