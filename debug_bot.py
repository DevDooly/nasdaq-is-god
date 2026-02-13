import os
import sys
import logging
from telegram.ext import Application
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("No token")
        return
    
    print(f"Starting bot with token: {token[:10]}...")
    try:
        application = Application.builder().token(token).build()
        print("Application built. Running polling...")
        application.run_polling()
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
