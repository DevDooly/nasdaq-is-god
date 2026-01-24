import httpx
import yfinance as yf
import pandas as pd
from urllib.parse import quote
from .config import logger

ticker_cache = {}

async def find_ticker(query: str) -> dict | None:
    """입력된 쿼리(종목명 또는 티커)로 가장 적합한 티커 심볼을 찾습니다."""
    if query in ticker_cache:
        logger.info(f"Found ticker in cache for query: {query}")
        return ticker_cache[query]

    logger.info(f"Searching ticker for query: {query}")
    encoded_query = quote(query)
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        quotes = data.get('quotes', [])
        if not quotes:
            return None

        best_result = next((q for q in quotes if q.get('quoteType') == 'EQUITY'), None)
        if not best_result:
            best_result = next((q for q in quotes if q.get('symbol')), None)
        
        if not best_result:
            return None

        symbol = best_result.get('symbol')
        long_name = best_result.get('longname', best_result.get('shortname', ''))
        
        result = {"symbol": symbol, "name": long_name}
        ticker_cache[query] = result
        logger.info(f"Found ticker: {symbol} for query: {query}")
        return result

    except Exception as e:
        logger.error(f"Error finding ticker for {query}: {e}")
        return None

async def get_stock_info(ticker_symbol: str) -> dict:
    """yfinance를 사용하여 특정 티커 심볼의 현재 주식 정보를 가져옵니다."""
    ticker = yf.Ticker(ticker_symbol)
    try:
        info = ticker.info
        
        hist = ticker.history(period="5d")
        
        current_price = None
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
        
        if current_price is None:
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        previous_close = info.get('previousClose')
        if previous_close is None and len(hist) > 1:
            previous_close = hist['Close'].iloc[-2]
            
        open_price = info.get('open')
        day_high = info.get('dayHigh')
        day_low = info.get('dayLow')
        volume = info.get('volume')
        short_name = info.get('shortName', ticker_symbol)

        change = None
        change_percent = None
        if current_price and previous_close:
            change = current_price - previous_close
            if previous_close != 0:
                change_percent = (change / previous_close) * 100

        return {
            "shortName": short_name,
            "currentPrice": current_price,
            "previousClose": previous_close,
            "open": open_price,
            "dayHigh": day_high,
            "dayLow": day_low,
            "volume": volume,
            "change": change,
            "changePercent": change_percent,
            "currency": info.get('currency')
        }
    except Exception as e:
        logger.error(f"Error fetching data for {ticker_symbol}: {e}")
        return {"error": f"'{ticker_symbol}'에 대한 정보를 가져오는 데 실패했습니다. 티커 심볼을 확인해주세요."}
