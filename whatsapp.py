import requests
from config import WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_API_VERSION

class WhatsAppClient:
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"
        self.headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, to_phone_number, message_text):
        url = f"{self.base_url}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone_number,
            "text": {"body": message_text}
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
