"""OAuthToken model definition."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class OAuthToken(Base):
    """Google OAuth tokens and credentials storage model."""
    __tablename__ = "oauth_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_uri = Column(String(255), default="https://oauth2.googleapis.com/token", nullable=False)
    client_id = Column(String(255), nullable=True)
    client_secret = Column(String(255), nullable=True)
    scopes = Column(Text, nullable=True)  # JSON or comma-separated scopes
    expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="oauth_token")
