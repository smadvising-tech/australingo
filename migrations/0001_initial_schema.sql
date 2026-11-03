
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone_number TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_students_phone
ON students(phone_number)
WHERE phone_number IS NOT NULL;

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL UNIQUE
        REFERENCES students(id) ON DELETE CASCADE,
    unread_count INTEGER NOT NULL DEFAULT 0
        CHECK (unread_count >= 0),
    last_message_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL
        REFERENCES conversations(id) ON DELETE CASCADE,
    whatsapp_message_id TEXT UNIQUE,
    direction TEXT NOT NULL
        CHECK (direction IN ('incoming', 'outgoing')),
    text TEXT NOT NULL
        CHECK (length(trim(text)) BETWEEN 1 AND 4096),
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'received'
);

CREATE TABLE IF NOT EXISTS processed_webhook_messages (
    message_id TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
ON messages(conversation_id, created_at, id);

CREATE INDEX IF NOT EXISTS idx_conversations_last_message
ON conversations(last_message_at DESC);

-- Fictional students only.
INSERT OR IGNORE INTO students (id, name, phone_number) VALUES
('maya', 'Maya L.', '10000000000'),
('noah', 'Noah T.', NULL),
('lina', 'Lina P.', NULL),
('elio', 'Elio R.', NULL);

-- Keep existing dashboard conversation IDs.
INSERT OR IGNORE INTO conversations
(id, student_id, unread_count, last_message_at)
VALUES
('maya', 'maya', 1, '2026-11-03T09:00:00Z'),
('noah', 'noah', 1, '2026-11-03T09:15:00Z'),
('lina', 'lina', 0, '2026-11-03T09:30:00Z'),
('elio', 'elio', 0, '2026-11-03T09:45:00Z');

INSERT OR IGNORE INTO messages
(id, conversation_id, direction, text, created_at, status)
VALUES
('demo-1', 'maya', 'incoming', 'Hello teacher!', '2026-11-03T09:00:00Z', 'received'),
('demo-2', 'noah', 'incoming', 'Can we practice again?', '2026-11-03T09:15:00Z', 'received'),
('demo-3', 'lina', 'incoming', 'Thank you for the lesson!', '2026-11-03T09:30:00Z', 'received'),
('demo-4', 'elio', 'incoming', 'See you next lesson!', '2026-11-03T09:45:00Z', 'received');

-- Keep message insertion, unread updates and deduplication atomic.
CREATE TRIGGER IF NOT EXISTS messages_after_insert
AFTER INSERT ON messages
BEGIN
    UPDATE conversations
    SET
        unread_count = unread_count +
            CASE WHEN NEW.direction = 'incoming' THEN 1 ELSE 0 END,
        last_message_at = CASE
            WHEN last_message_at IS NULL OR NEW.created_at > last_message_at
            THEN NEW.created_at
            ELSE last_message_at
        END,
        updated_at = NEW.created_at
    WHERE id = NEW.conversation_id;

    INSERT INTO processed_webhook_messages (message_id, processed_at)
    SELECT NEW.whatsapp_message_id, NEW.created_at
    WHERE NEW.whatsapp_message_id IS NOT NULL;
END;
