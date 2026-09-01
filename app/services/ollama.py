import httpx

from urllib.parse import urlparse
from app.core.security import security_policy
from app.core.security_enforcer import enforce
from app.agents.system_prompt import SYSTEM_PROMPT
from app.core.config import settings
from app.services.project_context import load_project_context

class OllamaService:
    def __init__(self) -> None:
        self.base_url = settings.ollama_host
        self.model = settings.ollama_model
    async def chat(self, message: str) -> str:
        project_context = load_project_context()
        parsed_host = urlparse(self.base_url).hostname
        enforce(
            security_policy.validate_model(self.model)
        )
        enforce(
            security_policy.validate_destination(parsed_host)
        )
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
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
ollama_service = OllamaService()
