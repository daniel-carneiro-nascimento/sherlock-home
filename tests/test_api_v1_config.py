from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db_session
from app.api.v1.router import router
from app.services.auth import create_user


PASSWORD = "correct-horse-battery-staple"


def build_admin_client(
    db_session: Session,
) -> TestClient:
    create_user(
        db_session,
        username="admin",
        password=PASSWORD,
        role="admin",
    )

    app = FastAPI()
    app.include_router(router)

    def override_db():
        yield db_session

    app.dependency_overrides[
        get_db_session
    ] = override_db

    client = TestClient(
        app,
        base_url="https://testserver",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": PASSWORD,
        },
    )

    assert response.status_code == 200

    return client


def csrf_headers(
    client: TestClient,
) -> dict[str, str]:
    return {
        "X-CSRF-Token": (
            client.cookies.get(
                "__Host-sherlock_csrf"
            )
        )
    }


def test_category_rule_crud(
    db_session: Session,
):
    client = build_admin_client(
        db_session
    )

    create = client.post(
        "/api/v1/config/category-rules",
        headers=csrf_headers(client),
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": r"\bSYNTHETIC CINEMA\b",
            "priority": 5,
            "enabled": True,
        },
    )

    assert create.status_code == 201
    assert "id" not in create.json()
    assert create.json()["public_id"].startswith("cr_")

    rule_id = create.json()["public_id"]

    listing = client.get(
        "/api/v1/config/category-rules"
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["public_id"] == rule_id
    assert "id" not in listing.json()[0]

    update = client.put(
        f"/api/v1/config/category-rules/{rule_id}",
        headers=csrf_headers(client),
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": r"\bSYNTHETIC THEATER\b",
            "priority": 5,
            "enabled": True,
        },
    )

    assert update.status_code == 200
    assert update.json()["public_id"] == rule_id

    disable = client.patch(
        f"/api/v1/config/category-rules/{rule_id}/enabled",
        headers=csrf_headers(client),
        json={"enabled": False},
    )

    assert disable.status_code == 200
    assert disable.json()["enabled"] is False

    delete = client.delete(
        f"/api/v1/config/category-rules/{rule_id}",
        headers=csrf_headers(client),
    )

    assert delete.status_code == 204

    missing = client.get(
        f"/api/v1/config/category-rules/{rule_id}"
    )

    assert missing.status_code == 404


def test_category_rule_integer_id_is_not_an_api_identifier(
    db_session: Session,
):
    client = build_admin_client(db_session)

    response = client.get(
        "/api/v1/config/category-rules/1"
    )

    assert response.status_code == 404


def test_category_rule_invalid_regex_is_422(
    db_session: Session,
):
    client = build_admin_client(db_session)

    response = client.post(
        "/api/v1/config/category-rules",
        headers=csrf_headers(client),
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": "[",
            "priority": 5,
            "enabled": True,
        },
    )

    assert response.status_code == 422


def test_category_rule_priority_conflict_is_409(
    db_session: Session,
):
    client = build_admin_client(db_session)

    payload = {
        "category": "leisure",
        "field": "merchant",
        "pattern": "ONE",
        "priority": 5,
        "enabled": True,
    }

    first = client.post(
        "/api/v1/config/category-rules",
        headers=csrf_headers(client),
        json=payload,
    )

    assert first.status_code == 201

    payload["pattern"] = "TWO"

    second = client.post(
        "/api/v1/config/category-rules",
        headers=csrf_headers(client),
        json=payload,
    )

    assert second.status_code == 409


def test_mutating_config_requires_csrf(
    db_session: Session,
):
    client = build_admin_client(db_session)

    response = client.post(
        "/api/v1/config/category-rules",
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": "TEST",
            "priority": 5,
            "enabled": True,
        },
    )

    assert response.status_code == 403


def test_merchant_alias_crud(
    db_session: Session,
):
    client = build_admin_client(db_session)

    create = client.post(
        "/api/v1/config/merchant-aliases",
        headers=csrf_headers(client),
        json={
            "canonical_name": "Synthetic Market",
            "pattern": (
                r"^SYNTHETIC MARKET"
                r"(?:\s+\*\d+)?$"
            ),
            "priority": 10,
            "enabled": True,
        },
    )

    assert create.status_code == 201
    assert "id" not in create.json()
    assert create.json()["public_id"].startswith("ma_")
    assert (
        create.json()["canonical_name"]
        == "SYNTHETIC MARKET"
    )

    alias_id = create.json()["public_id"]

    listing = client.get(
        "/api/v1/config/merchant-aliases"
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["public_id"] == alias_id
    assert "id" not in listing.json()[0]

    disable = client.patch(
        f"/api/v1/config/merchant-aliases/{alias_id}/enabled",
        headers=csrf_headers(client),
        json={"enabled": False},
    )

    assert disable.status_code == 200
    assert disable.json()["enabled"] is False

    delete = client.delete(
        f"/api/v1/config/merchant-aliases/{alias_id}",
        headers=csrf_headers(client),
    )

    assert delete.status_code == 204


def test_merchant_alias_integer_id_is_not_an_api_identifier(
    db_session: Session,
):
    client = build_admin_client(db_session)

    response = client.get(
        "/api/v1/config/merchant-aliases/1"
    )

    assert response.status_code == 404


def test_merchant_alias_invalid_regex_is_422(
    db_session: Session,
):
    client = build_admin_client(db_session)

    response = client.post(
        "/api/v1/config/merchant-aliases",
        headers=csrf_headers(client),
        json={
            "canonical_name": "TEST",
            "pattern": "[",
            "priority": 10,
            "enabled": True,
        },
    )

    assert response.status_code == 422
