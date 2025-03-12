import requests

def test_webhook_verification():
    url = "https://dotori-chat-bot-442938708244.asia-southeast1.run.app/webhook"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "dotori_chatbot_verify_token",
        "hub.challenge": "123456"
    }
    
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_webhook_verification() 