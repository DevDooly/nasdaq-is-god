import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

async def wait_for_group():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    bot = Bot(token)
    print(f"Waiting for messages with token {token[:10]}...")
    
    # Clear any previous updates
    await bot.get_updates(offset=-1, timeout=1)
    
    for i in range(30):
        updates = await bot.get_updates(timeout=2)
        if updates:
            for u in updates:
                chat = u.effective_chat
                if chat:
                    print(f"Update: ID={chat.id}, Type={chat.type}, Title={chat.title}")
        else:
            print(f"Waiting... {i+1}/30")
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(wait_for_group())
