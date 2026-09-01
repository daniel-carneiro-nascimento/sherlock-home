from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ollama import ollama_service


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/health")
async def health():
    return {
        "status": "ok",
    }


@router.post("/chat")
async def chat(request: ChatRequest):
    response = await ollama_service.chat(request.message)

    return {
        "model": ollama_service.model,
        "response": response,
    }
