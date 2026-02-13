import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

async def find_chat_id():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    bot = Bot(token)
    
    print("Finding Chat ID... Please send a message to the bot @k_dopamine_bot")
    print("I will retry for 60 seconds...")
    
    for i in range(12): # 12 * 5s = 60s
        try:
            updates = await bot.get_updates(timeout=10)
            if updates:
                for u in updates:
                    if u.effective_chat:
                        chat_id = u.effective_chat.id
                        username = u.effective_user.username if u.effective_user else "Unknown"
                        print(f"!!! FOUND CHAT ID: {chat_id} from {username}")
                        return chat_id
            else:
                print(f"Waiting... ({i+1}/12)")
        except Exception as e:
            print(f"Retry {i+1} failed: {e}")
        
        await asyncio.sleep(5)
    
    print("Could not find Chat ID. Make sure you sent a message to the bot.")
    return None

if __name__ == "__main__":
    asyncio.run(find_chat_id())
