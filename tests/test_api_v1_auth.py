from datetime import timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    get_db_session,
)
from app.api.v1.router import router
from app.models.user_session import UserSession
from app.services.auth import (
    SESSION_IDLE_TIMEOUT,
    create_user,
    utcnow,
)
from app.services.login_rate_limiter import (
    LOGIN_PRINCIPAL_MAX_FAILURES,
    login_rate_limiter,
)


PASSWORD = "correct-horse-battery-staple"


def build_client(
    db_session: Session,
) -> TestClient:
    login_rate_limiter.reset()

    app = FastAPI()
    app.include_router(router)

    def override_db():
        yield db_session

    app.dependency_overrides[
        get_db_session
    ] = override_db

    return TestClient(
        app,
        base_url="https://testserver",
    )


def login(
    client: TestClient,
    *,
    username: str = "admin",
    password: str = PASSWORD,
):
    return client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )


def csrf_header(
    client: TestClient,
) -> dict[str, str]:
    return {
        "X-CSRF-Token": client.cookies.get(
            "__Host-sherlock_csrf"
        )
    }


def test_no_public_register_endpoint(
    db_session: Session,
):
    client = build_client(
        db_session
    )

    response = client.post(
        "/api/v1/auth/register",
        json={},
    )

    assert response.status_code == 404


def test_me_requires_authentication(
    db_session: Session,
):
    client = build_client(
        db_session
    )

    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_login_sets_host_secure_session_and_csrf_cookies(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(
        db_session
    )

    response = login(client)

    assert response.status_code == 200
    assert (
        response.json()["user"]["username"]
        == "admin"
    )

    set_cookie = response.headers.get_list(
        "set-cookie"
    )

    assert any(
        "__Host-sherlock_session="
        in header
        and "HttpOnly" in header
        and "Secure" in header
        and "SameSite=strict" in header
        and "Path=/" in header
        for header in set_cookie
    )

    assert any(
        "__Host-sherlock_csrf="
        in header
        and "Secure" in header
        and "SameSite=strict" in header
        and "Path=/" in header
        and "HttpOnly" not in header
        for header in set_cookie
    )

    assert (
        response.headers["cache-control"]
        == "no-store"
    )


def test_authenticated_me(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(
        db_session
    )

    assert login(
        client
    ).status_code == 200

    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.headers["cache-control"] == "no-store"


def test_unknown_user_returns_generic_401(
    db_session: Session,
):
    client = build_client(
        db_session
    )

    response = login(
        client,
        username="does-not-exist",
        password="some-invalid-password",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


def test_invalid_password_is_rejected(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(
        db_session
    )

    response = login(
        client,
        password="wrong-password",
    )

    assert response.status_code == 401


def test_login_rate_limit_backoff_after_repeated_failures(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(
        db_session
    )

    for _ in range(
        LOGIN_PRINCIPAL_MAX_FAILURES
    ):
        response = login(
            client,
            password="wrong-password",
        )
        assert response.status_code == 401

    response = login(client)

    assert response.status_code == 429
    assert int(
        response.headers["retry-after"]
    ) >= 1
    assert (
        response.json()["detail"]
        == "Too many login attempts."
    )


def test_rate_limit_does_not_disclose_unknown_user(
    db_session: Session,
):
    client = build_client(
        db_session
    )

    for _ in range(
        LOGIN_PRINCIPAL_MAX_FAILURES
    ):
        response = login(
            client,
            username="not-a-user",
            password="wrong-password",
        )
        assert response.status_code == 401

    response = login(
        client,
        username="not-a-user",
        password="wrong-password",
    )

    assert response.status_code == 429


def test_disabled_user_does_not_disclose_account_state(
    db_session: Session,
):
    user = create_user(
        db_session,
        username="disabled",
        password=PASSWORD,
        role="user",
    )
    user.is_active = False
    db_session.commit()

    client = build_client(
        db_session
    )

    response = login(
        client,
        username="disabled",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


def test_logout_requires_csrf(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(
        db_session
    )
    assert login(client).status_code == 200

    response = client.post(
        "/api/v1/auth/logout"
    )

    assert response.status_code == 403


def test_logout_with_csrf_revokes_session(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(
        db_session
    )
    assert login(client).status_code == 200

    response = client.post(
        "/api/v1/auth/logout",
        headers=csrf_header(client),
    )

    assert response.status_code == 204

    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_logout_all_revokes_every_session_for_user(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client_a = build_client(db_session)
    client_b = build_client(db_session)

    assert login(client_a).status_code == 200
    assert login(client_b).status_code == 200

    response = client_a.post(
        "/api/v1/auth/logout-all",
        headers=csrf_header(client_a),
    )

    assert response.status_code == 204
    assert client_a.get(
        "/api/v1/auth/me"
    ).status_code == 401
    assert client_b.get(
        "/api/v1/auth/me"
    ).status_code == 401


def test_change_password_revokes_all_sessions(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(db_session)

    assert login(client).status_code == 200

    response = client.post(
        "/api/v1/auth/change-password",
        headers=csrf_header(client),
        json={
            "current_password": PASSWORD,
            "new_password": "new-correct-horse-battery-staple",
        },
    )

    assert response.status_code == 204
    assert client.get(
        "/api/v1/auth/me"
    ).status_code == 401

    old_login = login(client)
    assert old_login.status_code == 401

    new_login = login(
        client,
        password="new-correct-horse-battery-staple",
    )
    assert new_login.status_code == 200


def test_change_password_requires_current_password(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(db_session)
    assert login(client).status_code == 200

    response = client.post(
        "/api/v1/auth/change-password",
        headers=csrf_header(client),
        json={
            "current_password": "wrong-password",
            "new_password": "new-correct-horse-battery-staple",
        },
    )

    assert response.status_code == 401


def test_idle_session_is_rejected(
    db_session: Session,
):
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    client = build_client(db_session)
    assert login(client).status_code == 200

    user_session = db_session.scalar(
        select(UserSession)
    )

    user_session.last_seen_at = (
        utcnow()
        - SESSION_IDLE_TIMEOUT
        - timedelta(seconds=1)
    )
    db_session.commit()

    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_non_admin_is_forbidden_from_config(
    db_session: Session,
):
    create_user(
        db_session,
        username="member",
        password=PASSWORD,
        role="user",
    )

    client = build_client(
        db_session
    )

    assert login(
        client,
        username="member",
    ).status_code == 200

    response = client.get(
        "/api/v1/config/category-rules"
    )

    assert response.status_code == 403


def test_openapi_contains_session_security_scheme(
    db_session: Session,
):
    client = build_client(
        db_session
    )

    schema = client.get(
        "/openapi.json"
    ).json()

    schemes = (
        schema["components"]
        ["securitySchemes"]
    )

    assert "SherlockHomeSession" in schemes

    scheme = schemes[
        "SherlockHomeSession"
    ]

    assert scheme["type"] == "apiKey"
    assert scheme["in"] == "cookie"
    assert (
        scheme["name"]
        == "__Host-sherlock_session"
    )
