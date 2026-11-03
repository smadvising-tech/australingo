import os
from datetime import datetime

# Check if we're in demo mode (Cloudflare Worker environment)
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

# In-memory storage for demo mode - this will be replaced with Cloudflare KV in production
demo_messages_storage = []

def init_db():
    # In demo mode, we don't need to initialize anything
    if DEMO_MODE:
        return

    # For non-demo mode, we would initialize the database here
    # But in Cloudflare Workers, we'll use a different storage approach
    pass

def log_message(phone_number, message_content, direction='received', status='received'):
    # In demo mode, we store in memory
    if DEMO_MODE:
        demo_messages_storage.append({
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "phone_number": phone_number,
            "message_content": message_content,
            "status": status
        })
        return

    # For non-demo mode, we would log to the database
    # But in Cloudflare Workers, we'll use a different storage approach
    pass

def get_recent_messages(limit=50):
    # In demo mode, we return demo data
    if DEMO_MODE:
        # Return demo data in reverse order (most recent first)
        return [(msg["timestamp"], msg["direction"], msg["phone_number"], msg["message_content"], msg["status"])
                for msg in reversed(demo_messages_storage[-limit:])]

    # For non-demo mode, we would retrieve from database
    # But in Cloudflare Workers, we'll use a different storage approach
    return []
