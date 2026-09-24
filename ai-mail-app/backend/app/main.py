"""FastAPI application main entry point."""
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, SessionLocal
from app.routers import auth_router, emails_router, users_router, assistant_router
from app.websocket.manager import ws_manager
from app.services.oauth_service import oauth_service
from app.services.email_service import email_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    logger.info("Starting up AI Mail App Backend...")
    # Initialize database tables
    init_db()
    
    # Initialize demo user and sample seed emails if database is fresh
    db = SessionLocal()
    try:
        demo_user, _ = oauth_service.get_or_create_demo_user(db)
        email_service.seed_initial_emails(db, demo_user.id)
        logger.info(f"Database ready. Demo user active: {demo_user.email}")
    except Exception as e:
        logger.error(f"Error during startup seeding: {e}")
    finally:
        db.close()
        
    yield
    
    logger.info("Shutting down AI Mail App Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready AI-Powered Mail Web Application with UI-controlling agent",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
# Ensure common local dev ports are included
for dev_origin in ["http://localhost:3000", "http://127.0.0.1:3000"]:
    if dev_origin not in origins:
        origins.append(dev_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(users_router)
app.include_router(assistant_router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "google_oauth_configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time inbox synchronization and AI UI action streaming.
    Clients can connect to ws://localhost:8000/ws or ws://localhost:8000/ws?token=<jwt>
    """
    user_id = None
    if token:
        user_id = oauth_service.verify_token(token)

    # If no token provided via query param, fallback to demo user ID
    if not user_id:
        db = SessionLocal()
        try:
            demo_user, _ = oauth_service.get_or_create_demo_user(db)
            user_id = demo_user.id
        finally:
            db.close()

    await ws_manager.connect(websocket, user_id=user_id)
    try:
        # Send initial connected greeting
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "message": "Connected to AI Mail real-time event stream"
        })

        while True:
            # Keep receiving pings or client events
            data = await websocket.receive_text()
            # Respond to ping
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id=user_id)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        ws_manager.disconnect(websocket, user_id=user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
