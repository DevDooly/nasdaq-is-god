import asyncio
import os
from dotenv import load_dotenv
from core.notification_service import notification_service

async def test_notification():
    print("🚀 Testing Telegram Notification...")
    load_dotenv()
    
    # Manually check env vars
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    print(f"Token: {token[:10]}...")
    print(f"Chat ID: {chat_id}")
    
    test_message = {
        "title": "✅ 시스템 테스트 알림",
        "body": "봇 토큰 업데이트 후 정상 작동 테스트 중입니다."
    }
    
    await notification_service._send_telegram(test_message)
    print("✨ Test sequence finished. Check your Telegram!")

if __name__ == "__main__":
    asyncio.run(test_notification())
