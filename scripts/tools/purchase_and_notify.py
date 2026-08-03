import asyncio
import httpx
import os
from telegram import Bot
from dotenv import load_dotenv

API_URL = "http://localhost:9000"

async def purchase_and_notify():
    load_dotenv()
    token_tg = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token_tg or not chat_id:
        print("Telegram configuration missing in .env")
        return

    bot = Bot(token_tg)
    results = []
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_res = await client.post(f"{API_URL}/login", data={"username": "admin", "password": "admin123"})
        if login_res.status_code != 200:
            print("Login failed")
            return
        
        access_token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Top 5 NASDAQ stocks
        top_stocks = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
        
        for symbol in top_stocks:
            print(f"Purchasing 10 shares of {symbol}...")
            trade_res = await client.post(
                f"{API_URL}/trade/order", 
                params={"symbol": symbol, "quantity": 10, "side": "BUY"},
                headers=headers
            )
            if trade_res.status_code == 200:
                data = trade_res.json()
                price = data.get('price')
                price_str = f"${price:,.2f}" if price is not None else "N/A"
                results.append(f"✅ {symbol}: 10주 매수 성공 ({price_str})")
            else:
                results.append(f"❌ {symbol}: 매수 실패 ({trade_res.text})")
        
        # 3. Final balance
        me_res = await client.get(f"{API_URL}/users/me", headers=headers)
        new_balance = me_res.json()['cash_balance']
        
        # 4. Format and send Telegram message
        message = "🔔 *추가 매수 집행 리포트*\n\n"
        message += "\n".join(results)
        message += f"\n\n💰 *현재 잔고*: ${new_balance:,.2f}"
        
        chat_ids = [cid.strip() for cid in chat_id.split(",") if cid.strip()]
        for cid in chat_ids:
            try:
                await bot.send_message(chat_id=cid, text=message, parse_mode='Markdown')
                print(f"Telegram notification sent to {cid}!")
            except Exception as e:
                print(f"Failed to send Telegram message to {cid}: {e}")

if __name__ == "__main__":
    asyncio.run(purchase_and_notify())
