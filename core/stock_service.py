import httpx
import yfinance as yf
import pandas as pd
from urllib.parse import quote
import logging
import time

logger = logging.getLogger("stock_service")

# 캐시 저장소
ticker_cache = {}
price_cache = {}
CACHE_EXPIRE_SECONDS = 60  # 시세 데이터 캐시 유지 시간 (1분)

async def find_ticker(query: str) -> dict | None:
    """입력된 쿼리(종목명 또는 티커)로 가장 적합한 티커 심볼을 찾습니다."""
    if query in ticker_cache:
        logger.info(f"Found ticker in cache: {query}")
        return ticker_cache[query]

    logger.info(f"Searching ticker for: {query}")
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
        return result

    except Exception as e:
        logger.error(f"Error finding ticker for {query}: {e}")
        return None

async def get_stock_info(ticker_symbol: str) -> dict:
    """yfinance를 사용하여 주식 정보를 가져오며, 1분간 캐싱을 적용합니다."""
    
    # 1. 캐시 확인
    now = time.time()
    if ticker_symbol in price_cache:
        cached_data, timestamp = price_cache[ticker_symbol]
        if now - timestamp < CACHE_EXPIRE_SECONDS:
            logger.info(f"💡 [Cache Hit] Returning cached price for {ticker_symbol}")
            return cached_data

    # 2. 캐시 없거나 만료된 경우 실제 조회
    logger.info(f"🌐 [API Fetch] Fetching real-time price for {ticker_symbol}")
    ticker = yf.Ticker(ticker_symbol)
    try:
        hist = ticker.history(period="2d")
        
        if hist.empty:
            info = ticker.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            previous_close = info.get('previousClose')
            short_name = info.get('shortName', ticker_symbol)
            currency = info.get('currency', 'USD')
        else:
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            short_name = ticker_symbol
            currency = "USD" 

        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close != 0 else 0

        result = {
            "shortName": short_name,
            "currentPrice": float(current_price),
            "previousClose": float(previous_close),
            "change": float(change),
            "changePercent": float(change_percent),
            "currency": currency
        }

        # 3. 결과 캐싱
        price_cache[ticker_symbol] = (result, now)
        return result

    except Exception as e:
        logger.error(f"Error fetching data for {ticker_symbol}: {e}")
        return {"error": f"Failed to fetch data for {ticker_symbol}"}

async def get_stock_news(ticker_symbol: str) -> list:
    """yfinance를 사용하여 특정 종목의 최신 뉴스 리스트를 가져옵니다."""
    ticker = yf.Ticker(ticker_symbol)
    try:
        news = ticker.news
        return news[:5]  # 최신 뉴스 5개만 반환
    except Exception as e:
        logger.error(f"Error fetching news for {ticker_symbol}: {e}")
        return []