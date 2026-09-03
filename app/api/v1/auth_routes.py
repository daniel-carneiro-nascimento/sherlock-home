from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    AuthContext,
    get_db_session,
    require_auth_context,
    require_csrf,
    require_current_user,
)
from app.api.v1.schemas.auth import (
    ChangePasswordRequest,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from app.api.v1.security import (
    CSRF_COOKIE_HTTPONLY,
    CSRF_COOKIE_NAME,
    CSRF_COOKIE_SAMESITE,
    CSRF_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_PATH,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
)
from app.models.user import User
from app.services.auth import (
    SESSION_TTL,
    change_user_password,
    create_session,
    find_user_by_username,
    record_login_failure,
    record_login_success,
    revoke_all_user_sessions,
    revoke_session,
    verify_password,
    verify_unknown_user_password,
)
from app.services.login_rate_limiter import (
    login_rate_limiter,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def _set_no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _client_source(
    request: Request,
) -> str:
    if request.client is None:
        return "unknown"

    return request.client.host


def _raise_rate_limited(
    retry_after: int,
) -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many login attempts.",
        headers={
            "Retry-After": str(
                retry_after
            )
        },
    )


def _set_auth_cookies(
    response: Response,
    *,
    session_token: str,
    csrf_token: str,
) -> None:
    max_age = int(
        SESSION_TTL.total_seconds()
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age,
        expires=max_age,
        path=SESSION_COOKIE_PATH,
        secure=SESSION_COOKIE_SECURE,
        httponly=SESSION_COOKIE_HTTPONLY,
        samesite=SESSION_COOKIE_SAMESITE,
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        expires=max_age,
        path=SESSION_COOKIE_PATH,
        secure=CSRF_COOKIE_SECURE,
        httponly=CSRF_COOKIE_HTTPONLY,
        samesite=CSRF_COOKIE_SAMESITE,
    )


def _clear_auth_cookies(
    response: Response,
) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        secure=SESSION_COOKIE_SECURE,
        httponly=SESSION_COOKIE_HTTPONLY,
        samesite=SESSION_COOKIE_SAMESITE,
    )

    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        secure=CSRF_COOKIE_SECURE,
        httponly=CSRF_COOKIE_HTTPONLY,
        samesite=CSRF_COOKIE_SAMESITE,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Invalid credentials.",
        },
        429: {
            "model": ErrorResponse,
            "description": (
                "Login rate limit/backoff active."
            ),
        },
    },
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(
        get_db_session
    ),
) -> LoginResponse:
    _set_no_store(response)

    source = _client_source(
        request
    )

    retry_after = (
        login_rate_limiter.check(
            source=source,
            username=payload.username,
        )
    )

    if retry_after:
        _raise_rate_limited(
            retry_after
        )

    user = find_user_by_username(
        db,
        payload.username,
    )

    if user is None:
        verify_unknown_user_password(
            payload.password
        )

        login_rate_limiter.record_failure(
            source=source,
            username=payload.username,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if not user.is_active:
        verify_password(
            user.password_hash,
            payload.password,
        )

        login_rate_limiter.record_failure(
            source=source,
            username=payload.username,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if not verify_password(
        user.password_hash,
        payload.password,
    ):
        record_login_failure(
            db,
            user,
        )

        login_rate_limiter.record_failure(
            source=source,
            username=payload.username,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    record_login_success(
        db,
        user,
        password=payload.password,
    )

    login_rate_limiter.record_success(
        source=source,
        username=payload.username,
    )

    created = create_session(
        db,
        user_id=user.id,
    )

    _set_auth_cookies(
        response,
        session_token=created.session_token,
        csrf_token=created.csrf_token,
    )

    return LoginResponse(
        user=UserResponse.model_validate(
            user
        ),
        expires_at=created.expires_at,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_csrf)
    ],
)
def logout(
    response: Response,
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
) -> Response:
    revoke_session(
        db,
        auth.session,
    )

    _clear_auth_cookies(response)
    _set_no_store(response)

    response.status_code = (
        status.HTTP_204_NO_CONTENT
    )

    return response


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_csrf)
    ],
)
def logout_all(
    response: Response,
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
) -> Response:
    revoke_all_user_sessions(
        db,
        user_id=auth.user.id,
    )

    _clear_auth_cookies(response)
    _set_no_store(response)

    response.status_code = (
        status.HTTP_204_NO_CONTENT
    )

    return response


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(require_csrf)
    ],
)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    auth: AuthContext = Depends(
        require_auth_context
    ),
    db: Session = Depends(
        get_db_session
    ),
) -> Response:
    try:
        changed = change_user_password(
            db,
            user=auth.user,
            current_password=(
                payload.current_password
            ),
            new_password=(
                payload.new_password
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if not changed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    _clear_auth_cookies(response)
    _set_no_store(response)

    response.status_code = (
        status.HTTP_204_NO_CONTENT
    )

    return response


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    response: Response,
    user: User = Depends(
        require_current_user
    ),
) -> UserResponse:
    _set_no_store(response)

    return UserResponse.model_validate(
        user
    )
