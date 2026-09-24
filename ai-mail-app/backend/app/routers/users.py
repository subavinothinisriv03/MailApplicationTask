"""User profile management router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Retrieves current user profile information."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_user_info(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user name or avatar."""
    if updates.name is not None:
        current_user.name = updates.name
    if updates.picture is not None:
        current_user.picture = updates.picture

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
