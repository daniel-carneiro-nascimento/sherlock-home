from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.router import router


EXPECTED_API_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/logout-all",
    "/api/v1/auth/change-password",
    "/api/v1/auth/me",
    "/api/v1/config/category-rules",
    "/api/v1/config/category-rules/{rule_id}",
    "/api/v1/config/category-rules/{rule_id}/enabled",
    "/api/v1/config/merchant-aliases",
    "/api/v1/config/merchant-aliases/{alias_id}",
    "/api/v1/config/merchant-aliases/{alias_id}/enabled",
}


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def test_api_v1_contract_contains_expected_paths():
    schema = build_app().openapi()

    assert EXPECTED_API_PATHS.issubset(
        set(schema["paths"])
    )


def test_api_v1_contract_has_no_public_registration():
    schema = build_app().openapi()

    assert (
        "/api/v1/auth/register"
        not in schema["paths"]
    )


def test_login_contract_documents_rate_limit():
    schema = build_app().openapi()

    responses = (
        schema["paths"]
        ["/api/v1/auth/login"]
        ["post"]
        ["responses"]
    )

    assert "401" in responses
    assert "429" in responses


def test_config_mutations_are_not_anonymous_in_contract():
    schema = build_app().openapi()

    protected_operations = [
        (
            "/api/v1/config/category-rules",
            "post",
        ),
        (
            "/api/v1/config/category-rules/{rule_id}",
            "put",
        ),
        (
            "/api/v1/config/category-rules/{rule_id}",
            "delete",
        ),
        (
            "/api/v1/config/merchant-aliases",
            "post",
        ),
        (
            "/api/v1/config/merchant-aliases/{alias_id}",
            "put",
        ),
        (
            "/api/v1/config/merchant-aliases/{alias_id}",
            "delete",
        ),
    ]

    for path, method in protected_operations:
        operation = (
            schema["paths"][path][method]
        )

        assert operation.get("security")
