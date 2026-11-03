
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/demo", tags=["D1 inbox"])


class MessageInput(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def _plain(value):
    if value is None:
        return None

    converter = getattr(value, "to_py", None)
    if callable(converter):
        value = converter()

    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]

    if hasattr(value, "items"):
        return {str(k): _plain(v) for k, v in value.items()}

    return value


def _get_db(request):
    env = request.scope.get("env")

    db = getattr(env, "DB", None) if env is not None else None

    if db is None and isinstance(env, dict):
        db = env.get("DB")

    if db is None:
        raise HTTPException(
            status_code=503,
            detail="D1 database binding unavailable"
        )

    return db


async def _execute(db, sql, *params):
    statement = db.prepare(sql)

    if params:
        statement = statement.bind(*params)

    return await statement.run()


def _rows(result):
    rows = _plain(getattr(result, "results", [])) or []

    if not isinstance(rows, list):
        raise RuntimeError("Unexpected D1 result format")

    return rows


def _changes(result):
    meta = _plain(getattr(result, "meta", {})) or {}

    return int(meta.get("changes", 0))


async def _query(db, sql, *params):
    result = await _execute(db, sql, *params)
    return _rows(result)


async def _get_conversation(db, student_id):
    rows = await _query(
        db,
        """
        SELECT
            c.id AS conversation_id,
            c.student_id,
            s.name,
            s.phone_number
        FROM conversations c
        JOIN students s ON s.id = c.student_id
        WHERE s.id = ?
        LIMIT 1
        """,
        student_id
    )

    return rows[0] if rows else None


async def list_conversations(db):
    return await _query(
        db,
        """
        SELECT
            s.id,
            s.name,
            COALESCE(last_message.text, '') AS preview,
            COALESCE(
                last_message.created_at,
                c.last_message_at,
                c.created_at
            ) AS last_at,
            c.unread_count AS unread
        FROM conversations c
        JOIN students s ON s.id = c.student_id
        LEFT JOIN messages last_message
            ON last_message.id = (
                SELECT m.id
                FROM messages m
                WHERE m.conversation_id = c.id
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT 1
            )
        ORDER BY
            COALESCE(c.last_message_at, c.created_at) DESC,
            s.name COLLATE NOCASE ASC
        """
    )


async def list_messages(db, student_id):
    conversation = await _get_conversation(db, student_id)

    if not conversation:
        raise HTTPException(404, "Conversation not found")

    return await _query(
        db,
        """
        SELECT
            m.id,
            m.direction,
            m.text,
            m.created_at,
            m.status
        FROM messages m
        WHERE m.conversation_id = ?
        ORDER BY m.created_at ASC, m.id ASC
        """,
        conversation["conversation_id"]
    )


async def _insert_message(
    db,
    conversation_id,
    direction,
    text,
    status,
    whatsapp_message_id=None
):
    text = text.strip()

    if not text or len(text) > 4096:
        raise HTTPException(422, "Invalid message text")

    message = {
        "id": uuid4().hex,
        "direction": direction,
        "text": text,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z"),
        "status": status
    }

    sql = """
        INSERT INTO messages (
            id,
            conversation_id,
            whatsapp_message_id,
            direction,
            text,
            created_at,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    # Only webhook messages have a WhatsApp ID.
    # INSERT OR IGNORE makes duplicate delivery safe.
    if whatsapp_message_id is not None:
        sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")

    result = await _execute(
        db,
        sql,
        message["id"],
        conversation_id,
        whatsapp_message_id,
        direction,
        text,
        message["created_at"],
        status
    )

    if _changes(result) != 1:
        return None

    return message


async def create_reply(db, student_id, text):
    conversation = await _get_conversation(db, student_id)

    if not conversation:
        raise HTTPException(404, "Conversation not found")

    message = await _insert_message(
        db,
        conversation["conversation_id"],
        "outgoing",
        text,
        "saved"
    )

    if message is None:
        raise HTTPException(500, "Could not save reply")

    # Saved only. This does NOT send a WhatsApp message.
    return message


async def simulate_incoming(db, student_id, text):
    conversation = await _get_conversation(db, student_id)

    if not conversation:
        raise HTTPException(404, "Conversation not found")

    message = await _insert_message(
        db,
        conversation["conversation_id"],
        "incoming",
        text,
        "received"
    )

    if message is None:
        raise HTTPException(500, "Could not save message")

    return message


async def mark_read(db, student_id):
    conversation = await _get_conversation(db, student_id)

    if not conversation:
        raise HTTPException(404, "Conversation not found")

    await _execute(
        db,
        """
        UPDATE conversations
        SET unread_count = 0
        WHERE student_id = ?
        """,
        student_id
    )

    return {"status": "ok"}


async def save_incoming_by_phone(
    db,
    phone,
    text,
    whatsapp_message_id
):
    conversation_rows = await _query(
        db,
        """
        SELECT c.id AS conversation_id
        FROM students s
        JOIN conversations c ON c.student_id = s.id
        WHERE s.phone_number = ?
        LIMIT 1
        """,
        phone
    )

    if not conversation_rows:
        return {"stored": False, "unmatched": True}

    message = await _insert_message(
        db,
        conversation_rows[0]["conversation_id"],
        "incoming",
        text,
        "received",
        whatsapp_message_id=whatsapp_message_id
    )

    if message is None:
        return {"stored": False, "duplicate": True}

    # The database trigger updates unread_count and
    # processed_webhook_messages automatically.
    return {"stored": True, "message": message}


async def ingest_whatsapp_payload(db, payload):
    accepted = 0
    duplicates = 0
    unmatched = 0
    ignored = 0

    if not isinstance(payload, dict):
        return {
            "accepted": 0,
            "duplicates": 0,
            "unmatched": 0,
            "ignored": 1
        }

    if payload.get("object") != "whatsapp_business_account":
        return {
            "accepted": 0,
            "duplicates": 0,
            "unmatched": 0,
            "ignored": 0
        }

    entries = payload.get("entry")

    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            ignored += 1
            continue

        changes = entry.get("changes")

        for change in changes if isinstance(changes, list) else []:
            if not isinstance(change, dict):
                ignored += 1
                continue

            value = change.get("value")
            messages = value.get("messages") if isinstance(value, dict) else None

            for item in messages if isinstance(messages, list) else []:
                if not isinstance(item, dict) or item.get("type") != "text":
                    ignored += 1
                    continue

                message_id = item.get("id")
                phone = item.get("from")
                text_obj = item.get("text")
                text = text_obj.get("body") if isinstance(text_obj, dict) else None

                if not (
                    isinstance(message_id, str) and message_id
                    and isinstance(phone, str)
                    and phone.isascii() and phone.isdigit()
                    and isinstance(text, str) and text.strip()
                ):
                    ignored += 1
                    continue

                result = await save_incoming_by_phone(
                    db,
                    phone,
                    text.strip()[:4096],
                    message_id
                )

                if result.get("stored"):
                    accepted += 1
                elif result.get("duplicate"):
                    duplicates += 1
                elif result.get("unmatched"):
                    unmatched += 1

    return {
        "accepted": accepted,
        "duplicates": duplicates,
        "unmatched": unmatched,
        "ignored": ignored
    }


# Preserve the existing dashboard API contract.

@router.get("/conversations")
async def conversations(request: Request):
    return {
        "conversations": await list_conversations(_get_db(request))
    }


@router.get("/conversations/{student_id}/messages")
async def messages(student_id: str, request: Request):
    return {
        "messages": await list_messages(
            _get_db(request), student_id
        )
    }


@router.post("/conversations/{student_id}/reply")
async def reply(
    student_id: str,
    body: MessageInput,
    request: Request
):
    message = await create_reply(
        _get_db(request), student_id, body.text
    )
    return {"message": message, "demo": True}


@router.post("/conversations/{student_id}/simulate")
async def simulate(
    student_id: str,
    body: MessageInput,
    request: Request
):
    message = await simulate_incoming(
        _get_db(request), student_id, body.text
    )
    return {"message": message, "demo": True}


@router.post("/conversations/{student_id}/read")
async def read(student_id: str, request: Request):
    return await mark_read(_get_db(request), student_id)
