from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.network_policy import validate_endpoint
from app.core.runtime_state import ensure_runtime_safe
from app.core.security import security_policy
from app.core.security_enforcer import enforce


class OllamaRuntimeError(RuntimeError):
    pass


@dataclass
class OllamaClient:
    host: str
    model: str
    timeout_seconds: float = 120.0
    client: httpx.Client | None = None

    def _validate_runtime(self) -> None:
        ensure_runtime_safe()

        enforce(
            security_policy.validate_model(
                self.model
            )
        )

        enforce(
            validate_endpoint(
                self.host
            )
        )

    def chat(
        self,
        *,
        messages: list[
            dict[str, str]
        ],
        json_mode: bool = False,
        temperature: float = 0.0,
    ) -> str:
        """
        Send a chat request only to the configured, policy-approved local
        Ollama runtime.

        The returned model text is still untrusted input. Callers must parse
        and validate it before using it to request deterministic operations.
        """
        self._validate_runtime()

        url = (
            self.host.rstrip("/")
            + "/api/chat"
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": (
                    temperature
                ),
            },
        }

        if json_mode:
            payload["format"] = "json"

        owned_client = (
            self.client is None
        )

        http_client = (
            self.client
            if self.client is not None
            else httpx.Client(
                timeout=self.timeout_seconds
            )
        )

        try:
            response = http_client.post(
                url,
                json=payload,
            )

            response.raise_for_status()

            body = response.json()
        except (
            httpx.HTTPError,
            ValueError,
        ) as exc:
            raise OllamaRuntimeError(
                "local Ollama request failed"
            ) from exc
        finally:
            if owned_client:
                http_client.close()

        try:
            content = body[
                "message"
            ][
                "content"
            ]
        except (
            KeyError,
            TypeError,
        ) as exc:
            raise OllamaRuntimeError(
                "unexpected Ollama response"
            ) from exc

        if not isinstance(
            content,
            str,
        ):
            raise OllamaRuntimeError(
                "unexpected Ollama response"
            )

        content = content.strip()

        if not content:
            raise OllamaRuntimeError(
                "empty Ollama response"
            )

        return content
