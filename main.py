from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse
import json
import os
from config import WHATSAPP_WEBHOOK_VERIFY_TOKEN
from whatsapp import WhatsAppClient
from teacher_access import require_teacher
# AUSTRALIGO_TEACHER_AUTH_V1

# Check if we're in demo mode (Cloudflare Worker environment)
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"
ENABLE_D1_INBOX = os.environ.get("ENABLE_D1_INBOX") == "1"
ENABLE_DEMO_API = os.environ.get("ENABLE_DEMO_API") == "1"

# In-memory storage for demo mode - this will be replaced with Cloudflare KV in production
demo_messages_storage = []

app = FastAPI(title="WhatsApp Business Cloud API")

# AUSTRALIGO_D1_INBOX_ROUTER_V1
# D1 takes priority over the legacy SQLite demo API.
if ENABLE_D1_INBOX and not DEMO_MODE:
    raise RuntimeError("D1 inbox is restricted to the development demo environment")

if DEMO_MODE and ENABLE_D1_INBOX:
    from d1_inbox import router as d1_inbox_router
    app.include_router(
        d1_inbox_router,
        dependencies=[Depends(require_teacher)]
    )
elif DEMO_MODE and ENABLE_DEMO_API:
    from demo_inbox import router as demo_inbox_router
    app.include_router(
        demo_inbox_router,
        dependencies=[Depends(require_teacher)]
    )


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
    # AUSTRALIGO_HMAC_V1
    import hashlib
    import hmac

    secret = os.environ.get("META_APP_SECRET", "")
    if not secret:
        try:
            from workers import env as cf_env
            secret = getattr(cf_env, "META_APP_SECRET", "") or ""
        except (ImportError, AttributeError, RuntimeError):
            pass

    if not secret:
        raise HTTPException(
            status_code=503, detail="Webhook not configured"
        )

    raw = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        str(secret).encode("utf-8"), raw, hashlib.sha256
    ).hexdigest()

    if not signature.isascii() or not hmac.compare_digest(
        signature, expected
    ):
        raise HTTPException(
            status_code=403, detail="Invalid signature"
        )

    try:
        body = json.loads(raw)
    except (ValueError, UnicodeError):
        raise HTTPException(
            status_code=400, detail="Invalid JSON"
        )

    if not isinstance(body, dict):
        raise HTTPException(
            status_code=400, detail="Invalid payload"
        )

    # AUSTRALIGO_D1_WEBHOOK_V1
    if DEMO_MODE and ENABLE_D1_INBOX:
        from d1_inbox import _get_db, ingest_whatsapp_payload

        await ingest_whatsapp_payload(
            _get_db(request),
            body
        )

    elif DEMO_MODE and ENABLE_DEMO_API:
        from webhook_parser import ingest_text
        from demo_inbox import append_message

        demo_numbers = {"10000000000": "maya"}

        def save_demo_message(phone, text, direction="received"):
            student_id = demo_numbers.get(phone)
            if student_id is None:
                return

            log_message(phone, text, direction=direction)
            append_message(student_id, "incoming", text)

        from demo_dedup import claim_message, release_message

        ingest_text(
            body,
            save_demo_message,
            deduplicate=claim_message,
            release=release_message
        )

    else:
        from webhook_parser import ingest_text
        ingest_text(body, log_message)

    return {"status": "ok"}

@app.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(require_teacher)])
async def dashboard():
    # Until access control exists, never serve actual student data publicly.
    if not DEMO_MODE:
        raise HTTPException(status_code=503, detail="Dashboard login not configured")
    from dashboard_ui import DASHBOARD_HTML
    if ENABLE_D1_INBOX or ENABLE_DEMO_API:
        from dashboard_bridge import connect_demo_dashboard
        dashboard_html = connect_demo_dashboard(DASHBOARD_HTML)
    else:
        dashboard_html = DASHBOARD_HTML
    return HTMLResponse(dashboard_html, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

@app.get("/health")
async def health():
    return {"status": "ok"}

# Cloudflare Worker entry point
if __name__ == "__main__":
    # This is for local development only
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)