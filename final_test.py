import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

async def test_bot():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("No token")
        return
    
    bot = Bot(token)
    print("Testing get_me...")
    me = await bot.get_me()
    print(f"Me: {me.username}")
    
    print("Testing get_updates...")
    try:
        updates = await bot.get_updates(timeout=5)
        print(f"Got {len(updates)} updates")
    except Exception as e:
        print(f"Error during get_updates: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot())
