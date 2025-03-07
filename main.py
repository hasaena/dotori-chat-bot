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
    logger.info("챗봇 초기화 시작...")
    logger.debug(f"OPENAI_API_KEY 설정 여부: {bool(OPENAI_API_KEY)}")
    logger.debug(f"GOOGLE_CREDS 설정 여부: {bool(GOOGLE_CREDS)}")
    logger.debug(f"PAGE_ACCESS_TOKEN 설정 여부: {bool(PAGE_ACCESS_TOKEN)}")
    
    chatbot = DotoriChatbot()
    logger.info("챗봇이 성공적으로 초기화되었습니다.")
except Exception as e:
    logger.error(f"챗봇 초기화 중 오류 발생: {str(e)}")
    logger.error(f"상세 오류: {traceback.format_exc()}")
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
        if not PAGE_ACCESS_TOKEN:
            logger.error("PAGE_ACCESS_TOKEN이 설정되지 않았습니다.")
            return False
            
        url = "https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": PAGE_ACCESS_TOKEN}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        data = {
            "recipient": {"id": sender_id},
            "message": {"text": message}
        }
        
        logger.info(f"페이스북 메시지 전송 시도 - URL: {url}")
        logger.info(f"페이스북 메시지 전송 시도 - 수신자: {sender_id}")
        logger.debug(f"전송 데이터: {json.dumps(data, ensure_ascii=False)}")
        
        # 타임아웃 설정 추가
        response = requests.post(
            url, 
            params=params, 
            headers=headers, 
            json=data,
            timeout=10  # 10초 타임아웃
        )
        
        response_data = response.json() if response.text else {}
        logger.debug(f"페이스북 응답: {json.dumps(response_data, ensure_ascii=False)}")
        
        if response.status_code == 200:
            if response_data.get("error"):
                logger.error(f"페이스북 API 오류: {response_data['error']}")
                return False
            logger.info(f"메시지 전송 성공 - 수신자: {sender_id}")
            return True
        else:
            logger.error(f"메시지 전송 실패 - 상태 코드: {response.status_code}")
            logger.error(f"오류 응답: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("페이스북 API 요청 타임아웃")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("페이스북 서버 연결 실패")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"메시지 전송 중 네트워크 오류 발생: {str(e)}", exc_info=True)
        return False
    except json.JSONDecodeError as e:
        logger.error(f"페이스북 응답 JSON 파싱 오류: {str(e)}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"메시지 전송 중 예상치 못한 오류 발생: {str(e)}", exc_info=True)
        return False

@app.post("/webhook")
async def webhook(request: Request):
    """페이스북 메시지 수신 및 처리"""
    if not chatbot:
        logger.error("챗봇이 초기화되지 않았습니다.")
        raise HTTPException(status_code=500, detail="챗봇이 초기화되지 않았습니다.")
        
    try:
        # 요청 바디 파싱
        try:
            body = await request.json()
            logger.info(f"웹훅 데이터 수신: {json.dumps(body, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {str(e)}")
            raise HTTPException(status_code=400, detail="잘못된 JSON 형식입니다.")
        
        # 페이지 이벤트 검증
        if body.get("object") != "page":
            logger.warning(f"페이지 이벤트가 아닙니다: {body.get('object')}")
            raise HTTPException(status_code=400, detail="잘못된 이벤트 타입입니다.")
        
        # 메시지 처리
        for entry in body.get("entry", []):
            logger.debug(f"엔트리 처리: {json.dumps(entry, indent=2, ensure_ascii=False)}")
            
            for messaging_event in entry.get("messaging", []):
                logger.debug(f"메시징 이벤트 처리: {json.dumps(messaging_event, indent=2, ensure_ascii=False)}")
                
                if messaging_event.get("message"):
                    try:
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"].get("text")
                        
                        if not message_text:
                            logger.warning(f"텍스트가 없는 메시지 수신: {messaging_event}")
                            send_message(sender_id, "죄송합니다. 텍스트 메시지만 처리할 수 있습니다.")
                            continue
                            
                        logger.info(f"메시지 수신 - 발신자: {sender_id}, 내용: {message_text}")
                        
                        # 챗봇 응답 생성
                        try:
                            response = chatbot.process_message(message_text)
                            if not response:
                                logger.error("챗봇이 빈 응답을 반환했습니다.")
                                response = "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                        except Exception as e:
                            logger.error(f"챗봇 응답 생성 중 오류 발생: {str(e)}", exc_info=True)
                            response = "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                        
                        # 응답 전송
                        if not send_message(sender_id, response):
                            logger.error(f"메시지 전송 실패 - 발신자: {sender_id}")
                            raise HTTPException(status_code=500, detail="메시지 전송에 실패했습니다.")
                            
                    except KeyError as e:
                        logger.error(f"필수 필드 누락: {str(e)}", exc_info=True)
                        continue
                        
                    except Exception as e:
                        logger.error(f"메시지 처리 중 오류 발생: {str(e)}", exc_info=True)
                        continue
        
        return {"status": "ok"}
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"웹훅 처리 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")

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

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 환경 변수와 설정을 확인합니다."""
    logger.info("서버 시작 - 환경 변수 확인")
    
    # 필수 환경 변수 확인
    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"),
        "PAGE_ACCESS_TOKEN": os.getenv("PAGE_ACCESS_TOKEN")
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        logger.error(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        raise RuntimeError(f"필수 환경 변수 누락: {', '.join(missing_vars)}")
    
    logger.info("모든 필수 환경 변수가 설정되어 있습니다.")
    
    # Google Credentials JSON 형식 확인
    try:
        google_creds = json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
        logger.info("Google Credentials JSON 형식이 유효합니다.")
    except json.JSONDecodeError as e:
        logger.error(f"Google Credentials JSON 형식이 잘못되었습니다: {str(e)}")
        raise RuntimeError("Google Credentials JSON 형식 오류")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 