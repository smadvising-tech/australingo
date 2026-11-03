
import os
import json
import hmac
import hashlib
import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_d1_inbox import FakeD1

AUTH = ("d1-teacher", "local-test-password")


class InjectEnvironment:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            scope = dict(scope)
            scope["env"] = {"DB": self.db}

        await self.app(scope, receive, send)


@pytest.fixture
def system(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("ENABLE_D1_INBOX", "1")
    monkeypatch.setenv("ENABLE_DEMO_API", "0")
    monkeypatch.setenv("TEACHER_USERNAME", AUTH[0])
    monkeypatch.setenv("TEACHER_PASSWORD", AUTH[1])
    monkeypatch.setenv("META_APP_SECRET", "test-webhook-secret")

    if "main" in sys.modules:
        module = importlib.reload(sys.modules["main"])
    else:
        module = importlib.import_module("main")

    db = FakeD1()
    client = TestClient(InjectEnvironment(module.app, db))

    return client, db


def test_d1_routes_require_teacher(system):
    client, db = system

    assert client.get("/health").status_code == 200

    assert client.get(
        "/api/demo/conversations"
    ).status_code == 401

    assert client.get("/dashboard").status_code == 401

    response = client.get(
        "/api/demo/conversations",
        auth=AUTH
    )

    assert response.status_code == 200
    assert len(response.json()["conversations"]) == 4


def test_d1_dashboard_operations(system):
    client, db = system

    response = client.get(
        "/api/demo/conversations/maya/messages",
        auth=AUTH
    )
    assert response.status_code == 200
    assert len(response.json()["messages"]) == 1

    response = client.post(
        "/api/demo/conversations/maya/reply",
        json={"text": "Let's practice together."},
        auth=AUTH
    )
    assert response.status_code == 200
    assert response.json()["message"]["direction"] == "outgoing"

    response = client.post(
        "/api/demo/conversations/maya/simulate",
        json={"text": "I have a question."},
        auth=AUTH
    )
    assert response.status_code == 200

    response = client.post(
        "/api/demo/conversations/maya/read",
        auth=AUTH
    )
    assert response.status_code == 200

    conversations = client.get(
        "/api/demo/conversations",
        auth=AUTH
    ).json()["conversations"]

    maya = next(c for c in conversations if c["id"] == "maya")
    assert maya["unread"] == 0


def test_signed_webhook_is_persisted_and_deduplicated(system):
    client, db = system

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "wamid.integration.001",
                        "from": "10000000000",
                        "type": "text",
                        "text": {
                            "body": "Can we practice English?"
                        }
                    }]
                }
            }]
        }]
    }

    raw = json.dumps(
        payload,
        separators=(",", ":")
    ).encode()

    signature = "sha256=" + hmac.new(
        b"test-webhook-secret",
        raw,
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }

    first = client.post(
        "/webhook",
        content=raw,
        headers=headers
    )

    second = client.post(
        "/webhook",
        content=raw,
        headers=headers
    )

    assert first.status_code == 200
    assert second.status_code == 200

    messages = client.get(
        "/api/demo/conversations/maya/messages",
        auth=AUTH
    ).json()["messages"]

    assert sum(
        m["text"] == "Can we practice English?"
        for m in messages
    ) == 1

    count = db.connection.execute(
        "SELECT COUNT(*) FROM processed_webhook_messages"
    ).fetchone()[0]

    assert count == 1
