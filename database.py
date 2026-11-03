import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('whatsapp_messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            direction TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            message_content TEXT,
            status TEXT DEFAULT 'received'
        )
    ''')
    conn.commit()
    conn.close()

def log_message(phone_number, message_content, direction='received', status='received'):
    conn = sqlite3.connect('whatsapp_messages.db')
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO messages (timestamp, direction, phone_number, message_content, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, direction, phone_number, message_content, status))
    conn.commit()
    conn.close()

def get_recent_messages(limit=50):
    conn = sqlite3.connect('whatsapp_messages.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, direction, phone_number, message_content, status
        FROM messages ORDER BY timestamp DESC LIMIT ?
    ''', (limit,))
    messages = cursor.fetchall()
    conn.close()
    return messages
