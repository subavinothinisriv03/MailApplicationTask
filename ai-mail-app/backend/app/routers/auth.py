"""Authentication API router for Google OAuth 2.0 and user sessions."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, TokenResponse
from app.services.oauth_service import oauth_service
from app.dependencies import get_current_user

logger = logging.getLogger("auth_router")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/google/login")
async def google_login():
    """Initiates Google OAuth flow by redirecting to Google authorization URL."""
    try:
        auth_url, state = oauth_service.get_authorization_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error generating Google OAuth URL: {e}")
        # Fallback to frontend with error or demo login
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=oauth_init_failed")


@router.get("/demo-login-redirect")
async def demo_login_redirect(db: Session = Depends(get_db)):
    """Automatic redirect to demo user session when Google credentials are not supplied."""
    user, jwt_token = oauth_service.get_or_create_demo_user(db)
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/inbox?token={jwt_token}")
    response.set_cookie(key="access_token", value=jwt_token, httponly=True, max_age=86400 * 7)
    return response


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Handles OAuth callback redirect from Google."""
    if error:
        logger.warning(f"Google OAuth returned error: {error}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error={error}")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code.")

    try:
        user, jwt_token = oauth_service.exchange_code_for_user(code=code, db=db)
        # Redirect user back to frontend inbox with JWT token
        redirect_url = f"{settings.FRONTEND_URL}/inbox?token={jwt_token}"
        response = RedirectResponse(url=redirect_url)
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7
        )
        return response
    except Exception as e:
        logger.error(f"Error exchanging OAuth code: {e}")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=auth_exchange_failed")


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(response: Response, db: Session = Depends(get_db)):
    """1-Click demo authentication endpoint for testing without Google keys."""
    user, jwt_token = oauth_service.get_or_create_demo_user(db)
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7
    )
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user profile."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(response: Response):
    """Clears authentication cookies."""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully."}
