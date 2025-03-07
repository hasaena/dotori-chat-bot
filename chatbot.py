from sheets import get_kpop_data, get_size_data, get_faq_data
from fastapi import FastAPI, Request, HTTPException
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

# 환경 변수 검증
required_env_vars = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "GOOGLE_APPLICATION_CREDENTIALS_JSON": os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"),
    "PAGE_ACCESS_TOKEN": os.getenv("PAGE_ACCESS_TOKEN")
}

for var_name, var_value in required_env_vars.items():
    if not var_value:
        logger.error(f"{var_name}가 설정되지 않았습니다.")
        raise ValueError(f"{var_name}가 필요합니다.")
    else:
        logger.info(f"{var_name} 설정 확인 완료")

# OpenAI 클라이언트 초기화
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
        raise ValueError("OPENAI_API_KEY가 필요합니다.")
        
    client = OpenAI()  # 환경 변수에서 자동으로 API 키를 가져옵니다
    
    # 클라이언트 테스트
    test_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5
    )
    logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
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
PAGE_ACCESS_TOKEN = "EAAGr57aUTyUBOZC3ZCAR3W8rGMXsWB07wyZBfn0WgTbNnt8aNYg0FfxQU6zl6XkeWH6aKnmBgPgJ0Myl6YvlrZAZBu2B5Y1PQ0ASHFFz9GAd2LwrQeZAZAjidZBKZCSHFDiA8FamekQ4LxJDGs3ItV4dyAQs3Cn9RzagRZChvR3Qbz6jDrZBV33NuORH4mgCnVmoUSWxqECZBcL8ZC8ZBcqAhG0gZDZD"

def send_message(recipient_id: str, message_text: str):
    """페이스북 메신저로 메시지를 전송합니다."""
    try:
        url = f"https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": PAGE_ACCESS_TOKEN}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        # API 호출 전 상세 로깅
        logger.info("=== Facebook API 호출 시작 ===")
        logger.info(f"URL: {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Parameters: {params}")
        logger.info(f"Request Data: {json.dumps(data, ensure_ascii=False)}")
        
        # API 호출 시도
        try:
            response = requests.post(
                url, 
                params=params, 
                json=data, 
                headers=headers,
                timeout=10
            )
            
            # 응답 상세 로깅
            logger.info("=== Facebook API 응답 ===")
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                logger.info(f"Response Body: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                
                if response.status_code != 200:
                    logger.error(f"=== Facebook API HTTP 오류 ===")
                    logger.error(f"Status Code: {response.status_code}")
                    logger.error(f"Error Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    return False
                    
                if 'error' in response_data:
                    error_data = response_data['error']
                    logger.error(f"=== Facebook API 오류 상세 ===")
                    logger.error(f"Error Message: {error_data.get('message')}")
                    logger.error(f"Error Type: {error_data.get('type')}")
                    logger.error(f"Error Code: {error_data.get('code')}")
                    logger.error(f"Error Subcode: {error_data.get('error_subcode')}")
                    logger.error(f"FBTrace ID: {error_data.get('fbtrace_id')}")
                    return False
                    
                logger.info("=== Facebook API 호출 성공 ===")
                return True
                
            except json.JSONDecodeError as e:
                logger.error("=== Facebook API 응답 파싱 오류 ===")
                logger.error(f"Error: {str(e)}")
                logger.error(f"Raw Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("=== Facebook API 타임아웃 ===")
            logger.error(f"Timeout after 10 seconds")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error("=== Facebook API 연결 오류 ===")
            logger.error(f"Connection Error: {str(e)}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error("=== Facebook API 요청 오류 ===")
            logger.error(f"Request Error: {str(e)}")
            return False
            
    except Exception as e:
        logger.error("=== 예상치 못한 오류 ===")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error Message: {str(e)}")
        logger.error("Stack Trace:", exc_info=True)
        return False

@app.get("/webhook")
async def verify_webhook(request: Request):
    """페이스북 웹훅 검증"""
    try:
        # 필수 파라미터 추출
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        logger.info(f"웹훅 검증 시도 - mode: {mode}, token: {token}, challenge: {challenge}")
        
        # 검증 토큰 확인
        if mode == "subscribe" and token == VERIFY_TOKEN:
            if challenge:
                logger.info("웹훅 검증 성공")
                return int(challenge)  # 문자열을 정수로 변환하여 반환
            else:
                logger.error("challenge 값이 없음")
                return "challenge missing"
        else:
            logger.error(f"검증 실패 - 잘못된 토큰 또는 모드")
            return "invalid token or mode"
            
    except Exception as e:
        logger.error(f"웹훅 검증 중 오류: {str(e)}", exc_info=True)
        return "verification error"

@app.post("/webhook")
async def webhook(request: Request):
    """페이스북 메시지 수신 및 처리"""
    try:
        # 요청 전체 로깅
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        headers = dict(request.headers)
        
        logger.info("=== 웹훅 요청 시작 ===")
        logger.info(f"Headers: {json.dumps(headers, indent=2)}")
        logger.info(f"Raw Body: {body_str}")
        
        try:
            body = json.loads(body_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {str(e)}")
            logger.error(f"문제의 데이터: {body_str}")
            return {"status": "ok"}
            
        logger.info(f"Parsed Body: {json.dumps(body, indent=2)}")
        
        # 페이지 이벤트 검증
        if body.get("object") != "page":
            logger.warning(f"지원하지 않는 이벤트 타입: {body.get('object')}")
            return {"status": "ok"}
            
        try:
            # 엔트리 처리
            entries = body.get("entry", [])
            logger.info(f"처리할 엔트리 수: {len(entries)}")
            
            for entry_idx, entry in enumerate(entries):
                logger.info(f"=== 엔트리 {entry_idx + 1} 처리 시작 ===")
                logger.info(f"엔트리 데이터: {json.dumps(entry, indent=2)}")
                
                messaging_events = entry.get("messaging", [])
                logger.info(f"메시징 이벤트 수: {len(messaging_events)}")
                
                for event_idx, event in enumerate(messaging_events):
                    try:
                        logger.info(f"=== 이벤트 {event_idx + 1} 처리 시작 ===")
                        logger.info(f"이벤트 데이터: {json.dumps(event, indent=2)}")
                        
                        sender_id = event.get("sender", {}).get("id")
                        message = event.get("message", {})
                        
                        if not sender_id or not message:
                            logger.warning("sender_id 또는 message 누락")
                            logger.warning(f"sender_id: {sender_id}")
                            logger.warning(f"message: {message}")
                            continue
                            
                        message_text = message.get("text", "").strip()
                        if not message_text:
                            logger.warning("텍스트 메시지 아님")
                            continue
                            
                        logger.info(f"메시지 처리 - 발신자: {sender_id}, 내용: {message_text}")
                        
                        try:
                            # 챗봇 응답 생성
                            response = chatbot.process_message(message_text)
                            if not response:
                                logger.error("챗봇이 빈 응답을 반환")
                                continue
                                
                            logger.info(f"생성된 응답: {response}")
                            
                            # 응답 전송
                            send_result = send_message(sender_id, response)
                            if send_result:
                                logger.info("응답 전송 성공")
                            else:
                                logger.error("응답 전송 실패")
                                
                        except Exception as e:
                            logger.error("챗봇 처리 중 오류", exc_info=True)
                            logger.error(f"오류 상세: {str(e)}")
                            continue
                            
                    except Exception as e:
                        logger.error("이벤트 처리 중 오류", exc_info=True)
                        logger.error(f"오류 상세: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error("엔트리 처리 중 오류", exc_info=True)
            logger.error(f"오류 상세: {str(e)}")
            
        logger.info("=== 웹훅 처리 완료 ===")
        return {"status": "ok"}
        
    except Exception as e:
        logger.error("=== 웹훅 처리 중 치명적 오류 ===", exc_info=True)
        logger.error(f"오류 상세: {str(e)}")
        # 스택 트레이스 상세 출력
        import traceback
        logger.error(f"스택 트레이스:\n{''.join(traceback.format_exc())}")
        return {"status": "ok"}

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
            "access_token": PAGE_ACCESS_TOKEN,
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
                logger.info(f"페이지 연결 성공!")
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
async def check_page_connection():
    """페이지 연결 상태를 확인하는 엔드포인트"""
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

if __name__ == "__main__":
    if not PAGE_ACCESS_TOKEN:
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