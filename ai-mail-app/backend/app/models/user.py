"""User model definition."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    oauth_token = relationship("OAuthToken", back_populates="user", uselist=False, cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="user", cascade="all, delete-orphan")
