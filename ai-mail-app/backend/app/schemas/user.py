"""User Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user properties."""
    email: EmailStr
    name: str
    picture: Optional[str] = None


class UserCreate(UserBase):
    """Properties required on user creation."""
    pass


class UserUpdate(BaseModel):
    """Properties that can be updated on a user."""
    name: Optional[str] = None
    picture: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Authentication token response schema."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
