"""Assistant API router for AI chat and natural language UI commands."""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.assistant import AssistantChatRequest, AssistantResponse, AssistantMessage
from app.services.ai_agent import ai_agent_service
from app.dependencies import get_current_user

logger = logging.getLogger("assistant_router")

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

# In-memory session history cache per user (could also be stored in DB)
_session_history: Dict[str, List[Dict[str, Any]]] = {}


@router.post("/chat", response_model=AssistantResponse)
async def assistant_chat(
    request: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Main assistant interaction endpoint.
    Processes user instructions, triggers OpenAI tool calling or fallback parser,
    executes mail tools, emits WebSocket events to control UI, and returns structured response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    response = await ai_agent_service.chat(
        request=request,
        user_id=current_user.id,
        db=db
    )

    # Store in session history
    if current_user.id not in _session_history:
        _session_history[current_user.id] = []

    _session_history[current_user.id].append({
        "role": "user",
        "content": request.message,
        "tool_actions": None
    })
    _session_history[current_user.id].append({
        "role": "assistant",
        "content": response.message,
        "tool_actions": [ta.model_dump() for ta in response.tool_actions]
    })

    return response


@router.get("/history", response_model=List[Dict[str, Any]])
def get_assistant_history(current_user: User = Depends(get_current_user)):
    """Returns conversation history for current session."""
    return _session_history.get(current_user.id, [])


@router.delete("/history")
def clear_assistant_history(current_user: User = Depends(get_current_user)):
    """Clears conversation history for current session."""
    if current_user.id in _session_history:
        del _session_history[current_user.id]
    return {"message": "Assistant history cleared."}
