"""Email business logic and database querying service."""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import Session

from app.models.email import Email
from app.models.user import User
from app.schemas.email import EmailCreate, EmailResponse
from app.services.gmail_service import gmail_service
from app.websocket.manager import ws_manager

logger = logging.getLogger("email_service")


class EmailService:
    """Handles email querying, creation, updating, and synchronizing with Gmail."""

    def get_emails(
        self,
        db: Session,
        user_id: str,
        folder: str = "inbox",
        query: Optional[str] = None,
        sender: Optional[str] = None,
        is_read: Optional[bool] = None,
        is_starred: Optional[bool] = None,
        days_ago: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Email], int]:
        """Queries emails for a user with comprehensive filtering and pagination."""
        q = db.query(Email).filter(Email.user_id == user_id)

        # Folder filtering
        folder_lower = folder.lower()
        if folder_lower == "inbox":
            q = q.filter(Email.is_sent == False)
        elif folder_lower == "sent":
            q = q.filter(Email.is_sent == True)
        elif folder_lower == "starred":
            q = q.filter(Email.is_starred == True)

        # Sender filter
        if sender:
            q = q.filter(
                or_(
                    Email.sender.ilike(f"%{sender}%"),
                    Email.sender_name.ilike(f"%{sender}%")
                )
            )

        # Keyword / search query filter (matches subject, body, snippet, sender)
        if query:
            q = q.filter(
                or_(
                    Email.subject.ilike(f"%{query}%"),
                    Email.body.ilike(f"%{query}%"),
                    Email.snippet.ilike(f"%{query}%"),
                    Email.sender.ilike(f"%{query}%"),
                    Email.sender_name.ilike(f"%{query}%"),
                    Email.recipients.ilike(f"%{query}%")
                )
            )

        # Read / Unread filter
        if is_read is not None:
            q = q.filter(Email.is_read == is_read)

        # Starred filter
        if is_starred is not None:
            q = q.filter(Email.is_starred == is_starred)

        # Date range filter (e.g. emails from last N days)
        if isinstance(days_ago, int) and days_ago > 0:
            cutoff = datetime.utcnow() - timedelta(days=days_ago)
            q = q.filter(Email.received_at >= cutoff)

        total = q.count()
        offset = (page - 1) * page_size
        items = q.order_by(desc(Email.received_at)).offset(offset).limit(page_size).all()

        return items, total

    def get_email_by_id(self, db: Session, user_id: str, email_id: str) -> Optional[Email]:
        """Fetches a specific email by ID belonging to user."""
        return db.query(Email).filter(
            Email.id == email_id,
            Email.user_id == user_id
        ).first()

    def mark_as_read(self, db: Session, user_id: str, email_id: str, is_read: bool = True) -> Optional[Email]:
        """Updates read status of an email and modifies Gmail labels if applicable."""
        email_obj = self.get_email_by_id(db, user_id, email_id)
        if not email_obj:
            return None

        email_obj.is_read = is_read
        email_obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(email_obj)

        # Synchronize with Gmail if gmail_id exists
        if email_obj.gmail_id:
            try:
                if is_read:
                    gmail_service.modify_message(user_id, db, email_obj.gmail_id, remove_labels=["UNREAD"])
                else:
                    gmail_service.modify_message(user_id, db, email_obj.gmail_id, add_labels=["UNREAD"])
            except Exception as e:
                logger.warning(f"Failed to sync read status to Gmail: {e}")

        return email_obj

    def toggle_star(self, db: Session, user_id: str, email_id: str, is_starred: bool) -> Optional[Email]:
        """Toggles starred status on email."""
        email_obj = self.get_email_by_id(db, user_id, email_id)
        if not email_obj:
            return None

        email_obj.is_starred = is_starred
        email_obj.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(email_obj)

        if email_obj.gmail_id:
            try:
                if is_starred:
                    gmail_service.modify_message(user_id, db, email_obj.gmail_id, add_labels=["STARRED"])
                else:
                    gmail_service.modify_message(user_id, db, email_obj.gmail_id, remove_labels=["STARRED"])
            except Exception as e:
                logger.warning(f"Failed to sync star status to Gmail: {e}")

        return email_obj

    def delete_email(self, db: Session, user_id: str, email_id: str) -> bool:
        """Deletes or moves email to trash."""
        email_obj = self.get_email_by_id(db, user_id, email_id)
        if not email_obj:
            return False

        if email_obj.gmail_id:
            try:
                gmail_service.modify_message(user_id, db, email_obj.gmail_id, add_labels=["TRASH"])
            except Exception as e:
                logger.warning(f"Failed to trash email in Gmail: {e}")

        db.delete(email_obj)
        db.commit()
        return True

    async def create_and_send_email(
        self,
        db: Session,
        user_id: str,
        email_data: EmailCreate
    ) -> Email:
        """
        Sends email via Gmail API if authenticated, creates local record, and notifies WebSocket clients.
        """
        user = db.query(User).filter(User.id == user_id).first()
        sender_email = user.email if user else "me@example.com"
        sender_name = user.name if user else "Me"

        gmail_id = None
        thread_id = email_data.thread_id

        # Attempt to send via real Gmail API
        try:
            gmail_res = gmail_service.send_message(
                user_id=user_id,
                db=db,
                to=email_data.to,
                subject=email_data.subject,
                body=email_data.body,
                cc=email_data.cc,
                bcc=email_data.bcc,
                thread_id=thread_id,
                in_reply_to=email_data.reply_to_id
            )
            if gmail_res:
                gmail_id = gmail_res.get("id")
                thread_id = gmail_res.get("threadId") or thread_id
        except Exception as e:
            logger.error(f"Gmail send encountered an error, recording in database: {e}")

        # Create record in database
        now = datetime.utcnow()
        new_email = Email(
            user_id=user_id,
            gmail_id=gmail_id,
            thread_id=thread_id or f"thread_{int(now.timestamp())}",
            sender=sender_email,
            sender_name=sender_name,
            recipients=json.dumps(email_data.to),
            cc=json.dumps(email_data.cc or []),
            bcc=json.dumps(email_data.bcc or []),
            subject=email_data.subject,
            body=email_data.body,
            snippet=email_data.body[:120].replace("\n", " ") if email_data.body else "",
            is_read=True,
            is_starred=False,
            is_sent=True,
            labels=json.dumps(["SENT"]),
            received_at=now,
        )
        db.add(new_email)
        db.commit()
        db.refresh(new_email)

        # Notify active WebSocket clients
        email_dict = EmailResponse.model_validate(new_email).model_dump(mode="json")
        await ws_manager.emit_email_sent(email_dict, user_id)

        return new_email

    async def reply_to_email(
        self,
        db: Session,
        user_id: str,
        email_id: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Email:
        """Replies to an existing email thread."""
        orig = self.get_email_by_id(db, user_id, email_id)
        if not orig:
            raise ValueError(f"Email with ID {email_id} not found.")

        # Determine reply subject
        subject = orig.subject
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        # Reply goes to original sender
        to_recipients = [orig.sender]

        email_create = EmailCreate(
            to=to_recipients,
            cc=cc or [],
            bcc=bcc or [],
            subject=subject,
            body=body,
            thread_id=orig.thread_id,
            reply_to_id=orig.gmail_id or orig.id
        )

        return await self.create_and_send_email(db, user_id, email_create)

    def seed_initial_emails(self, db: Session, user_id: str):
        """Populates rich seed emails if the user has no existing emails."""
        existing_count = db.query(Email).filter(Email.user_id == user_id).count()
        if existing_count > 0:
            return

        now = datetime.utcnow()
        demo_emails = [
            {
                "sender": "david.miller@techcorp.io",
                "sender_name": "David Miller",
                "recipients": ["user@example.com"],
                "subject": "Project Roadmap & Q4 Milestones",
                "body": (
                    "Hi team,\n\nI've finalized the Q4 engineering roadmap. Here are the key priorities:\n"
                    "1. Real-time AI Assistant UI integrations\n"
                    "2. Low-latency WebSocket synchronization pipeline\n"
                    "3. Modern responsive mail interface with dark mode\n\n"
                    "Let me know if you have questions or want to review the timeline during our sync tomorrow.\n\n"
                    "Best regards,\nDavid"
                ),
                "snippet": "I've finalized the Q4 engineering roadmap. Here are the key priorities...",
                "is_read": False,
                "is_starred": True,
                "is_sent": False,
                "labels": ["INBOX", "IMPORTANT"],
                "received_at": now - timedelta(hours=2),
                "thread_id": "thread_david_roadmap"
            },
            {
                "sender": "sarah.jenkins@designstudio.co",
                "sender_name": "Sarah Jenkins",
                "recipients": ["user@example.com"],
                "subject": "Design Review: New Glassmorphism Mail UI",
                "body": (
                    "Hey there,\n\nAttached are the updated Figma mockups for the new mail client.\n"
                    "We've refined the dark mode color palette, enhanced keyboard focus states, "
                    "and smoothed the AI typing animations in the compose form.\n\n"
                    "Let's review at 3:00 PM.\n\nCheers,\nSarah"
                ),
                "snippet": "Attached are the updated Figma mockups for the new mail client...",
                "is_read": False,
                "is_starred": False,
                "is_sent": False,
                "labels": ["INBOX"],
                "received_at": now - timedelta(days=1, hours=4),
                "thread_id": "thread_sarah_design"
            },
            {
                "sender": "alex.chen@cloudscale.net",
                "sender_name": "Alex Chen",
                "recipients": ["user@example.com"],
                "subject": "Database Migration & Backup Completed",
                "body": (
                    "Hello,\n\nThe scheduled database maintenance and index optimization completed with zero downtime.\n"
                    "Query latencies have dropped by ~38% across the board.\n\n"
                    "Thanks,\nAlex Chen\nDevOps Lead"
                ),
                "snippet": "The scheduled database maintenance and index optimization completed with zero downtime...",
                "is_read": True,
                "is_starred": False,
                "is_sent": False,
                "labels": ["INBOX"],
                "received_at": now - timedelta(days=3),
                "thread_id": "thread_alex_db"
            },
            {
                "sender": "john.doe@partnercorp.com",
                "sender_name": "John Doe",
                "recipients": ["user@example.com"],
                "subject": "Meeting Tomorrow at 3pm",
                "body": (
                    "Hi,\n\nFollowing up on our discussion last Friday. Are we still on track to meet tomorrow at 3pm?\n"
                    "Looking forward to seeing the product demo.\n\nRegards,\nJohn Doe"
                ),
                "snippet": "Following up on our discussion last Friday. Are we still on track to meet tomorrow at 3pm?...",
                "is_read": True,
                "is_starred": True,
                "is_sent": False,
                "labels": ["INBOX"],
                "received_at": now - timedelta(days=5),
                "thread_id": "thread_john_meeting"
            },
            {
                "sender": "david.miller@techcorp.io",
                "sender_name": "David Miller",
                "recipients": ["user@example.com"],
                "subject": "Q3 Performance & Team Recognition",
                "body": (
                    "Hey all,\n\nGreat work closing out Q3! Special shoutout to everyone involved in the automated mail assistant release.\n"
                    "Coffee and pastries on me Friday morning!\n\nDavid"
                ),
                "snippet": "Great work closing out Q3! Special shoutout to everyone involved...",
                "is_read": True,
                "is_starred": False,
                "is_sent": False,
                "labels": ["INBOX"],
                "received_at": now - timedelta(days=8),
                "thread_id": "thread_david_q3"
            },
            {
                "sender": "emily.watson@financeops.org",
                "sender_name": "Emily Watson",
                "recipients": ["user@example.com"],
                "subject": "Monthly Expense Reports - Action Required",
                "body": (
                    "Hi,\n\nPlease remember to submit all pending travel and software expense receipts by Friday EOD.\n"
                    "Let me know if you run into any portal issues.\n\nBest,\nEmily"
                ),
                "snippet": "Please remember to submit all pending travel and software expense receipts...",
                "is_read": True,
                "is_starred": False,
                "is_sent": False,
                "labels": ["INBOX"],
                "received_at": now - timedelta(days=9),
                "thread_id": "thread_emily_finance"
            },
            {
                "sender": "security-alerts@techcorp.io",
                "sender_name": "TechCorp Security",
                "recipients": ["user@example.com"],
                "subject": "Security Notice: 2FA Device Verification",
                "body": (
                    "Your account security check was verified successfully.\n"
                    "If this was not you, please immediately reset your password.\n\nTechCorp Infosec Team"
                ),
                "snippet": "Your account security check was verified successfully...",
                "is_read": True,
                "is_starred": False,
                "is_sent": False,
                "labels": ["INBOX"],
                "received_at": now - timedelta(days=14),
                "thread_id": "thread_security"
            },
            {
                "sender": "user@example.com",
                "sender_name": "Me",
                "recipients": ["client@enterprise.com"],
                "subject": "Proposal: Enterprise Cloud Architecture",
                "body": "Hi Robert,\n\nPlease find our enterprise architecture proposal attached.\nBest regards,\nDemo User",
                "snippet": "Please find our enterprise architecture proposal attached...",
                "is_read": True,
                "is_starred": False,
                "is_sent": True,
                "labels": ["SENT"],
                "received_at": now - timedelta(days=2),
                "thread_id": "thread_proposal"
            }
        ]

        for item in demo_emails:
            em = Email(
                user_id=user_id,
                gmail_id=None,
                thread_id=item["thread_id"],
                sender=item["sender"],
                sender_name=item["sender_name"],
                recipients=json.dumps(item["recipients"]),
                cc=json.dumps([]),
                bcc=json.dumps([]),
                subject=item["subject"],
                body=item["body"],
                snippet=item["snippet"],
                is_read=item["is_read"],
                is_starred=item["is_starred"],
                is_sent=item["is_sent"],
                labels=json.dumps(item["labels"]),
                received_at=item["received_at"],
            )
            db.add(em)

        db.commit()
        logger.info(f"Seeded {len(demo_emails)} emails for user {user_id}")


email_service = EmailService()
