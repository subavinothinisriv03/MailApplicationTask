"""Routers package export."""
from app.routers.auth import router as auth_router
from app.routers.emails import router as emails_router
from app.routers.users import router as users_router
from app.routers.assistant import router as assistant_router

__all__ = ["auth_router", "emails_router", "users_router", "assistant_router"]
