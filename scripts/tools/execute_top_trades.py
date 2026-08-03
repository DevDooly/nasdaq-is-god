import asyncio
import httpx

API_URL = "http://localhost:9000"

async def execute_trades():
    async with httpx.AsyncClient() as client:
        # 1. Login to get token
        login_res = await client.post(f"{API_URL}/login", data={"username": "admin", "password": "admin123"})
        if login_res.status_code != 200:
            print("Login failed")
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Check current balance
        me_res = await client.get(f"{API_URL}/users/me", headers=headers)
        print(f"Current Balance: {me_res.json()['cash_balance']}")
        
        # 3. Top 5 NASDAQ stocks
        top_stocks = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
        
        for symbol in top_stocks:
            print(f"Purchasing 10 shares of {symbol}...")
            trade_res = await client.post(
                f"{API_URL}/trade/order", 
                params={"symbol": symbol, "quantity": 10, "side": "BUY"},
                headers=headers
            )
            if trade_res.status_code == 200:
                print(f"Successfully bought {symbol}: {trade_res.json()}")
            else:
                print(f"Failed to buy {symbol}: {trade_res.text}")

if __name__ == "__main__":
    asyncio.run(execute_trades())
