from sheets import get_kpop_data, get_size_data, get_faq_data
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from openai import OpenAI
import uvicorn
import logging
import os
import json
import requests

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DotoriChatbot:
    def __init__(self):
        self.kpop_data = []
        self.size_data = []
        self.faq_data = []
        self.load_data()
        
    def load_data(self):
        """데이터를 로드합니다."""
        try:
            logger.debug("K-pop 데이터 로드 시작")
            self.kpop_data = get_kpop_data()
            logger.info(f"K-pop 데이터 로드 완료: {len(self.kpop_data)}개")
        except Exception as e:
            logger.error(f"K-pop 데이터 로드 실패: {str(e)}", exc_info=True)
            self.kpop_data = []
            
        try:
            logger.debug("사이즈 데이터 로드 시작")
            self.size_data = get_size_data()
            logger.info(f"사이즈 데이터 로드 완료: {len(self.size_data)}개")
        except Exception as e:
            logger.error(f"사이즈 데이터 로드 실패: {str(e)}", exc_info=True)
            self.size_data = []
            
        try:
            logger.debug("FAQ 데이터 로드 시작")
            self.faq_data = get_faq_data()
            logger.info(f"FAQ 데이터 로드 완료: {len(self.faq_data)}개")
        except Exception as e:
            logger.error(f"FAQ 데이터 로드 실패: {str(e)}", exc_info=True)
            self.faq_data = []
            
        logger.debug(f"전체 데이터 상태 - K-pop: {len(self.kpop_data)}개, Size: {len(self.size_data)}개, FAQ: {len(self.faq_data)}개")
    
    def find_product(self, query):
        """상품 정보를 검색합니다."""
        for product in self.kpop_data:
            if not product:  # 빈 행 건너뛰기
                continue
            # 상품코드나 상품명으로 검색
            if query.lower() in product[0].lower() or query.lower() in product[1].lower():
                return {
                    "상품코드": product[0],
                    "상품명": product[1],
                    "출시일": product[2],
                    "배송예정일": product[3],
                    "구성품": product[4],
                    "특전": product[5],
                    "이미지": product[6] if len(product) > 6 else None
                }
        return None
    
    def find_size_info(self, query):
        """사이즈 정보를 검색합니다."""
        for size in self.size_data:
            if not size:  # 빈 행 건너뛰기
                continue
            if query.lower() in size[0].lower():  # 브랜드나 상품 카테고리로 검색
                return {
                    "브랜드": size[0],
                    "카테고리": size[1],
                    "사이즈표": size[2],
                    "참고사항": size[3] if len(size) > 3 else None
                }
        return None
    
    def find_faq(self, query):
        """FAQ를 검색합니다."""
        for faq in self.faq_data:
            if not faq:  # 빈 행 건너뛰기
                continue
            if query.lower() in faq[0].lower() or query.lower() in faq[1].lower():
                return {
                    "카테고리": faq[0],
                    "질문": faq[1],
                    "답변": faq[2]
                }
        return None
    
    def get_ai_response(self, user_message: str, context: dict = None) -> str:
        """OpenAI API를 사용하여 응답을 생성합니다."""
        try:
            # 시스템 메시지 구성
            system_message = """당신은 도토리몰의 친절한 고객상담 챗봇입니다.
            K-pop 굿즈, 의류 사이즈, 자주 묻는 질문 등에 대해 답변해주세요.
            답변은 한국어로 해주시고, 친절하고 공손한 톤을 유지해주세요."""
            
            # 컨텍스트가 있는 경우 시스템 메시지에 추가
            if context:
                system_message += f"\n\n참고할 정보:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            logger.debug(f"Sending to OpenAI - messages: {messages}")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            logger.info(f"AI response generated: {ai_response}")
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}", exc_info=True)
            return None
    
    def process_message(self, message):
        """메시지를 처리하고 응답을 생성합니다."""
        try:
            logger.info(f"메시지 처리 시작: {message}")
            
            # 기본 인사 처리
            if any(greeting in message.lower() for greeting in ["안녕", "hi", "hello", "ㅎㅇ"]):
                return self.get_ai_response(message)
            
            # 데이터 상태 확인
            logger.debug(f"현재 데이터 상태 - K-pop: {len(self.kpop_data)}개, Size: {len(self.size_data)}개, FAQ: {len(self.faq_data)}개")
            
            context = {}
            
            # 상품 검색
            logger.debug("상품 검색 시작")
            product = self.find_product(message)
            if product:
                logger.info(f"상품 정보 찾음: {product}")
                context["product"] = product
            
            # 사이즈 정보 검색
            logger.debug("사이즈 정보 검색 시작")
            size = self.find_size_info(message)
            if size:
                logger.info(f"사이즈 정보 찾음: {size}")
                context["size"] = size
            
            # FAQ 검색
            logger.debug("FAQ 검색 시작")
            faq = self.find_faq(message)
            if faq:
                logger.info(f"FAQ 찾음: {faq}")
                context["faq"] = faq
            
            # AI 응답 생성
            if context:
                return self.get_ai_response(message, context)
            else:
                return self.get_ai_response(message)
            
        except Exception as e:
            logger.error(f"메시지 처리 중 오류 발생: {str(e)}", exc_info=True)
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

# FastAPI 앱 초기화
app = FastAPI()

# 챗봇 인스턴스 생성
chatbot = DotoriChatbot()

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
        
        logger.info(f"Sending message to {recipient_id}: {message_text}")
        response = requests.post(url, params=params, json=data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.status_code} - {response.text}")
            return False
            
        logger.info(f"Message sent successfully to {recipient_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        return False

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
    """페이스북 메시지 수신 및 처리"""
    try:
        # 요청 바디 로깅
        body = await request.json()
        logger.info(f"Received webhook data: {json.dumps(body, indent=2, ensure_ascii=False)}")
        
        # 페이지 이벤트가 아닌 경우 처리
        if body.get("object") != "page":
            logger.warning(f"Received non-page event: {body.get('object')}")
            return {"status": "error", "message": "Invalid event type"}
        
        # 엔트리 처리
        entries = body.get("entry", [])
        logger.info(f"Processing {len(entries)} entries")
        
        for entry in entries:
            logger.debug(f"Processing entry: {entry}")
            messaging = entry.get("messaging", [])
            
            for message_event in messaging:
                logger.debug(f"Processing message event: {message_event}")
                
                sender_id = message_event.get("sender", {}).get("id")
                if not sender_id:
                    logger.error("No sender ID found in message event")
                    continue
                    
                message = message_event.get("message", {}).get("text")
                if not message:
                    logger.warning(f"No message text found for sender {sender_id}")
                    continue
                
                logger.info(f"Processing message from {sender_id}: {message}")
                
                try:
                    # 챗봇 응답 생성
                    response = chatbot.process_message(message)
                    if response:
                        # 응답 전송
                        success = send_message(sender_id, response)
                        if not success:
                            logger.error(f"Failed to send message to {sender_id}")
                    else:
                        logger.error("No response generated from chatbot")
                        send_message(sender_id, "죄송합니다. 응답을 생성하는 중에 문제가 발생했습니다.")
                        
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}", exc_info=True)
                    send_message(sender_id, "죄송합니다. 메시지 처리 중에 오류가 발생했습니다.")
        
        return {"status": "success"}
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}", exc_info=True)
        return {"status": "error", "message": "Invalid JSON format"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return {"status": "error", "message": "Internal server error"}

if __name__ == "__main__":
    if not PAGE_ACCESS_TOKEN:
        logger.error("PAGE_ACCESS_TOKEN is not set!")
        exit(1)
        
    # 서버 실행
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting chatbot server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port) 