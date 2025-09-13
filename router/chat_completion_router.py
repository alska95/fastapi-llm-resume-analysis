from fastapi import APIRouter

from service.chat_completion.chat_completion_service import get_chat_completion_response

router = APIRouter()


@router.get("/chat")
async def chat_completion(prompt: str) -> str:
    return await get_chat_completion_response(prompt);
