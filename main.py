from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from chatbot import DotoriChatbot
import uvicorn
import os
import requests
import json
import logging

app = FastAPI(title="Dotori Mall Chatbot API")

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 확인
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables")

# Google Sheets 자격 증명 확인
GOOGLE_CREDS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not GOOGLE_CREDS:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS_JSON not found in environment variables")

# 페이스북 페이지 액세스 토큰
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
if not PAGE_ACCESS_TOKEN:
    logger.warning("PAGE_ACCESS_TOKEN not found in environment variables")

try:
    logger.info("Initializing chatbot...")
    chatbot = DotoriChatbot()
    logger.info("Chatbot initialized successfully")
except Exception as e:
    logger.error(f"Error initializing chatbot: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    chatbot = None

VERIFY_TOKEN = "dotori_chatbot_verify_token"

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Dotori Chatbot is running", "status": "ok"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    print("Webhook verification params:", params)
    
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    print(f"mode: {mode}, token: {token}, challenge: {challenge}")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            if challenge:
                return int(challenge)
            return {"status": "ok"}
        raise HTTPException(status_code=403, detail="Verification failed")
    return {"status": "ok"}

def send_message(sender_id: str, message: str):
    """페이스북 메신저로 메시지를 전송합니다."""
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        data = {
            "recipient": {"id": sender_id},
            "message": {"text": message}
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        print(f"Message sent successfully to {sender_id}")
    except Exception as e:
        print(f"Error sending message to Facebook: {e}")

@app.post("/webhook")
async def webhook(request: Request):
    print("Starting webhook processing")
    if not chatbot:
        print("Error: Chatbot not initialized")
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    try:
        body = await request.json()
        print(f"Received webhook body: {json.dumps(body, indent=2)}")
        
        if body.get("object") == "page":
            for entry in body.get("entry", []):
                print(f"Processing entry: {json.dumps(entry, indent=2)}")
                for messaging_event in entry.get("messaging", []):
                    print(f"Processing messaging event: {json.dumps(messaging_event, indent=2)}")
                    if messaging_event.get("message"):
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"]["text"]
                        print(f"Received message from {sender_id}: {message_text}")
                        try:
                            response = chatbot.process_message(message_text)
                            print(f"Generated response: {response}")
                            send_message(sender_id, response)
                        except Exception as e:
                            print(f"Error in message processing: {str(e)}")
                            print(f"Error details: {type(e).__name__}")
                            import traceback
                            print(f"Traceback: {traceback.format_exc()}")
                            send_message(sender_id, "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
                    
            return {"status": "ok"}
        
        print(f"Invalid request object type: {body.get('object')}")
        raise HTTPException(status_code=404, detail="Not Found")
    except Exception as e:
        print(f"Error in webhook endpoint: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not chatbot:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    try:
        response = chatbot.process_message(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 