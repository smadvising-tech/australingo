from collections import deque

_seen = set()
_order = deque()

def ingest_text(payload, save):
    """Process text messages; deduplicate within this Python process only."""
    if payload.get("object") != "whatsapp_business_account":
        return 0
    count = 0
    entries = payload.get("entry")
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        changes = entry.get("changes")
        for change in changes if isinstance(changes, list) else []:
            if not isinstance(change, dict):
                continue
            value = change.get("value")
            messages = value.get("messages") if isinstance(value, dict) else None
            for msg in messages if isinstance(messages, list) else []:
                if not isinstance(msg, dict) or msg.get("type") != "text":
                    continue
                mid, phone, text_obj = msg.get("id"), msg.get("from"), msg.get("text")
                body = text_obj.get("body") if isinstance(text_obj, dict) else None
                if not (isinstance(mid, str) and mid and isinstance(phone, str)
                        and phone.isascii() and phone.isdigit()
                        and isinstance(body, str) and body.strip()):
                    continue
                if mid in _seen:
                    continue
                save(phone, body.strip()[:4096], direction="received")
                _seen.add(mid)
                _order.append(mid)
                if len(_order) > 1024:
                    _seen.discard(_order.popleft())
                count += 1
    return count
