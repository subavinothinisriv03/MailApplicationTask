"""Email CRUD and management router."""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.email import (
    EmailCreate,
    EmailUpdate,
    EmailReply,
    EmailResponse,
    EmailListResponse
)
from app.services.email_service import email_service
from app.dependencies import get_current_user

logger = logging.getLogger("emails_router")

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.get("", response_model=EmailListResponse)
def list_emails(
    folder: str = Query("inbox", description="Folder: inbox, sent, starred"),
    query: Optional[str] = Query(None, description="Search keyword in subject or body"),
    sender: Optional[str] = Query(None, description="Filter by sender email or name"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    is_starred: Optional[bool] = Query(None, description="Filter by starred status"),
    days_ago: Optional[int] = Query(None, description="Filter emails from last N days"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists emails with comprehensive filtering and pagination."""
    items, total = email_service.get_emails(
        db=db,
        user_id=current_user.id,
        folder=folder,
        query=query,
        sender=sender,
        is_read=is_read,
        is_starred=is_starred,
        days_ago=days_ago,
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    parsed_items = [EmailResponse.model_validate(e) for e in items]

    return EmailListResponse(
        items=parsed_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/inbox", response_model=EmailListResponse)
def get_inbox_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convenience shortcut for inbox emails."""
    items, total = email_service.get_emails(
        db=db,
        user_id=current_user.id,
        folder="inbox",
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return EmailListResponse(
        items=[EmailResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/sent", response_model=EmailListResponse)
def get_sent_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convenience shortcut for sent emails."""
    items, total = email_service.get_emails(
        db=db,
        user_id=current_user.id,
        folder="sent",
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return EmailListResponse(
        items=[EmailResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/search", response_model=EmailListResponse)
def search_emails(
    q: str = Query(..., description="Search term across sender, subject, body"),
    folder: str = Query("inbox"),
    days_ago: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search emails endpoint."""
    items, total = email_service.get_emails(
        db=db,
        user_id=current_user.id,
        folder=folder,
        query=q,
        days_ago=days_ago,
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return EmailListResponse(
        items=[EmailResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{email_id}", response_model=EmailResponse)
def get_email_details(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full email details by ID and marks as read."""
    email_obj = email_service.get_email_by_id(db, current_user.id, email_id)
    if not email_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")

    # Automatically mark as read when opened
    if not email_obj.is_read:
        email_obj = email_service.mark_as_read(db, current_user.id, email_id, is_read=True)

    return EmailResponse.model_validate(email_obj)


@router.post("", response_model=EmailResponse, status_code=status.HTTP_201_CREATED)
async def compose_email(
    email_data: EmailCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Composes and sends an email via Gmail and saves record."""
    sent_email = await email_service.create_and_send_email(
        db=db,
        user_id=current_user.id,
        email_data=email_data
    )
    return EmailResponse.model_validate(sent_email)


@router.post("/send", response_model=EmailResponse)
async def send_email(
    email_data: EmailCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicit send endpoint matching REST contract."""
    return await compose_email(email_data=email_data, current_user=current_user, db=db)


@router.put("/{email_id}", response_model=EmailResponse)
def update_email(
    email_id: str,
    updates: EmailUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates email metadata such as read or starred state."""
    email_obj = email_service.get_email_by_id(db, current_user.id, email_id)
    if not email_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")

    if updates.is_read is not None:
        email_service.mark_as_read(db, current_user.id, email_id, updates.is_read)
    if updates.is_starred is not None:
        email_service.toggle_star(db, current_user.id, email_id, updates.is_starred)

    db.refresh(email_obj)
    return EmailResponse.model_validate(email_obj)


@router.delete("/{email_id}")
def delete_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes an email or moves it to trash."""
    success = email_service.delete_email(db, current_user.id, email_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return {"message": "Email deleted successfully."}


@router.post("/{email_id}/read", response_model=EmailResponse)
def mark_read(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks an email as read."""
    email_obj = email_service.mark_as_read(db, current_user.id, email_id, is_read=True)
    if not email_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return EmailResponse.model_validate(email_obj)


@router.post("/{email_id}/unread", response_model=EmailResponse)
def mark_unread(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks an email as unread."""
    email_obj = email_service.mark_as_read(db, current_user.id, email_id, is_read=False)
    if not email_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return EmailResponse.model_validate(email_obj)


@router.post("/{email_id}/star", response_model=EmailResponse)
def star_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stars an email."""
    email_obj = email_service.toggle_star(db, current_user.id, email_id, is_starred=True)
    if not email_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return EmailResponse.model_validate(email_obj)


@router.post("/{email_id}/unstar", response_model=EmailResponse)
def unstar_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unstars an email."""
    email_obj = email_service.toggle_star(db, current_user.id, email_id, is_starred=False)
    if not email_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return EmailResponse.model_validate(email_obj)


@router.post("/{email_id}/reply", response_model=EmailResponse)
async def reply_to_email(
    email_id: str,
    reply_data: EmailReply,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sends a reply to an existing email thread."""
    try:
        reply_email = await email_service.reply_to_email(
            db=db,
            user_id=current_user.id,
            email_id=email_id,
            body=reply_data.body,
            cc=reply_data.cc,
            bcc=reply_data.bcc
        )
        return EmailResponse.model_validate(reply_email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
