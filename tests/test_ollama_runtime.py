import httpx
import pytest

from app.agents.ollama_runtime import (
    OllamaClient,
    OllamaRuntimeError,
)
from app.core.security_enforcer import (
    SecurityPolicyError,
)


def test_ollama_client_calls_local_chat_endpoint():
    captured = {}

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        captured["url"] = str(
            request.url
        )
        captured["body"] = (
            request.read().decode()
        )

        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": (
                        '{"calls":[]}'
                    ),
                }
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as http_client:
        client = OllamaClient(
            host=(
                "http://127.0.0.1:11434"
            ),
            model="qwen3:14b",
            client=http_client,
        )

        result = client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "test",
                }
            ],
            json_mode=True,
        )

    assert (
        captured["url"]
        == (
            "http://127.0.0.1:11434"
            "/api/chat"
        )
    )
    assert result == '{"calls":[]}'


def test_ollama_client_rejects_unapproved_model():
    client = OllamaClient(
        host="http://127.0.0.1:11434",
        model="unapproved:model",
    )

    with pytest.raises(
        SecurityPolicyError
    ):
        client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "test",
                }
            ]
        )


def test_ollama_client_rejects_external_endpoint():
    client = OllamaClient(
        host="https://example.com",
        model="qwen3:14b",
    )

    with pytest.raises(
        SecurityPolicyError
    ):
        client.chat(
            messages=[
                {
                    "role": "user",
                    "content": "test",
                }
            ]
        )


def test_ollama_client_rejects_invalid_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "unexpected": True,
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as http_client:
        client = OllamaClient(
            host=(
                "http://127.0.0.1:11434"
            ),
            model="qwen3:14b",
            client=http_client,
        )

        with pytest.raises(
            OllamaRuntimeError,
            match="unexpected",
        ):
            client.chat(
                messages=[
                    {
                        "role": "user",
                        "content": "test",
                    }
                ]
            )


def test_ollama_client_rejects_empty_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "content": "   ",
                },
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as http_client:
        client = OllamaClient(
            host=(
                "http://127.0.0.1:11434"
            ),
            model="qwen3:14b",
            client=http_client,
        )

        with pytest.raises(
            OllamaRuntimeError,
            match="empty",
        ):
            client.chat(
                messages=[
                    {
                        "role": "user",
                        "content": "test",
                    }
                ]
            )
