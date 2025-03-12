# 1) Python 베이스 이미지 사용 (슬림 버전)
FROM python:3.9-slim

# 2) 작업 디렉토리 설정
WORKDIR /app

# 3) requirements.txt를 먼저 복사 (의존성 설치 시 캐싱 활용)
COPY requirements.txt /app/

# 4) 나머지 소스 파일(.py 등)을 모두 /app/에 복사
COPY . /app/

# 5) pip로 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# [선택] 로컬 테스트 시 편의를 위해 8080 포트를 명시
EXPOSE 8080

# 6) 컨테이너 실행 시 "python chatbot.py"를 실행
CMD ["python", "/app/chatbot.py"]
