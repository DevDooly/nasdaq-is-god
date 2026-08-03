import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

async def find_chat_id():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    bot = Bot(token)
    
    print("Waiting for any message (Group or Private)... Send a message now.")
    
    for i in range(20):
        try:
            updates = await bot.get_updates(timeout=10)
            if updates:
                for u in updates:
                    chat = u.effective_chat
                    if chat:
                        print(f"!!! FOUND: ID={chat.id}, Title={chat.title if chat.title else 'Private'}, Type={chat.type}")
            else:
                print(f"Checking... {i+1}/20")
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(find_chat_id())
