from openai import OpenAI
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

def get_openai_response(user_input):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 친절한 한국어 챗봇입니다."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

def simple_chat():
    print("OpenAI가 연동된 대화창입니다. '종료'를 입력하면 대화가 종료됩니다.")
    
    while True:
        user_input = input("\n사용자: ")
        
        if user_input.lower() == '종료':
            print("대화를 종료합니다.")
            break
            
        # OpenAI API를 통해 응답 생성
        response = get_openai_response(user_input)
        print(f"\n챗봇: {response}")

if __name__ == "__main__":
    simple_chat() 