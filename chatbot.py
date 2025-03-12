from sheets import get_kpop_data, get_size_data, get_faq_data
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import uvicorn
import logging
import os
import json
import requests
import time
from langchain_community.chat_models import ChatOpenAI
import openai

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 환경 변수 검증
required_env_vars = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "GOOGLE_APPLICATION_CREDENTIALS_JSON": os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"),
    "PAGE_ACCESS_TOKEN": os.getenv("PAGE_ACCESS_TOKEN"),
    "VERIFY_TOKEN": os.getenv("VERIFY_TOKEN")
}

for var_name, var_value in required_env_vars.items():
    if not var_value:
        logger.error(f"{var_name}가 설정되지 않았습니다.")
        raise ValueError(f"{var_name}가 필요합니다.")
    else:
        logger.info(f"{var_name} 설정 확인 완료")

# 클라이언트 초기화 상태를 나타낼 변수
client = None

# OpenAI 클라이언트 초기화
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
        raise ValueError("OPENAI_API_KEY가 필요합니다.")
        
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "안녕?"}],
        max_tokens=50,
        temperature=0.7
    )
    chatbot_answer = response.choices[0].message["content"]
    logger.info(f"OpenAI 클라이언트가 성공적으로 초기화되었습니다. 응답: {chatbot_answer}")
    
    client = True  # 오류 없이 초기화되었음을 표시

except Exception as e:
    logger.error(f"OpenAI 클라이언트 초기화 중 오류 발생: {str(e)}", exc_info=True)
    client = None

class DotoriChatbot:
    def __init__(self):
        self.kpop_data = []
        self.size_data = []
        self.faq_data = []
        
        # OpenAI 클라이언트 확인
        if client is None:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            raise RuntimeError("OpenAI 클라이언트 초기화 실패")
            
        # Google Sheets 자격 증명 확인
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
            logger.error("GOOGLE_APPLICATION_CREDENTIALS_JSON가 설정되지 않았습니다.")
            raise ValueError("Google Sheets 자격 증명이 필요합니다.")
            
        # Facebook 페이지 액세스 토큰 확인
        if not os.getenv("PAGE_ACCESS_TOKEN"):
            logger.error("PAGE_ACCESS_TOKEN이 설정되지 않았습니다.")
            raise ValueError("Facebook 페이지 액세스 토큰이 필요합니다.")
            
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
            
            response = openai.ChatCompletion.create(
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
app = FastAPI(
    title="도토리몰 챗봇 API",
    description="Facebook Messenger를 위한 도토리몰 챗봇 API",
    version="1.0.0"
)

# 챗봇 인스턴스 생성
chatbot = DotoriChatbot()

# OpenAI API 설정
chatbot_langchain = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7
)

@app.post("/webhook")
async def webhook(request: Request):
    """페이스북 메시지 수신 및 처리"""
    logger.info("=== /webhook called ===")

    try:
        body = await request.json()
        logger.info("Webhook body: %s", body)

        # 메시지 처리 로직
        if body.get("object") == "page":
            logger.info("Detected object=page, start processing entries.")
            for entry in body.get("entry", []):
                logger.info("Processing entry: %s", entry)

                for messaging in entry.get("messaging", []):
                    logger.info("Processing messaging: %s", messaging)

                    sender_id = messaging["sender"]["id"]
                    message_text = messaging.get("message", {}).get("text", "")
                    logger.info("Sender: %s, Message Text: %s", sender_id, message_text)

                    # OpenAI API를 통해 응답 생성 (langchain)
                    try:
                        logger.debug("Calling chatbot_langchain with message_text.")
                        response = chatbot_langchain(message_text)
                        logger.debug("chatbot_langchain response: %s", response)
                    except Exception as e:
                        logger.error("Error in chatbot_langchain call: %s", e, exc_info=True)
                        return {"status": "error", "message": str(e)}

                    # 메시지 전송
                    try:
                        logger.debug("Calling send_message to %s", sender_id)
                        send_message(sender_id, response)
                        logger.debug("send_message complete.")
                    except Exception as e:
                        logger.error("Error sending message: %s", e, exc_info=True)
                        return {"status": "error", "message": str(e)}

            logger.info("All entries processed.")
        else:
            logger.info("No 'page' object in request, ignoring.")

        logger.info("=== /webhook finished successfully ===")
        return {"status": "ok"}

    except Exception as e:
        logger.error("=== Error processing webhook ===", exc_info=True)
        return {"status": "error", "message": str(e)}

def send_message(recipient_id, message_text):
    """페이스북 메신저로 메시지를 전송합니다."""
    url = f"https://graph.facebook.com/v11.0/me/messages?access_token={os.getenv('PAGE_ACCESS_TOKEN')}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, headers=headers, json=data)
    logger.info(f"Sent message to {recipient_id}: {response.status_code}")

@app.get("/")
@app.get("/index.html")
async def root():
    """API 루트 엔드포인트"""
    return {
        "status": "online",
        "message": "도토리몰 챗봇 API가 실행 중입니다.",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API 상태 확인"},
            {"path": "/webhook", "method": "GET", "description": "페이스북 웹훅 검증"},
            {"path": "/webhook", "method": "POST", "description": "페이스북 메시지 수신"},
            {"path": "/check-page", "method": "GET", "description": "페이지 연결 상태 확인"}
        ]
    }

@app.get("/webhook")
async def verify_webhook(request: Request):
    """페이스북 웹훅 검증"""
    try:
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        logger.info(f"웹훅 검증 시도 - mode: {mode}, token: {token}, challenge: {challenge}")
        
        if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
            if challenge:
                logger.info("웹훅 검증 성공")
                return int(challenge)  # 문자열을 정수로 변환
            else:
                logger.error("challenge 값이 없음")
                return "challenge missing"
        else:
            logger.error("검증 실패 - 잘못된 토큰 또는 모드")
            return "invalid token or mode"
            
    except Exception as e:
        logger.error(f"웹훅 검증 중 오류: {str(e)}", exc_info=True)
        return "verification error"

# FastAPI 예외 핸들러 추가
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("=== 전역 예외 처리 ===")
    logger.error(f"요청 URL: {request.url}")
    logger.error(f"예외 타입: {type(exc)}")
    logger.error(f"예외 메시지: {str(exc)}")
    logger.error("스택 트레이스:", exc_info=True)
    return {"status": "error", "message": "Internal server error"}

def verify_page_connection():
    """페이스북 페이지 연결 상태를 확인합니다."""
    try:
        url = "https://graph.facebook.com/v18.0/me"
        params = {
            "access_token": os.getenv("PAGE_ACCESS_TOKEN"),
            "fields": "id,name,category"
        }
        headers = {
            "Accept": "application/json"
        }
        
        logger.info("=== 페이지 연결 상태 확인 시작 ===")
        logger.info(f"URL: {url}")
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        logger.info(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            logger.info(f"Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            if response.status_code == 200:
                logger.info("페이지 연결 성공!")
                logger.info(f"페이지 이름: {response_data.get('name')}")
                logger.info(f"페이지 ID: {response_data.get('id')}")
                logger.info(f"페이지 카테고리: {response_data.get('category')}")
                return True, response_data
            else:
                logger.error(f"페이지 연결 실패 - HTTP {response.status_code}")
                if 'error' in response_data:
                    error = response_data['error']
                    logger.error(f"오류 메시지: {error.get('message')}")
                    logger.error(f"오류 타입: {error.get('type')}")
                    logger.error(f"오류 코드: {error.get('code')}")
                return False, response_data
                
        except json.JSONDecodeError as e:
            logger.error(f"응답 파싱 오류: {str(e)}")
            logger.error(f"원본 응답: {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"페이지 연결 확인 중 오류 발생: {str(e)}", exc_info=True)
        return False, None

@app.get("/check-page")
@app.get("/check-page/")
async def check_page_connection():
    """페이지 연결 상태를 확인하는 엔드포인트"""
    try:
        success, data = verify_page_connection()
        if success:
            return {
                "status": "success",
                "message": "페이지가 정상적으로 연결되어 있습니다.",
                "page_info": data
            }
        else:
            return {
                "status": "error",
                "message": "페이지 연결에 문제가 있습니다.",
                "error_info": data
            }
    except Exception as e:
        logger.error("페이지 연결 확인 중 오류", exc_info=True)
        return {
            "status": "error",
            "message": f"페이지 연결 확인 중 오류 발생: {str(e)}"
        }

if __name__ == "__main__":
    if not os.getenv("PAGE_ACCESS_TOKEN"):
        logger.error("PAGE_ACCESS_TOKEN is not set!")
        exit(1)
        
    # 서버 시작 시 페이지 연결 상태 확인
    logger.info("페이지 연결 상태 확인 중...")
    success, data = verify_page_connection()
    if not success:
        logger.error("페이지 연결에 문제가 있습니다!")
    
    # 서버 실행
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting chatbot server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
