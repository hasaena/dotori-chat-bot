from sheets import get_kpop_data, get_size_data, get_faq_data
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from openai import OpenAI
import uvicorn
import logging
import os
import json
import requests
import time

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
except Exception as e:
    logger.error(f"OpenAI 클라이언트 초기화 중 오류 발생: {str(e)}")
    client = None

class DotoriChatbot:
    def __init__(self):
        self.kpop_data = []
        self.size_data = []
        self.faq_data = []
        
        # OpenAI API 키 확인
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
            raise ValueError("OPENAI_API_KEY가 필요합니다.")
            
        # Google Sheets 자격 증명 확인
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
            logger.error("GOOGLE_APPLICATION_CREDENTIALS_JSON가 설정되지 않았습니다.")
            raise ValueError("Google Sheets 자격 증명이 필요합니다.")
            
        # Facebook 페이지 액세스 토큰 확인
        if not os.getenv("PAGE_ACCESS_TOKEN"):
            logger.error("PAGE_ACCESS_TOKEN이 설정되지 않았습니다.")
            raise ValueError("Facebook 페이지 액세스 토큰이 필요합니다.")
            
        # OpenAI 클라이언트 확인
        if client is None:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            raise RuntimeError("OpenAI 클라이언트 초기화 실패")
            
        self.load_data()
        
    def load_data(self):
        """데이터를 로드합니다."""
        success = False
        retry_count = 0
        max_retries = 3
        
        while not success and retry_count < max_retries:
            try:
                logger.debug(f"데이터 로드 시도 #{retry_count + 1}")
                
                # K-pop 데이터 로드
                self.kpop_data = get_kpop_data() or []
                logger.info(f"K-pop 데이터 로드 완료: {len(self.kpop_data)}개")
                
                # 사이즈 데이터 로드
                self.size_data = get_size_data() or []
                logger.info(f"사이즈 데이터 로드 완료: {len(self.size_data)}개")
                
                # FAQ 데이터 로드
                self.faq_data = get_faq_data() or []
                logger.info(f"FAQ 데이터 로드 완료: {len(self.faq_data)}개")
                
                success = True
                logger.info("모든 데이터 로드 완료")
                
            except Exception as e:
                retry_count += 1
                logger.error(f"데이터 로드 실패 (시도 #{retry_count}): {str(e)}", exc_info=True)
                if retry_count < max_retries:
                    logger.info(f"{5 * retry_count}초 후 재시도...")
                    time.sleep(5 * retry_count)
                else:
                    logger.error("최대 재시도 횟수 초과")
                    raise
                    
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
            if not user_message:
                logger.warning("빈 메시지가 전달되었습니다.")
                return "죄송합니다. 메시지를 이해하지 못했습니다."
                
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
            
            logger.debug(f"OpenAI API 호출 - messages: {messages}")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            logger.info(f"AI 응답 생성 완료: {ai_response}")
            return ai_response
            
        except Exception as e:
            logger.error(f"AI 응답 생성 중 오류 발생: {str(e)}", exc_info=True)
            return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            
    def process_message(self, message):
        """메시지를 처리하고 응답을 생성합니다."""
        if not message:
            logger.warning("빈 메시지가 전달되었습니다.")
            return "죄송합니다. 메시지를 이해하지 못했습니다."
            
        try:
            logger.info(f"메시지 처리 시작: {message}")
            
            # 데이터가 비어있는 경우 재로드 시도
            if not any([self.kpop_data, self.size_data, self.faq_data]):
                logger.warning("데이터가 비어있어 재로드를 시도합니다.")
                self.load_data()
            
            # 기본 인사 처리
            if any(greeting in message.lower() for greeting in ["안녕", "hi", "hello", "ㅎㅇ"]):
                return self.get_ai_response(message)
            
            context = {}
            
            # 상품 검색
            try:
                product = self.find_product(message)
                if product:
                    logger.info(f"상품 정보 찾음: {product}")
                    context["product"] = product
            except Exception as e:
                logger.error(f"상품 검색 중 오류 발생: {str(e)}", exc_info=True)
            
            # 사이즈 정보 검색
            try:
                size = self.find_size_info(message)
                if size:
                    logger.info(f"사이즈 정보 찾음: {size}")
                    context["size"] = size
            except Exception as e:
                logger.error(f"사이즈 정보 검색 중 오류 발생: {str(e)}", exc_info=True)
            
            # FAQ 검색
            try:
                faq = self.find_faq(message)
                if faq:
                    logger.info(f"FAQ 찾음: {faq}")
                    context["faq"] = faq
            except Exception as e:
                logger.error(f"FAQ 검색 중 오류 발생: {str(e)}", exc_info=True)
            
            # AI 응답 생성
            return self.get_ai_response(message, context if context else None)
            
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