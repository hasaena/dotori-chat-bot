import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def test_env():
    variables = [
        "OPENAI_API_KEY",
        "PAGE_ACCESS_TOKEN",
        "GOOGLE_APPLICATION_CREDENTIALS_JSON"
    ]
    
    results = {}
    for var in variables:
        value = os.getenv(var)
        if value:
            logger.info(f"{var}: 존재함 (값: {value[:5]}...)")
            results[var] = True
        else:
            logger.error(f"{var}: 없음")
            results[var] = False
    
    return results

if __name__ == "__main__":
    results = test_env()
    print("\n=== 테스트 결과 ===")
    for var, exists in results.items():
        print(f"{var}: {'성공 ✓' if exists else '실패 ✗'}") 