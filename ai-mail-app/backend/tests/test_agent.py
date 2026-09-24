"""Tests for AI Agent tool calling, context awareness, and UI actions."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, SessionLocal
from app.services.oauth_service import oauth_service
from app.services.email_service import email_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    db = SessionLocal()
    user, token = oauth_service.get_or_create_demo_user(db)
    email_service.seed_initial_emails(db, user.id)
    db.close()
    yield


def test_ai_compose_flow():
    """Verify AI calls navigate_to_compose and fill_compose_form without sending."""
    payload = {
        "message": "Compose an email to john@example.com with subject Meeting Tomorrow and body Let's meet at 3pm",
        "current_view": "inbox"
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "tool_actions" in data
    tools_called = [t["tool"] for t in data["tool_actions"]]
    
    assert "navigate_to_compose" in tools_called
    assert "fill_compose_form" in tools_called
    # Critical Safety Guard: Must NOT have called send_email!
    assert "send_email" not in tools_called

    # Check fill_compose_form arguments
    fill_action = next(t for t in data["tool_actions"] if t["tool"] == "fill_compose_form")
    assert "john@example.com" in fill_action["arguments"]["to"]
    assert "meeting" in fill_action["arguments"]["subject"].lower()


def test_ai_search_flow():
    """Verify AI calls search_emails with query."""
    payload = {
        "message": "Find emails from Sarah",
        "current_view": "inbox"
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    tools_called = [t["tool"] for t in data["tool_actions"]]
    assert "search_emails" in tools_called


def test_ai_open_email_flow():
    """Verify AI searches and calls open_email for latest email from David."""
    payload = {
        "message": "Open the latest email from David",
        "current_view": "inbox"
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    tools_called = [t["tool"] for t in data["tool_actions"]]
    assert "open_email" in tools_called


def test_ai_reply_flow():
    """Verify AI detects currently opened email and calls reply_to_email."""
    # Get an email ID from inbox
    inbox_res = client.get("/api/emails?folder=inbox")
    first_id = inbox_res.json()["items"][0]["id"]

    payload = {
        "message": "Reply to this email saying I will attend tomorrow's meeting",
        "current_view": "email_detail",
        "current_email_id": first_id
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    tools_called = [t["tool"] for t in data["tool_actions"]]
    assert "reply_to_email" in tools_called
    reply_action = next(t for t in data["tool_actions"] if t["tool"] == "reply_to_email")
    assert reply_action["arguments"]["email_id"] == first_id


def test_ai_send_explicit_flow():
    """Verify AI calls send_email when instructed explicitly to send."""
    payload = {
        "message": "Send the email",
        "current_view": "compose",
        "draft_state": {
            "to": ["partner@test.com"],
            "subject": "Ready to send",
            "body": "This is confirmed."
        }
    }
    response = client.post("/api/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    tools_called = [t["tool"] for t in data["tool_actions"]]
    assert "send_email" in tools_called
