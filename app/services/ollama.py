import httpx

from urllib.parse import urlparse
from app.agents.system_prompt import SYSTEM_PROMPT
from app.core.config import settings
from app.core.data_policy import (
    DataClassification,
    validate_data_egress,
)
from app.core.network_policy import validate_endpoint
from app.core.security import security_policy
from app.core.security_enforcer import enforce
from app.services.project_context import load_project_context
from app.core.secret_detector import detect_secret
from app.core.policy_bypass import detect_policy_bypass
from app.core.runtime_state import ensure_runtime_safe

class OllamaService:
    def __init__(self) -> None:
        self.base_url = settings.ollama_host
        self.model = settings.ollama_model

    async def chat(self, message: str) -> str:
        ensure_runtime_safe()

        # 1. Validate approved AI model
        enforce(
            security_policy.validate_model(self.model)
        )

        # 2. Validate approved network endpoint
        enforce(
            validate_endpoint(self.base_url)
        )

        # 3. Validate data egress policy
        parsed = urlparse(self.base_url)

        enforce(
            validate_data_egress(
                scheme=parsed.scheme,
                host=parsed.hostname or "",
                port=parsed.port,
                classification=DataClassification.PERSONAL,
            )
        )
        # 4. Detect Secrets
        enforce(
            detect_secret(message)
        )
        enforce(
            detect_secret(message)
        )
        enforce(
            detect_policy_bypass(message)
        )

        # 5. Load trusted local project context
        project_context = load_project_context()

        # 6. Build request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "system",
                    "content": (
                        "The following is trusted local project context. "
                        "Use it when answering questions about Sherlock Home.\n\n"
                        f"{project_context}"
                    ),
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            "stream": False,
        }

        # 7. Call approved local Ollama service
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )

            response.raise_for_status()

        data = response.json()

        return data["message"]["content"]


ollama_service = OllamaService()
