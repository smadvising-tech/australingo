from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
import json
import os
from config import WHATSAPP_WEBHOOK_VERIFY_TOKEN
from whatsapp import WhatsAppClient

# Check if we're in demo mode (Cloudflare Worker environment)
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

# In-memory storage for demo mode - this will be replaced with Cloudflare KV in production
demo_messages_storage = []

app = FastAPI(title="WhatsApp Business Cloud API")

# Initialize database or demo storage
if not DEMO_MODE:
    from database import init_db, log_message, get_recent_messages
    init_db()
    whatsapp_client = WhatsAppClient()
else:
    # In demo mode, we don't use the real database
    def init_db():
        pass

    def log_message(phone_number, message_content, direction='received', status='received'):
        # Store in demo storage for demo mode
        demo_messages_storage.append({
            "timestamp": "now",
            "direction": direction,
            "phone_number": phone_number,
            "message_content": message_content,
            "status": status
        })

    def get_recent_messages(limit=20):
        # Return demo data in reverse order (most recent first)
        return [(msg["timestamp"], msg["direction"], msg["phone_number"], msg["message_content"], msg["status"])
                for msg in reversed(demo_messages_storage[-limit:])]

# Routes remain the same for both modes
@app.get("/")
async def root():
    if DEMO_MODE:
        return {"message": "Australigo is running in demo mode"}
    return {"message": "Australigo is running"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # In demo mode, we still validate the webhook but fail closed
    if mode == "subscribe" and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def handle_webhook(request: Request):
    body = await request.json()

    # In demo mode, we don't actually process WhatsApp messages
    if not DEMO_MODE and "entry" in body:
        for entry in body["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    phone = message.get("from")
                    text = message.get("text", {}).get("body", "")
                    log_message(phone, text, direction="received")
    elif DEMO_MODE:
        # In demo mode, we simulate receiving messages
        if "entry" in body:
            for entry in body["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for message in value.get("messages", []):
                        phone = message.get("from")
                        text = message.get("text", {}).get("body", "")
                        # Add to demo storage
                        log_message(phone, text, direction="received")

    return {"status": "ok"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    messages = get_recent_messages(20)
    rows = ""
    for ts, direction, phone, content, status in messages:
        rows += f"<tr><td>{ts}</td><td>{direction}</td><td>{phone}</td><td>{content}</td><td>{status}</td></tr>"

    # In demo mode, show synthetic data
    if DEMO_MODE:
        demo_rows = ""
        for i in range(5):
            demo_rows += f"<tr><td>2026-11-03 12:0{i}:00</td><td>received</td><td>+1234567890{i}</td><td>Demo message {i}</td><td>received</td></tr>"
        rows = demo_rows + rows

    html = f"""
    <html><head><title>Australigo Dashboard</title>
    <style>body{{font-family:Arial;margin:20px}} table{{width:100%;border-collapse:collapse}} th,td{{border:1px solid #ddd;padding:8px}}</style>
    </head><body>
    <h1>Australigo Dashboard</h1>
    {'<p style="color:red; font-weight:bold;">DEMO MODE - Synthetic Data Only</p>' if DEMO_MODE else ''}
    <table><tr><th>Time</th><th>Direction</th><th>Phone</th><th>Message</th><th>Status</th></tr>
    {rows}</table></body></html>
    """
    return html

@app.get("/health")
async def health():
    return {"status": "ok"}

# Cloudflare Worker entry point
if __name__ == "__main__":
    # This is for local development only
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)