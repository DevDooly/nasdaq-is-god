from fastapi import FastAPI, HTTPException, Query
from core.stock_service import get_stock_info, find_ticker
import uvicorn
from bot.config import logger

app = FastAPI(title="Nasdaq is God API", description="Stock Information API using yfinance")

@app.get("/")
async def root():
    return {"message": "Welcome to Nasdaq is God API"}

@app.get("/stock/{symbol}")
async def get_stock(symbol: str):
    """특정 티커 심볼의 주식 정보를 가져옵니다."""
    logger.info(f"API request for stock: {symbol}")
    data = await get_stock_info(symbol)
    
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    
    return data

@app.get("/search")
async def search_stock(q: str = Query(..., min_length=1)):
    """종목명이나 티커로 검색하여 티커 정보를 반환합니다."""
    logger.info(f"API search request for: {q}")
    result = await find_ticker(q)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No ticker found for query: {q}")
    
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
