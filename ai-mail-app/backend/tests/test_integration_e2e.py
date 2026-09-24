"""End-to-End integration test covering WebSocket streaming and the 5 AI tool-calling user flows."""
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal
from app.services.oauth_service import oauth_service
from app.services.email_service import email_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_integration():
    init_db()
    db = SessionLocal()
    user, _ = oauth_service.get_or_create_demo_user(db)
    email_service.seed_initial_emails(db, user.id)
    db.close()
    yield


def test_websocket_connection_and_event_stream():
    """Verify WebSocket endpoint connects, establishes handshake, and handles ping."""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert "user_id" in data

        # Send ping, receive pong
        websocket.send_text("ping")
        pong = websocket.receive_text()
        assert pong == "pong"


def test_end_to_end_flow1_ai_compose():
    """FLOW 1 — AI COMPOSE:
    'Compose an email to john@example.com saying I will attend tomorrow's meeting.'
    Expected: AI understands request, calls navigate_to_compose, calls fill_compose_form with typing animation.
    Does NOT send email.
    """
    req = {
        "message": "Compose an email to john@example.com saying I will attend tomorrow's meeting.",
        "current_view": "inbox"
    }
    res = client.post("/api/assistant/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    tools = [t["tool"] for t in data["tool_actions"]]

    assert "navigate_to_compose" in tools
    assert "fill_compose_form" in tools
    assert "send_email" not in tools

    fill_args = next(t["arguments"] for t in data["tool_actions"] if t["tool"] == "fill_compose_form")
    assert any("john" in r.lower() for r in fill_args["to"])
    assert "attend" in fill_args["body"].lower()


def test_end_to_end_flow2_search_emails():
    """FLOW 2 — SEARCH:
    'Find emails from John'
    Expected: AI calls search_emails, results returned, view updated.
    """
    req = {
        "message": "Find emails from John",
        "current_view": "inbox"
    }
    res = client.post("/api/assistant/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    tools = [t["tool"] for t in data["tool_actions"]]
    assert "search_emails" in tools


def test_end_to_end_flow3_open_latest_from_david():
    """FLOW 3 — OPEN EMAIL:
    'Open the latest email from David'
    Expected: AI identifies email, calls open_email.
    """
    req = {
        "message": "Open the latest email from David",
        "current_view": "inbox"
    }
    res = client.post("/api/assistant/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    tools = [t["tool"] for t in data["tool_actions"]]
    assert "open_email" in tools
    open_action = next(t for t in data["tool_actions"] if t["tool"] == "open_email")
    assert "email_id" in open_action["arguments"]


def test_end_to_end_flow4_context_aware_reply():
    """FLOW 4 — REPLY:
    'Reply to this email saying I will attend'
    Expected: Identifies current email, calls reply_to_email, populates reply body.
    """
    # Grab an email ID from inbox
    inbox = client.get("/api/emails?folder=inbox").json()
    current_email = inbox["items"][0]

    req = {
        "message": "Reply to this email saying I will attend.",
        "current_view": "email_detail",
        "current_email_id": current_email["id"]
    }
    res = client.post("/api/assistant/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    tools = [t["tool"] for t in data["tool_actions"]]
    assert "reply_to_email" in tools
    reply_action = next(t for t in data["tool_actions"] if t["tool"] == "reply_to_email")
    assert reply_action["arguments"]["email_id"] == current_email["id"]


def test_end_to_end_flow5_send_email():
    """FLOW 5 — SEND:
    'Send this email'
    Expected: Validates required fields, sends email, updates DB, sends WebSocket event.
    """
    req = {
        "message": "Send this email",
        "current_view": "compose",
        "draft_state": {
            "to": ["alex.chen@cloudscale.net"],
            "subject": "Confirmation Re: Roadmap",
            "body": "Hi Alex, everything is confirmed on our end."
        }
    }
    res = client.post("/api/assistant/chat", json=req)
    assert res.status_code == 200
    data = res.json()
    tools = [t["tool"] for t in data["tool_actions"]]
    assert "send_email" in tools

    # Verify email was actually recorded as sent in the database
    sent = client.get("/api/emails/sent").json()
    assert any(e["subject"] == "Confirmation Re: Roadmap" for e in sent["items"])
