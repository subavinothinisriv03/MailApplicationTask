"""Assistant and Tool Calling Pydantic schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolAction(BaseModel):
    """Structured tool action produced during assistant execution."""
    type: str = "tool_action"
    tool: str = Field(..., description="Name of the tool executed, e.g. navigate_to_compose, fill_compose_form")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments supplied to the tool")
    result: Optional[Any] = Field(default=None, description="Result returned by the backend execution")


class AssistantMessage(BaseModel):
    """Message schema in the conversation transcript."""
    role: str = Field(..., description="Role: 'user', 'assistant', 'system', 'tool'")
    content: str = Field(..., description="Text content of the message")
    tool_actions: Optional[List[ToolAction]] = Field(default=None, description="Tools triggered in this turn")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AssistantChatRequest(BaseModel):
    """Request payload sent to POST /api/assistant/chat."""
    message: str = Field(..., description="User's natural language instruction or query")
    current_view: Optional[str] = Field(default="inbox", description="Active frontend view: inbox, sent, compose, email_detail")
    current_email_id: Optional[str] = Field(default=None, description="Currently opened or selected email ID")
    current_filters: Optional[Dict[str, Any]] = Field(default=None, description="Active search/filter terms on frontend")
    draft_state: Optional[Dict[str, Any]] = Field(default=None, description="Current content in compose form")


class AssistantResponse(BaseModel):
    """Response payload returned from POST /api/assistant/chat."""
    message: str = Field(..., description="Assistant's natural language explanation to the user")
    tool_actions: List[ToolAction] = Field(default_factory=list, description="Ordered list of tool actions for frontend execution")
    execution_context: Optional[Dict[str, Any]] = Field(default=None, description="Updated context for frontend state synchronization")
