"""Google OAuth 2.0 and JWT authentication service."""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import requests
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.oauth_token import OAuthToken

logger = logging.getLogger("oauth_service")

# Google OAuth Scopes
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class OAuthService:
    """Manages Google OAuth 2.0 flow, token storage, and JWT token issuance."""

    @staticmethod
    def get_flow(state: Optional[str] = None) -> Flow:
        """Constructs Google OAuth flow from client config and settings."""
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=SCOPES,
            state=state,
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        return flow

    @staticmethod
    def get_authorization_url() -> Tuple[str, str]:
        """Generates Google OAuth consent URL and state token."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            # If Google credentials are not configured, allow seamless demo login fallback
            return f"{settings.BACKEND_URL}/api/auth/demo-login-redirect", "demo-state"
            
        flow = OAuthService.get_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url, state

    @staticmethod
    def exchange_code_for_user(code: str, db: Session) -> Tuple[User, str]:
        """
        Exchanges authorization code for tokens, gets user info, updates DB, and returns (User, jwt_token).
        """
        flow = OAuthService.get_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Fetch user profile from Google UserInfo API
        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
            timeout=10,
        )
        if userinfo_resp.status_code != 200:
            raise ValueError(f"Failed to fetch user info: {userinfo_resp.text}")

        user_info = userinfo_resp.json()
        email = user_info.get("email")
        name = user_info.get("name", email)
        picture = user_info.get("picture")

        if not email:
            raise ValueError("Google account did not return an email address.")

        # Find or create User
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                name=name,
                picture=picture,
            )
            db.add(user)
            db.flush()
        else:
            user.name = name
            user.picture = picture

        # Find or create OAuthToken
        oauth_token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).first()
        if not oauth_token:
            oauth_token = OAuthToken(
                user_id=user.id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id or settings.GOOGLE_CLIENT_ID,
                client_secret=credentials.client_secret or settings.GOOGLE_CLIENT_SECRET,
                scopes=json.dumps(credentials.scopes or SCOPES),
                expiry=credentials.expiry,
            )
            db.add(oauth_token)
        else:
            oauth_token.access_token = credentials.token
            if credentials.refresh_token:
                oauth_token.refresh_token = credentials.refresh_token
            oauth_token.expiry = credentials.expiry
            oauth_token.scopes = json.dumps(credentials.scopes or SCOPES)

        db.commit()
        db.refresh(user)

        jwt_token = OAuthService.create_access_token(user.id)
        return user, jwt_token

    @staticmethod
    def create_access_token(user_id: str) -> str:
        """Issues signed JWT token for session management."""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Verifies JWT token and extracts user_id."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            return user_id
        except JWTError:
            return None

    @staticmethod
    def get_or_create_demo_user(db: Session) -> Tuple[User, str]:
        """Creates or retrieves a demo user for instant testing without OAuth configuration."""
        demo_email = "demo.user@example.com"
        user = db.query(User).filter(User.email == demo_email).first()
        if not user:
            user = User(
                email=demo_email,
                name="Demo User",
                picture="https://api.dicebear.com/7.x/avataaars/svg?seed=DemoUser",
            )
            db.add(user)
            db.flush()

            # Add placeholder token
            token = OAuthToken(
                user_id=user.id,
                access_token="demo_mock_access_token",
                refresh_token="demo_mock_refresh_token",
                scopes=json.dumps(SCOPES),
                expiry=datetime.utcnow() + timedelta(days=30),
            )
            db.add(token)
            db.commit()
            db.refresh(user)

        jwt_token = OAuthService.create_access_token(user.id)
        return user, jwt_token


oauth_service = OAuthService()
