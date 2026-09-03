from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db_session
from app.api.v1.router import router
from app.models.api_audit_event import ApiAuditEvent
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
        "X-CSRF-Token": client.cookies.get(
            "__Host-sherlock_csrf"
        )
    }


def audit_rows(
    db_session: Session,
) -> list[ApiAuditEvent]:
    return list(
        db_session.scalars(
            select(ApiAuditEvent).order_by(
                ApiAuditEvent.id
            )
        ).all()
    )


def test_category_rule_create_is_persistently_audited(
    db_session: Session,
):
    client = build_admin_client(db_session)

    response = client.post(
        "/api/v1/config/category-rules",
        headers=csrf_headers(client),
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": "SYNTHETIC AUDIT TEST",
            "priority": 5,
            "enabled": True,
        },
    )

    assert response.status_code == 201
    resource_id = response.json()["public_id"]

    rows = audit_rows(db_session)

    assert len(rows) == 1
    assert rows[0].public_id.startswith("ae_")
    assert rows[0].event_type == "config_change"
    assert rows[0].resource_type == "category_rule"
    assert rows[0].action == "create"
    assert rows[0].resource_public_id == resource_id
    assert rows[0].outcome == "success"


def test_category_rule_lifecycle_is_audited(
    db_session: Session,
):
    client = build_admin_client(db_session)
    headers = csrf_headers(client)

    create = client.post(
        "/api/v1/config/category-rules",
        headers=headers,
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": "SYNTHETIC ONE",
            "priority": 5,
            "enabled": True,
        },
    )
    resource_id = create.json()["public_id"]

    update = client.put(
        f"/api/v1/config/category-rules/{resource_id}",
        headers=headers,
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": "SYNTHETIC TWO",
            "priority": 5,
            "enabled": True,
        },
    )
    assert update.status_code == 200

    disable = client.patch(
        f"/api/v1/config/category-rules/{resource_id}/enabled",
        headers=headers,
        json={"enabled": False},
    )
    assert disable.status_code == 200

    delete = client.delete(
        f"/api/v1/config/category-rules/{resource_id}",
        headers=headers,
    )
    assert delete.status_code == 204

    rows = audit_rows(db_session)

    assert [
        row.action for row in rows
    ] == [
        "create",
        "update",
        "disable",
        "delete",
    ]

    assert all(
        row.resource_public_id == resource_id
        for row in rows
    )


def test_merchant_alias_lifecycle_is_audited(
    db_session: Session,
):
    client = build_admin_client(db_session)
    headers = csrf_headers(client)

    create = client.post(
        "/api/v1/config/merchant-aliases",
        headers=headers,
        json={
            "canonical_name": "Synthetic Audit Merchant",
            "pattern": "SYNTHETIC AUDIT MERCHANT",
            "priority": 10,
            "enabled": True,
        },
    )
    assert create.status_code == 201
    resource_id = create.json()["public_id"]

    delete = client.delete(
        f"/api/v1/config/merchant-aliases/{resource_id}",
        headers=headers,
    )
    assert delete.status_code == 204

    rows = audit_rows(db_session)

    assert [
        (row.resource_type, row.action)
        for row in rows
    ] == [
        ("merchant_alias", "create"),
        ("merchant_alias", "delete"),
    ]


def test_audit_does_not_store_rule_pattern_or_payload(
    db_session: Session,
):
    client = build_admin_client(db_session)

    secret_marker = "SYNTHETIC_PRIVATE_PATTERN"

    response = client.post(
        "/api/v1/config/category-rules",
        headers=csrf_headers(client),
        json={
            "category": "leisure",
            "field": "merchant",
            "pattern": secret_marker,
            "priority": 5,
            "enabled": True,
        },
    )
    assert response.status_code == 201

    row = audit_rows(db_session)[0]

    serialized = " ".join(
        [
            row.public_id,
            row.event_type,
            row.resource_type,
            row.action,
            row.resource_public_id,
            row.outcome,
        ]
    )

    assert secret_marker not in serialized
