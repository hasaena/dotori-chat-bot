FROM python:3.9-slim

WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt .
COPY *.py .
COPY *.json .

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 포트 설정
ENV PORT 8080

# 실행
CMD ["python", "chatbot.py"]
