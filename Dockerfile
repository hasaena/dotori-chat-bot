# 1) Python 3.9-slim 사용
FROM python:3.9-slim

# 2) 작업 디렉터리 설정
WORKDIR /app

# 3) requirements.txt 먼저 복사
COPY requirements.txt /app/

# 4) 나머지 소스(.py 등) 모두 /app/에 복사
COPY . /app/

# 5) dependencies 설치 (캐시 사용 X)
RUN pip install --no-cache-dir -r requirements.txt

# (선택) 로컬에서 "docker run -p 8080:8080" 할 때 편의를 위해 EXPOSE
EXPOSE 8080

# 6) dotori-chat-bot-key.json (실제 서비스계정 JSON) 복사
# COPY dotori-chat-bot-key.json /app/dotori-chat-bot-key.json
COPY chat-bot-key.json /app/chat-bot-key.json


# 7) 컨테이너 실행 시 "python /app/chatbot.py"
CMD ["python", "/app/chatbot.py"]
