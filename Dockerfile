FROM python:3.9-slim
WORKDIR /app

# 기존
# COPY requirements.txt .
# COPY *.py .

# 수정
COPY requirements.txt /app/
COPY *.py /app/

RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["python", "/app/chatbot.py"]
