from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/demo", tags=["Demo inbox"])

# Fictional students only. Never connected to WhatsApp.
STUDENTS = [
    {"id": "maya", "name": "Maya L."},
    {"id": "noah", "name": "Noah T."},
    {"id": "lina", "name": "Lina P."},
    {"id": "elio", "name": "Elio R."},
]

lock = Lock()

history = {
    "maya": [
        {"id": "demo-1", "direction": "incoming",
         "text": "Hello teacher!", "created_at": "2026-11-03T09:00:00Z"}
    ],
    "noah": [
        {"id": "demo-2", "direction": "incoming",
         "text": "Can we practice again?", "created_at": "2026-11-03T09:15:00Z"}
    ],
    "lina": [
        {"id": "demo-3", "direction": "incoming",
         "text": "Thank you for the lesson!", "created_at": "2026-11-03T09:30:00Z"}
    ],
    "elio": [
        {"id": "demo-4", "direction": "incoming",
         "text": "See you next lesson!", "created_at": "2026-11-03T09:45:00Z"}
    ],
}

unread = {"maya": 1, "noah": 1, "lina": 0, "elio": 0}

# AUSTRALIGO_SQLITE_DEMO_V1
from demo_sqlite_store import SQLiteBackedDict
history = SQLiteBackedDict('history', history)
unread = SQLiteBackedDict('unread', unread)



class MessageInput(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def require_student(student_id):
    if student_id not in history:
        raise HTTPException(status_code=404, detail="Conversation not found")


def append_message(student_id, direction, text):
    text = text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Empty message")

    message = {
        "id": uuid4().hex,
        "direction": direction,
        "text": text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with lock:
        history[student_id].append(message)
        history[student_id] = history[student_id][-100:]

        if direction == "incoming":
            unread[student_id] += 1

    return message


@router.get("/conversations")
def conversations():
    with lock:
        result = []
        for student in STUDENTS:
            student_id = student["id"]
            latest = history[student_id][-1]
            result.append({
                **student,
                "preview": latest["text"],
                "last_at": latest["created_at"],
                "unread": unread[student_id],
            })

    return {"conversations": result}


@router.get("/conversations/{student_id}/messages")
def messages(student_id: str):
    require_student(student_id)
    with lock:
        return {"messages": list(history[student_id])}


@router.post("/conversations/{student_id}/reply")
def reply(student_id: str, body: MessageInput):
    require_student(student_id)
    message = append_message(student_id, "outgoing", body.text)
    return {"message": message, "demo": True}


@router.post("/conversations/{student_id}/simulate")
def simulate_incoming(student_id: str, body: MessageInput):
    require_student(student_id)
    message = append_message(student_id, "incoming", body.text)
    return {"message": message, "demo": True}


@router.post("/conversations/{student_id}/read")
def mark_read(student_id: str):
    require_student(student_id)
    with lock:
        unread[student_id] = 0
    return {"status": "ok"}
