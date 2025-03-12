from fastapi import FastAPI, Request
from chatbot import ShoppingBot
import json
import hmac
import hashlib
from config import settings

app = FastAPI()
chatbot = ShoppingBot()

# 페이스북 앱 설정
FB_APP_SECRET = "your_app_secret_here"
FB_VERIFY_TOKEN = "your_verify_token_here"

def verify_webhook(request: Request):
    """페이스북 웹훅 검증"""
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        return False
    
    body = await request.body()
    expected_signature = hmac.new(
        FB_APP_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f"sha256={expected_signature}")

@app.get("/webhook")
async def verify(request: Request):
    """페이스북 웹훅 검증 엔드포인트"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == FB_VERIFY_TOKEN:
            return int(challenge)
    return "Invalid verification token"

@app.post("/webhook")
async def webhook(request: Request):
    """페이스북 메시지 수신 및 응답"""
    if not await verify_webhook(request):
        return {"error": "Invalid signature"}
    
    body = await request.json()
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                message = messaging.get("message", {}).get("text", "")
                
                # 챗봇 응답 생성
                response = chatbot.get_response(message)
                
                # 페이스북 메시지 전송
                await send_facebook_message(sender_id, response)
    
    return "OK"

async def send_facebook_message(recipient_id: str, message: str):
    """페이스북 메시지 전송"""
    # 실제 구현에서는 페이스북 Graph API를 사용하여 메시지를 전송합니다
    # 여기서는 예시로만 구현했습니다
    print(f"메시지 전송: {recipient_id} - {message}") 