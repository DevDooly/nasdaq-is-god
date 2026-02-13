import asyncio
from core.stock_service import get_stock_info, find_ticker

async def test_stock_service():
    print("Testing find_ticker('Samsung')...")
    res = await find_ticker("Samsung")
    print(f"Result: {res}")
    
    print("\nTesting get_stock_info('AAPL')...")
    res = await get_stock_info("AAPL")
    print(f"Result price: {res.get('currentPrice')}")
    
    print("\nTesting get_stock_info('KRW=X')...")
    res = await get_stock_info("KRW=X")
    print(f"Result price: {res.get('currentPrice')}")

if __name__ == "__main__":
    asyncio.run(test_stock_service())
