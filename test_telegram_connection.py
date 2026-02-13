import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

async def test_bot():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("No token found")
        return
    
    bot = Bot(token)
    try:
        # Clear webhook
        await bot.delete_webhook()
        print("Webhook cleared")
        
        me = await bot.get_me()
        print(f"Bot info: {me.username} ({me.id})")
        
        # Try to get updates (this might still fail if another poll is active)
        updates = await bot.get_updates(timeout=1)
        if updates:
            for u in updates:
                chat_id = u.effective_chat.id
                print(f"Latest chat ID: {chat_id} from {u.effective_user.username if u.effective_user else 'unknown'}")
        else:
            print("No recent updates found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot())
