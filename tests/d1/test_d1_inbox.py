
import asyncio
import sqlite3
from pathlib import Path

import d1_inbox as repo


MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "0001_initial_schema.sql"
)


class FakeResult:
    def __init__(self, rows, changes):
        self.results = rows
        self.meta = {"changes": changes}


class FakeStatement:
    def __init__(self, database, sql):
        self.database = database
        self.sql = sql
        self.params = ()

    def bind(self, *params):
        self.params = params
        return self

    async def run(self):
        cursor = self.database.connection.execute(
            self.sql, self.params
        )

        rows = (
            [dict(row) for row in cursor.fetchall()]
            if cursor.description else []
        )

        changes = max(cursor.rowcount, 0)
        self.database.connection.commit()

        return FakeResult(rows, changes)


class FakeD1:
    def __init__(self):
        self.connection = sqlite3.connect(":memory:", check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

        self.connection.executescript(
            MIGRATION.read_text(encoding="utf-8")
        )

    def prepare(self, sql):
        return FakeStatement(self, sql)


def run(coro):
    return asyncio.run(coro)


def make_db():
    return FakeD1()


def test_seeded_conversations():
    db = make_db()

    conversations = run(repo.list_conversations(db))

    assert len(conversations) == 4

    maya = next(c for c in conversations if c["id"] == "maya")
    assert maya["name"] == "Maya L."
    assert maya["preview"] == "Hello teacher!"
    assert maya["unread"] == 1

    messages = run(repo.list_messages(db, "maya"))
    assert len(messages) == 1
    assert messages[0]["text"] == "Hello teacher!"


def test_teacher_reply_is_persisted_without_unread_increment():
    db = make_db()

    message = run(repo.create_reply(
        db, "maya", "Let's practice together."
    ))

    assert message["direction"] == "outgoing"
    assert message["status"] == "saved"

    messages = run(repo.list_messages(db, "maya"))
    assert len(messages) == 2
    assert messages[-1]["text"] == "Let's practice together."

    conversations = run(repo.list_conversations(db))
    maya = next(c for c in conversations if c["id"] == "maya")

    # Outgoing messages must not increase unread.
    assert maya["unread"] == 1


def test_incoming_message_trigger_increments_unread():
    db = make_db()

    message = run(repo.simulate_incoming(
        db, "maya", "Can we practice past tense?"
    ))

    assert message["direction"] == "incoming"

    conversations = run(repo.list_conversations(db))
    maya = next(c for c in conversations if c["id"] == "maya")

    assert maya["unread"] == 2
    assert maya["preview"] == "Can we practice past tense?"


def test_mark_read():
    db = make_db()

    result = run(repo.mark_read(db, "maya"))
    assert result["status"] == "ok"

    conversations = run(repo.list_conversations(db))
    maya = next(c for c in conversations if c["id"] == "maya")

    assert maya["unread"] == 0


def test_webhook_deduplication_survives_repeated_calls():
    db = make_db()

    first = run(repo.save_incoming_by_phone(
        db,
        "10000000000",
        "I need help with English.",
        "wamid.test.001"
    ))

    second = run(repo.save_incoming_by_phone(
        db,
        "10000000000",
        "I need help with English.",
        "wamid.test.001"
    ))

    assert first["stored"] is True
    assert second["duplicate"] is True

    conversations = run(repo.list_conversations(db))
    maya = next(c for c in conversations if c["id"] == "maya")

    # Original unread 1 + exactly one incoming message.
    assert maya["unread"] == 2

    messages = run(repo.list_messages(db, "maya"))
    assert len(messages) == 2

    count = db.connection.execute(
        "SELECT COUNT(*) FROM processed_webhook_messages"
    ).fetchone()[0]

    assert count == 1


def test_unknown_phone_is_not_assigned_to_student():
    db = make_db()

    result = run(repo.save_incoming_by_phone(
        db,
        "19999999999",
        "Unknown student",
        "wamid.test.002"
    ))

    assert result["unmatched"] is True

    messages = run(repo.list_messages(db, "maya"))
    assert len(messages) == 1


def test_webhook_payload_and_duplicate_delivery():
    db = make_db()

    item = {
        "id": "wamid.test.003",
        "from": "10000000000",
        "type": "text",
        "text": {"body": "Hello teacher"}
    }

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {"messages": [item, item]}
            }]
        }]
    }

    result = run(repo.ingest_whatsapp_payload(db, payload))

    assert result["accepted"] == 1
    assert result["duplicates"] == 1


def test_foreign_key_integrity():
    db = make_db()

    violations = db.connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    assert violations == []
