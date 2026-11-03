import os
import sqlite3
from pathlib import Path

def connect():
    path = os.environ.get(
        "DEMO_DB_PATH",
        "/kaggle/working/australingo-demo.sqlite3"
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.execute("""
        CREATE TABLE IF NOT EXISTS processed_webhook_messages (
            message_id TEXT PRIMARY KEY,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return db

def claim_message(message_id):
    db = connect()
    try:
        cursor = db.execute(
            "INSERT OR IGNORE INTO processed_webhook_messages "
            "(message_id) VALUES (?)",
            (message_id,)
        )
        db.commit()
        return cursor.rowcount == 1
    finally:
        db.close()

def release_message(message_id):
    db = connect()
    try:
        db.execute(
            "DELETE FROM processed_webhook_messages WHERE message_id=?",
            (message_id,)
        )
        db.commit()
    finally:
        db.close()
