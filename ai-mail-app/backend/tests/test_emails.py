"""Tests for Email CRUD endpoints and services."""
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


def test_health_endpoint():
    """Verify health endpoint returns healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_inbox_emails():
    """Verify list emails returns seeded inbox items with pagination."""
    response = client.get("/api/emails?folder=inbox&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) > 0
    # Check item schema structure
    first = data["items"][0]
    assert "id" in first
    assert "subject" in first
    assert "sender" in first
    assert isinstance(first["recipients"], list)


def test_filter_emails_by_sender():
    """Verify filtering by sender name."""
    response = client.get("/api/emails?sender=David")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert "david" in item["sender"].lower() or "david" in (item["sender_name"] or "").lower()


def test_filter_emails_by_days_ago():
    """Verify filtering emails by date range (last 10 days)."""
    response = client.get("/api/emails?days_ago=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_compose_and_send_email():
    """Verify composing and sending an email creates record and broadcasts."""
    payload = {
        "to": ["partner@enterprise.org"],
        "subject": "Automated Test Email",
        "body": "This is a test body payload."
    }
    response = client.post("/api/emails", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["subject"] == "Automated Test Email"
    assert created["is_sent"] is True

    # Verify email appears in /api/emails/sent
    sent_res = client.get("/api/emails/sent")
    assert sent_res.status_code == 200
    sent_items = sent_res.json()["items"]
    assert any(e["id"] == created["id"] for e in sent_items)


def test_mark_read_and_starred():
    """Verify toggling read and star statuses."""
    inbox_res = client.get("/api/emails?folder=inbox")
    email_id = inbox_res.json()["items"][0]["id"]

    # Mark unread
    res_unread = client.post(f"/api/emails/{email_id}/unread")
    assert res_unread.status_code == 200
    assert res_unread.json()["is_read"] is False

    # Mark read
    res_read = client.post(f"/api/emails/{email_id}/read")
    assert res_read.status_code == 200
    assert res_read.json()["is_read"] is True

    # Star
    res_star = client.post(f"/api/emails/{email_id}/star")
    assert res_star.status_code == 200
    assert res_star.json()["is_starred"] is True
