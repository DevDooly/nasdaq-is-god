import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_progress_update():
    # Get updates to find a chat_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        response = requests.get(url).json()
    except Exception as e:
        print(f"Error fetching updates: {e}")
        return False
    
    if not response.get("ok") or not response.get("result"):
        print("Error: No updates found. Please send a message (like /start) to the bot first.")
        return False
    
    # Get the latest chat_id
    chat_id = response["result"][-1]["message"]["chat"]["id"]
    
    message = (
        "🚀 *Nasdaq is God 개발 진행 리포트*\n\n"
        "1. *아키텍처:* 풀스택(FastAPI + Flutter + PostgreSQL) 전환 완료\n"
        "2. *인증:* JWT 기반 보안 로그인 시스템 구축\n"
        "3. *매매:* KIS 실전 API 연동 및 Mock 브로커 지원\n"
        "4. *분석:* RSI, MACD 등 기술적 지표 엔진 완료\n"
        "5. *저장소:* GitHub Push 및 .env 템플릿 구성 완료\n\n"
        "✅ 모든 핵심 백엔드 준비가 끝났습니다!"
    )
    
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    send_response = requests.post(send_url, data={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).json()
    
    if send_response.get("ok"):
        print(f"Success: Message sent to chat_id {chat_id}")
        return True
    else:
        print(f"Error: {send_response.get('description')}")
        return False

if __name__ == "__main__":
    send_progress_update()