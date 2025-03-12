import os
from dotenv import load_dotenv
import urllib3
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

def test_openai_api():
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found")
        return False
    
    logger.info(f"API 키 확인됨: {api_key[:5]}...")
    
    # HTTP 클라이언트 초기화
    http = urllib3.PoolManager()
    
    # 테스트 메시지
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "안녕하세요"}
    ]
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info("OpenAI API 호출 시도...")
        response = http.request(
            'POST',
            'https://api.openai.com/v1/chat/completions',
            body=json.dumps(data).encode('utf-8'),
            headers=headers,
            timeout=10.0
        )
        
        logger.info(f"응답 상태 코드: {response.status}")
        response_data = json.loads(response.data.decode('utf-8'))
        
        if response.status == 200:
            message = response_data["choices"][0]["message"]["content"]
            logger.info(f"성공적인 응답: {message}")
            return True
        else:
            logger.error(f"API 오류: {response_data}")
            return False
            
    except Exception as e:
        logger.error(f"예외 발생: {e}")
        return False

if __name__ == "__main__":
    result = test_openai_api()
    print(f"\n테스트 결과: {'성공' if result else '실패'}") 