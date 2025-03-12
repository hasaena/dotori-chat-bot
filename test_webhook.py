from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
import os
import logging
import requests
import json
from pyngrok import ngrok

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

app = FastAPI()

# 웹훅 검증 토큰
VERIFY_TOKEN = "dotori_chatbot_verify_token"
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

def send_message(recipient_id: str, message_text: str):
    """페이스북 메신저로 메시지를 전송합니다."""
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": PAGE_ACCESS_TOKEN}
        headers = {"Content-Type": "application/json"}
        
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        response = requests.post(url, params=params, json=data, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.text}")
            return False
            
        logger.info(f"Message sent successfully to {recipient_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False

@app.get("/")
async def root():
    return {"message": "Dotori Chatbot Webhook Test Server"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """페이스북 웹훅 검증"""
    params = dict(request.query_params)
    logger.info(f"Webhook verification request: {params}")
    
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Webhook verified!")
            return int(challenge)
        else:
            logger.error("Verification failed")
            return {"status": "error", "message": "Invalid verification token"}
    
    return {"status": "error", "message": "Missing parameters"}

@app.post("/webhook")
async def webhook(request: Request):
    """페이스북 메시지 수신"""
    try:
        body = await request.json()
        logger.info(f"Received webhook data: {body}")
        
        # 페이지 이벤트 처리
        if body.get("object") == "page":
            for entry in body.get("entry", []):
                logger.info(f"Processing entry: {entry}")
                
                # 메시지 이벤트 처리
                for messaging in entry.get("messaging", []):
                    sender_id = messaging.get("sender", {}).get("id")
                    message = messaging.get("message", {}).get("text")
                    
                    if sender_id and message:
                        logger.info(f"Message from {sender_id}: {message}")
                        
                        # 간단한 응답 메시지 전송
                        response_text = f"메시지를 받았습니다: {message}"
                        send_message(sender_id, response_text)
                        
            return {"status": "ok"}
            
        return {"status": "error", "message": "Invalid event type"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if not PAGE_ACCESS_TOKEN:
        logger.error("PAGE_ACCESS_TOKEN is not set!")
        exit(1)
    
    try:
        # ngrok HTTP 터널 시작
        port = 8000
        public_url = ngrok.connect(port)
        logger.info(f"ngrok tunnel URL: {public_url}")
        
        # 웹훅 URL 안내
        webhook_url = f"{public_url}/webhook"
        logger.info("페이스북 웹훅 설정 방법:")
        logger.info(f"1. 웹훅 URL: {webhook_url}")
        logger.info(f"2. 검증 토큰: {VERIFY_TOKEN}")
        
        # 로컬 테스트 서버 실행
        logger.info("Starting webhook test server...")
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        exit(1)
    finally:
        # ngrok 터널 종료
        ngrok.kill() 