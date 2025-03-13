from sheets import get_kpop_data, get_size_data, get_faq_data
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import uvicorn
import logging
import os
import json
import requests
import time

# 공식 LangChain
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from sheets import get_kpop_data, get_size_data, get_faq_data


# (1) env 파일 로드
load_dotenv(dotenv_path=".env.local", override=True)

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경변수 체크
required_env_vars = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),  # 여기로 변경
    "PAGE_ACCESS_TOKEN": os.getenv("PAGE_ACCESS_TOKEN"),
    "VERIFY_TOKEN": os.getenv("VERIFY_TOKEN")
}
for var_name, var_value in required_env_vars.items():
    if not var_value:
        logger.error(f"{var_name}가 설정되지 않았습니다.")
        raise ValueError(f"{var_name}가 필요합니다.")
    else:
        logger.info(f"{var_name} 설정 확인 완료")


class DotoriChatbot:
    def __init__(self):
        self.kpop_data = []
        self.size_data = []
        self.faq_data = []

        # LangChain ChatOpenAI 객체 생성
        self.chat_model = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )

        # 구글 시트, 페북 토큰 등 체크
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.error("GOOGLE_APPLICATION_CREDENTIALS가 설정되지 않았습니다.")
            raise ValueError("Google Sheets 자격 증명이 필요합니다.")

        if not os.getenv("PAGE_ACCESS_TOKEN"):
            logger.error("PAGE_ACCESS_TOKEN이 설정되지 않았습니다.")
            raise ValueError("Facebook PAGE_ACCESS_TOKEN이 필요합니다.")

        # 데이터 로드
        self.load_data()

    def load_data(self):
        """구글 시트에서 데이터 로드"""
        success = False
        retry_count = 0
        max_retries = 3
        while not success and retry_count < max_retries:
            try:
                logger.debug(f"데이터 로드 시도 #{retry_count + 1}")
                self.kpop_data = get_kpop_data() or []
                logger.info(f"K-pop 데이터 로드 완료: {len(self.kpop_data)}개")

                self.size_data = get_size_data() or []
                logger.info(f"사이즈 데이터 로드 완료: {len(self.size_data)}개")

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
        for product in self.kpop_data:
            if not product:
                continue
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
        for size in self.size_data:
            if not size:
                continue
            if query.lower() in size[0].lower():
                return {
                    "브랜드": size[0],
                    "카테고리": size[1],
                    "사이즈표": size[2],
                    "참고사항": size[3] if len(size) > 3 else None
                }
        return None

    def find_faq(self, query):
        for faq in self.faq_data:
            if not faq:
                continue
            if query.lower() in faq[0].lower() or query.lower() in faq[1].lower():
                return {
                    "카테고리": faq[0],
                    "질문": faq[1],
                    "답변": faq[2]
                }
        return None

    def get_ai_response(self, user_message, context=None):
        """LangChain ChatOpenAI로 메시지 생성"""
        try:
            if not user_message:
                return "죄송합니다. 메시지를 이해하지 못했습니다."

            system_content = """당신은 도토리몰의 친절한 고객상담 챗봇입니다.
K-pop 굿즈, 의류 사이즈, 자주 묻는 질문 등에 대해 답변해주세요.
답변은 한국어로 해주시고, 친절하고 공손한 톤을 유지해주세요.
"""

            if context:
                system_content += f"\n\n참고할 정보:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

            system_msg = SystemMessage(content=system_content)
            user_msg = HumanMessage(content=user_message)

            messages = [system_msg, user_msg]

            logger.debug(f"ChatOpenAI에 보낼 메시지: {[m.content for m in messages]}")

            # ----- 수정 부분 시작 -----
            # 기존: response = self.chat_model(messages)
            # 수정: predict_messages() 사용
            response = self.chat_model.predict_messages(messages)
            ai_response = response.content
            # ----- 수정 부분 끝 -----

            logger.info(f"AI 응답 생성 완료: {ai_response}")
            return ai_response

        except Exception as e:
            logger.error(f"AI 응답 생성 중 오류 발생: {str(e)}", exc_info=True)
            return "죄송합니다. 일시적인 오류가 발생했습니다."

    def process_message(self, message):
        """사용자 메시지를 처리하고 최종 답변"""
        if not message:
            logger.warning("빈 메시지")
            return "죄송합니다. 메시지를 이해하지 못했습니다."

        try:
            logger.info(f"메시지 처리 시작: {message}")

            # 혹시 데이터 비었으면 재로드
            if not any([self.kpop_data, self.size_data, self.faq_data]):
                logger.warning("데이터 비어있어 재로드 시도")
                self.load_data()

            context = {}

            # 간단한 인사 처리
            if any(greeting in message.lower() for greeting in ["안녕", "hello", "hi"]):
                return self.get_ai_response(message)

            # 상품 검색
            try:
                product = self.find_product(message)
                if product:
                    context["product"] = product
            except Exception as e:
                logger.error(f"상품 검색 중 오류: {e}", exc_info=True)

            # 사이즈 검색
            try:
                size = self.find_size_info(message)
                if size:
                    context["size"] = size
            except Exception as e:
                logger.error(f"사이즈 검색 중 오류: {e}", exc_info=True)

            # FAQ 검색
            try:
                faq = self.find_faq(message)
                if faq:
                    context["faq"] = faq
            except Exception as e:
                logger.error(f"FAQ 검색 중 오류: {e}", exc_info=True)

            return self.get_ai_response(message, context if context else None)

        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {e}", exc_info=True)
            return "죄송합니다. 일시적인 오류가 발생했습니다."


# FastAPI 앱
app = FastAPI(title="도토리몰 챗봇 API", version="1.0.0")
chatbot = DotoriChatbot()

@app.post("/webhook")
async def webhook(request: Request):
    """페이스북 메시지 수신"""
    logger.info("=== /webhook called ===")
    try:
        body = await request.json()
        logger.info(f"Webhook body: {body}")

        if body.get("object") == "page":
            for entry in body.get("entry", []):
                for messaging in entry.get("messaging", []):
                    sender_id = messaging["sender"]["id"]
                    message_text = messaging.get("message", {}).get("text", "")
                    logger.info(f"Sender: {sender_id}, Message Text: {message_text}")

                    # AI 응답
                    response_text = chatbot.process_message(message_text)

                    # 페이스북 전송
                    send_message(sender_id, response_text)

        return {"status": "ok"}
    except Exception as e:
        logger.error("Error processing webhook", exc_info=True)
        return {"status": "error", "message": str(e)}


def send_message(recipient_id, text):
    """메신저 전송"""
    url = f"https://graph.facebook.com/v11.0/me/messages?access_token={os.getenv('PAGE_ACCESS_TOKEN')}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    r = requests.post(url, headers=headers, json=data)
    logger.info(f"Sent message to {recipient_id}, status={r.status_code}")


@app.get("/")
@app.get("/index.html")
async def root():
    return {"status": "online", "message": "도토리몰 챗봇 API 실행 중"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    """페이스북 웹훅 검증"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    logger.info(f"Webhook verify - mode={mode}, token={token}, challenge={challenge}")

    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
        if challenge:
            logger.info("웹훅 검증 성공")
            return int(challenge)
        else:
            return "challenge missing"
    else:
        logger.error("검증 실패 - 잘못된 토큰/모드")
        return "invalid token or mode"


# 전역 예외
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("=== 전역 예외 처리 ===")
    logger.error(f"URL: {request.url}")
    logger.error(f"예외: {str(exc)}", exc_info=True)
    return {"status": "error", "message": "Internal server error"}


def verify_page_connection():
    """페이스북 페이지 연결 상태 체크"""
    try:
        url = "https://graph.facebook.com/v18.0/me"
        params = {"access_token": os.getenv("PAGE_ACCESS_TOKEN"), "fields": "id,name,category"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f"Page connected: {data}")
            return True, data
        else:
            logger.error(f"Page connect fail: {resp.status_code}, {resp.text}")
            return False, resp.json()
    except Exception as e:
        logger.error(f"페이지 연결 오류: {e}", exc_info=True)
        return False, None


@app.get("/check-page")
async def check_page_endpoint():
    """연결 상태 확인"""
    ok, data = verify_page_connection()
    if ok:
        return {"status": "success", "data": data}
    else:
        return {"status": "error", "data": data}


if __name__ == "__main__":
    ok, data = verify_page_connection()
    if not ok:
        logger.error("페이지 연결 실패!")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
