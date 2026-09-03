from dataclasses import dataclass

from fastapi import (
    Cookie,
    Depends,
    Header,
    HTTPException,
    Security,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.security import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    session_cookie_scheme,
)
from app.db.database import SessionLocal
from app.models.user import User
from app.models.user_session import UserSession
from app.services.auth import (
    get_active_session,
    verify_csrf,
)


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: UserSession


def get_db_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def require_auth_context(
    raw_session_token: str | None = Security(
        session_cookie_scheme
    ),
    db: Session = Depends(
        get_db_session
    ),
) -> AuthContext:
    if not raw_session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    user_session = get_active_session(
        db,
        raw_token=raw_session_token,
    )

    if user_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    user = db.get(
        User,
        user_session.user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session user.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is disabled.",
        )

    return AuthContext(
        user=user,
        session=user_session,
    )


def require_current_user(
    auth: AuthContext = Depends(
        require_auth_context
    ),
) -> User:
    return auth.user


def require_admin(
    auth: AuthContext = Depends(
        require_auth_context
    ),
) -> User:
    if auth.user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return auth.user


def require_csrf(
    auth: AuthContext = Depends(
        require_auth_context
    ),
    csrf_cookie: str | None = Cookie(
        default=None,
        alias=CSRF_COOKIE_NAME,
    ),
    csrf_header: str | None = Header(
        default=None,
        alias=CSRF_HEADER_NAME,
    ),
) -> None:
    if (
        not csrf_cookie
        or not csrf_header
        or csrf_cookie != csrf_header
        or not verify_csrf(
            auth.session,
            csrf_header,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed.",
        )
