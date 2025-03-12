import os
from openai import OpenAI

api_key = "REDACTED_OPENAI_KEY"

client = OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "안녕하세요"}
        ]
    )
    print("API 호출 성공!")
    print("응답:", response.choices[0].message.content)
except Exception as e:
    print("API 호출 실패:", str(e)) 