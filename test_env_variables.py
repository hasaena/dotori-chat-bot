import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI

# .env 파일 로드
load_dotenv()

def test_env_variables():
    page_access_token = os.getenv("PAGE_ACCESS_TOKEN")
    app_secret = os.getenv("APP_SECRET")
    verify_token = os.getenv("VERIFY_TOKEN")
    
    print("PAGE_ACCESS_TOKEN:", page_access_token)
    print("APP_SECRET:", app_secret)
    print("VERIFY_TOKEN:", verify_token)

def create_chatbot():
    llm = ChatOpenAI(
        openai_api_key="REDACTED_OPENAI_KEY",
        temperature=0.7
    )
    return llm

if __name__ == "__main__":
    test_env_variables() 