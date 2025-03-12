import requests
import os
from dotenv import load_dotenv
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def test_facebook_webhook():
    """페이스북 웹훅 테스트"""
    results = {}
    
    # 환경 변수 확인
    page_access_token = os.getenv("PAGE_ACCESS_TOKEN")
    if not page_access_token:
        logger.error("PAGE_ACCESS_TOKEN이 설정되지 않았습니다.")
        return {"webhook": False}

    # 테스트 메시지 전송
    try:
        url = "https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": page_access_token}
        headers = {"Content-Type": "application/json"}
        
        # 테스트용 메시지 (실제 PSID가 필요합니다)
        data = {
            "recipient": {"id": "TEST_USER_ID"},  # 실제 테스트 시에는 유효한 PSID로 교체 필요
            "message": {"text": "테스트 메시지입니다."}
        }
        
        logger.info("페이스북 API 테스트 중...")
        response = requests.post(url, params=params, json=data)
        
        if response.status_code == 200:
            logger.info("페이스북 API 연동 테스트 성공")
            results['webhook'] = True
        else:
            logger.error(f"페이스북 API 오류: {response.text}")
            results['webhook'] = False
            
    except Exception as e:
        logger.error(f"페이스북 API 테스트 중 오류 발생: {e}")
        results['webhook'] = False
    
    return results

def test_page_access_token():
    """페이지 액세스 토큰을 테스트합니다."""
    PAGE_ACCESS_TOKEN = "EAAGr57aUTyUBOZC3ZCAR3W8rGMXsWB07wyZBfn0WgTbNnt8aNYg0FfxQU6zl6XkeWH6aKnmBgPgJ0Myl6YvlrZAZBu2B5Y1PQ0ASHFFz9GAd2LwrQeZAZAjidZBKZCSHFDiA8FamekQ4LxJDGs3ItV4dyAQs3Cn9RzagRZChvR3Qbz6jDrZBV33NuORH4mgCnVmoUSWxqECZBcL8ZC8ZBcqAhG0gZDZD"
    
    url = "https://graph.facebook.com/v18.0/me"
    params = {
        "access_token": PAGE_ACCESS_TOKEN,
        "fields": "id,name,category"
    }
    headers = {
        "Accept": "application/json"
    }
    
    print("=== 페이지 연결 테스트 시작 ===")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {str(e)}")
            print(f"원본 응답: {response.text}")
            
    except Exception as e:
        print(f"요청 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    results = test_facebook_webhook()
    print("\n=== 페이스북 웹훅 테스트 결과 ===")
    for test, success in results.items():
        print(f"{test.upper()}: {'성공 ✓' if success else '실패 ✗'}")
    test_page_access_token() 