import requests
import json

def test_send_message():
    PAGE_ACCESS_TOKEN = "EAAGr57aUTyUBO2zxcthfJX2o9LR2ykmAqq3Ddi5jt0fYjuQ7uXowm4LZAYkbEG3x9UnCkKnVUWurSLZBgTqUMtjPJV5eSGPPsgcDDBWZCyPMnntXJC0VAnz4XrVGXod38ky9Xq2y5dp96JvFdP3gABHswumYPhfW6PP8lYZAwxIPUZA8hXbOWDRarGRXcz2PPM1DHFncXyelv6TKgZCgZDZD"
    
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 테스트 메시지 데이터
    data = {
        "recipient": {"id": "7121549694532435"},  # 메시지를 보낸 사용자 ID
        "message": {"text": "네, 메시지 잘 받았습니다! 테스트 응답입니다."}
    }
    
    try:
        print("=== 메시지 전송 테스트 시작 ===")
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Parameters: {params}")
        print(f"Request Data: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(url, params=params, json=data, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_send_message() 