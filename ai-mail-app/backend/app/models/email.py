"""Email model definition."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Email(Base):
    """Email storage model representing received, sent, or draft emails."""
    __tablename__ = "emails"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_id = Column(String(128), nullable=True, index=True)
    thread_id = Column(String(128), nullable=True, index=True)
    sender = Column(String(255), nullable=False, index=True)
    sender_name = Column(String(255), nullable=True)
    recipients = Column(Text, nullable=False, default="[]")  # JSON encoded list of emails
    cc = Column(Text, nullable=True, default="[]")          # JSON encoded list
    bcc = Column(Text, nullable=True, default="[]")         # JSON encoded list
    subject = Column(String(512), nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    snippet = Column(String(512), nullable=True)
    is_read = Column(Boolean, default=False, index=True, nullable=False)
    is_starred = Column(Boolean, default=False, index=True, nullable=False)
    is_sent = Column(Boolean, default=False, index=True, nullable=False)
    labels = Column(Text, default='["INBOX"]', nullable=False) # JSON encoded list e.g. ["INBOX", "IMPORTANT"]
    received_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="emails")
