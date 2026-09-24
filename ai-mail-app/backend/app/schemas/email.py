"""Email Pydantic schemas."""
import json
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EmailBase(BaseModel):
    """Base email schema."""
    subject: str = ""
    body: str = ""


class EmailCreate(EmailBase):
    """Schema for composing and sending an email."""
    to: List[str] = Field(..., description="List of recipient email addresses")
    cc: Optional[List[str]] = Field(default_factory=list, description="List of CC email addresses")
    bcc: Optional[List[str]] = Field(default_factory=list, description="List of BCC email addresses")
    thread_id: Optional[str] = None
    reply_to_id: Optional[str] = None


class ComposeForm(BaseModel):
    """Schema for compose form data."""
    to: List[str] = Field(default_factory=list)
    cc: Optional[List[str]] = Field(default_factory=list)
    bcc: Optional[List[str]] = Field(default_factory=list)
    subject: str = ""
    body: str = ""


class EmailUpdate(BaseModel):
    """Schema for updating email metadata."""
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    labels: Optional[List[str]] = None


class EmailReply(BaseModel):
    """Schema for replying to an email."""
    body: str
    cc: Optional[List[str]] = Field(default_factory=list)
    bcc: Optional[List[str]] = Field(default_factory=list)


class EmailResponse(BaseModel):
    """Schema for returning email details to frontend."""
    id: str
    user_id: str
    gmail_id: Optional[str] = None
    thread_id: Optional[str] = None
    sender: str
    sender_name: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    bcc: List[str] = Field(default_factory=list)
    subject: str
    body: str
    snippet: Optional[str] = None
    is_read: bool
    is_starred: bool
    is_sent: bool
    labels: List[str] = Field(default_factory=list)
    received_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("recipients", "cc", "bcc", "labels", mode="before")
    @classmethod
    def parse_json_lists(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [s.strip() for s in v.split(",") if s.strip()]
        elif isinstance(v, list):
            return v
        return []


class EmailListResponse(BaseModel):
    """Paginated email list response."""
    items: List[EmailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
