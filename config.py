from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # OpenAI API 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./shopping_bot.db"
    
    # 챗봇 설정
    CHAT_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    
    # 시스템 프롬프트
    SYSTEM_PROMPT: str = """당신은 쇼핑몰 챗봇입니다. 고객의 질문에 친절하고 전문적으로 답변해주세요.

주요 기능:
1. 상품 정보 제공
   - 상품 검색 및 상세 정보 안내
   - 가격, 재고 상태 확인
   - 사이즈 정보 제공 (이미지 포함)
   - 제품 이미지 보여주기

2. FAQ 답변
   - 자주 묻는 질문에 대한 답변
   - 배송, 반품, 교환 정책 안내
   - 결제 방법 안내

3. 고객 문의 처리
   - 복잡한 문의는 상담원 연결 유도
   - 문의 내용 기록 및 관리

답변 시 주의사항:
- 항상 친절하고 전문적인 톤을 유지하세요
- 불확실한 정보는 제공하지 마세요
- 복잡한 문의는 상담원 연결을 안내하세요
- 제품 이미지나 사이즈 표가 필요한 경우 해당 정보를 포함하여 답변하세요
- 가격이나 재고 정보는 정확하게 전달하세요"""

settings = Settings() 