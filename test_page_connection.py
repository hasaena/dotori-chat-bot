import requests
import json

def test_page_connection():
    PAGE_ACCESS_TOKEN = "EAAGr57aUTyUBO2zxcthfJX2o9LR2ykmAqq3Ddi5jt0fYjuQ7uXowm4LZAYkbEG3x9UnCkKnVUWurSLZBgTqUMtjPJV5eSGPPsgcDDBWZCyPMnntXJC0VAnz4XrVGXod38ky9Xq2y5dp96JvFdP3gABHswumYPhfW6PP8lYZAwxIPUZA8hXbOWDRarGRXcz2PPM1DHFncXyelv6TKgZCgZDZD"
    
    url = "https://graph.facebook.com/v18.0/me"
    params = {
        "access_token": PAGE_ACCESS_TOKEN,
        "fields": "id,name,category"
    }
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_page_connection() 