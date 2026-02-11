import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

def wait_and_send():
    print("Waiting for a message from the user...")
    for _ in range(5):
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        try:
            response = requests.get(url).json()
            if response.get("ok") and response.get("result"):
                chat_id = response["result"][-1]["message"]["chat"]["id"]
                
                message = """🚀 *Nasdaq is God 개발 진행 리포트*

1. *아키텍처:* 풀스택(FastAPI + Flutter + PostgreSQL) 전환 완료
2. *인증:* JWT 기반 보안 로그인 시스템 구축
3. *매매:* KIS 실전 API 연동 및 Mock 브로커 지원
4. *분석:* RSI, MACD 등 기술적 지표 엔진 완료
5. *저장소:* GitHub Push 및 .env 템플릿 구성 완료

✅ 모든 핵심 백엔드 준비가 끝났습니다!"""
                
                send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                requests.post(send_url, data={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                })
                print(f"Success! Sent to {chat_id}")
                return True
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(2)
    
    print("Failed to find any updates.")
    return False

if __name__ == "__main__":
    wait_and_send()
