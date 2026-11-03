from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
import json
from config import WHATSAPP_WEBHOOK_VERIFY_TOKEN
from whatsapp import WhatsAppClient
from database import init_db, log_message, get_recent_messages

app = FastAPI(title="WhatsApp Business Cloud API")
init_db()
whatsapp_client = WhatsAppClient()

@app.get("/")
async def root():
    return {"message": "Australigo is running"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def handle_webhook(request: Request):
    body = await request.json()
    if "entry" in body:
        for entry in body["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    phone = message.get("from")
                    text = message.get("text", {}).get("body", "")
                    log_message(phone, text, direction="received")
    return {"status": "ok"}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    messages = get_recent_messages(20)
    rows = ""
    for ts, direction, phone, content, status in messages:
        rows += f"<tr><td>{ts}</td><td>{direction}</td><td>{phone}</td><td>{content}</td><td>{status}</td></tr>"
    html = f"""
    <html><head><title>Australigo Dashboard</title>
    <style>body{{font-family:Arial;margin:20px}} table{{width:100%;border-collapse:collapse}} th,td{{border:1px solid #ddd;padding:8px}}</style>
    </head><body>
    <h1>Australigo Dashboard</h1>
    <table><tr><th>Time</th><th>Direction</th><th>Phone</th><th>Message</th><th>Status</th></tr>
    {rows}</table></body></html>
    """
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
