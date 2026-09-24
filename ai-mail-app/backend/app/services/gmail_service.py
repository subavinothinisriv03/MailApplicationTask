"""Gmail API client service for listing, fetching, sending, and modifying messages."""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.oauth_token import OAuthToken
from app.models.user import User
from app.models.email import Email
from app.utils.email_parser import parse_gmail_message, create_rfc2822_message

logger = logging.getLogger("gmail_service")


class GmailService:
    """Service wrapping Google Gmail REST API with automatic token refresh."""

    def get_credentials(self, user_id: str, db: Session) -> Optional[Credentials]:
        """Loads and refreshes Google OAuth credentials for a user."""
        token_record = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
        if not token_record or not token_record.access_token:
            return None

        # Check if it's a demo mock token
        if token_record.access_token.startswith("demo_mock"):
            return None

        scopes = json.loads(token_record.scopes) if token_record.scopes else []
        creds = Credentials(
            token=token_record.access_token,
            refresh_token=token_record.refresh_token,
            token_uri=token_record.token_uri,
            client_id=token_record.client_id or settings.GOOGLE_CLIENT_ID,
            client_secret=token_record.client_secret or settings.GOOGLE_CLIENT_SECRET,
            scopes=scopes,
        )

        # Refresh token if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                token_record.access_token = creds.token
                token_record.expiry = creds.expiry
                db.commit()
                logger.info(f"Refreshed access token for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to refresh access token for user {user_id}: {e}")
                return None

        return creds

    def get_gmail_service(self, user_id: str, db: Session):
        """Constructs an authenticated Google Gmail API service client."""
        creds = self.get_credentials(user_id, db)
        if not creds:
            return None
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def list_messages(
        self,
        user_id: str,
        db: Session,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        max_results: int = 20,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lists message summaries from Gmail API.
        Returns {'messages': [{'id': '...'}], 'nextPageToken': '...'}
        """
        service = self.get_gmail_service(user_id, db)
        if not service:
            return {"messages": [], "nextPageToken": None}

        try:
            params: Dict[str, Any] = {
                "userId": "me",
                "maxResults": min(max_results, 50),
            }
            if query:
                params["q"] = query
            if label_ids:
                params["labelIds"] = label_ids
            if page_token:
                params["pageToken"] = page_token

            result = service.users().messages().list(**params).execute()
            return {
                "messages": result.get("messages", []),
                "nextPageToken": result.get("nextPageToken")
            }
        except HttpError as error:
            logger.error(f"Gmail API list_messages error: {error}")
            return {"messages": [], "nextPageToken": None}

    def get_message(self, user_id: str, db: Session, message_id: str) -> Optional[Dict[str, Any]]:
        """Fetches full email message from Gmail API by ID and parses into standard dict."""
        service = self.get_gmail_service(user_id, db)
        if not service:
            return None

        try:
            raw_msg = service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()
            return parse_gmail_message(raw_msg)
        except HttpError as error:
            logger.error(f"Gmail API get_message error: {error}")
            return None

    def send_message(
        self,
        user_id: str,
        db: Session,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sends an email using Gmail API users.messages.send.
        Falls back to None if credentials not available.
        """
        service = self.get_gmail_service(user_id, db)
        if not service:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        sender_email = user.email if user else "me"

        raw_payload = create_rfc2822_message(
            sender=sender_email,
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            thread_id=thread_id,
            in_reply_to=in_reply_to
        )

        try:
            sent_msg = service.users().messages().send(
                userId="me",
                body=raw_payload
            ).execute()
            logger.info(f"Email successfully sent via Gmail API: {sent_msg.get('id')}")
            return sent_msg
        except HttpError as error:
            logger.error(f"Gmail API send_message error: {error}")
            raise

    def modify_message(
        self,
        user_id: str,
        db: Session,
        message_id: str,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> bool:
        """Modifies labels (read, unread, star, trash) on a Gmail message."""
        service = self.get_gmail_service(user_id, db)
        if not service:
            return False

        body: Dict[str, Any] = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        try:
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body=body
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"Gmail API modify_message error: {error}")
            return False

    def search_messages(self, user_id: str, db: Session, query: str) -> List[Dict[str, Any]]:
        """Searches messages via Gmail search syntax (e.g. from:John, is:unread)."""
        list_result = self.list_messages(user_id=user_id, db=db, query=query, max_results=20)
        messages_meta = list_result.get("messages", [])
        detailed_messages = []
        for meta in messages_meta:
            detail = self.get_message(user_id=user_id, db=db, message_id=meta["id"])
            if detail:
                detailed_messages.append(detail)
        return detailed_messages


gmail_service = GmailService()
