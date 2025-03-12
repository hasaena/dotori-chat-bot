# 1. Python 베이스 이미지
FROM python:3.9-slim

# 2. 작업 디렉터리 설정
WORKDIR /app

# 3. requirements.txt 복사
COPY requirements.txt /app/

# 4. *.py 등 모든 소스 파일을 /app/ 에 복사
COPY . /app/

# 5. 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# 6. 컨테이너 실행 시, "python chatbot.py" 명령 실행
CMD ["python", "chatbot.py"]
