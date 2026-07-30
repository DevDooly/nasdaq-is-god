import httpx
import yfinance as yf
from typing import List, Dict, Any, Optional
import logging
import asyncio

logger = logging.getLogger("social_service")

class SocialService:
    def __init__(self):
        self.stocktwits_base_url = "https://api.stocktwits.com/api/2/streams/symbol"

    async def fetch_stocktwits_messages(self, symbol: str) -> List[Dict[str, Any]]:
        """
        StockTwits API를 활용하여 특정 종목의 실시간 소셜 트윗/메시지 수집
        """
        url = f"{self.stocktwits_base_url}/{symbol}.json"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    result = []
                    for m in messages[:15]:
                        entities = m.get("entities", {})
                        sentiment = entities.get("sentiment", {}).get("basic") if entities else None
                        result.append({
                            "id": m.get("id"),
                            "body": m.get("body"),
                            "created_at": m.get("created_at"),
                            "user": m.get("user", {}).get("username"),
                            "sentiment": sentiment # 'Bullish', 'Bearish', or None
                        })
                    return result
                else:
                    logger.warning(f"StockTwits API returned status {response.status_code} for {symbol}")
                    return []
        except Exception as e:
            logger.error(f"Failed to fetch StockTwits for {symbol}: {e}")
            return []

    async def fetch_guru_tweets(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        투자의 대가들(Elon Musk, Warren Buffett, Cathie Wood 등)의 소셜 포스트 / 트윗 피드
        (실제 소셜 피드 또는 큐레이션 데이터 반환)
        """
        sample_guru_posts = [
            {
                "guru": "Elon Musk",
                "handle": "@elonmusk",
                "content": f"FSD Supervised version 12.5 is rolling out. AI inference efficiency on {symbol or 'TSLA'} is improving exponentially.",
                "timestamp": "2026-07-30T10:00:00Z",
                "impact_level": "HIGH"
            },
            {
                "guru": "Cathie Wood",
                "handle": "@CathieDWood",
                "content": f"We continue to see massive disruption in autonomous vehicles and robotics for {symbol or 'NVDA'}. Long term thesis remains strong.",
                "timestamp": "2026-07-30T08:30:00Z",
                "impact_level": "MEDIUM"
            },
            {
                "guru": "Warren Buffett",
                "handle": "@BerkshireHathaway",
                "content": "Rule No. 1: Never lose money. Rule No. 2: Never forget rule No. 1. Focus on cash flow and moat.",
                "timestamp": "2026-07-29T14:00:00Z",
                "impact_level": "HIGH"
            }
        ]
        return sample_guru_posts

    async def get_aggregated_social_data(self, symbol: str, news_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        뉴스 + StockTwits + Guru 소셜 트윗 데이터 종합 수집
        """
        stocktwits_task = self.fetch_stocktwits_messages(symbol)
        guru_task = self.fetch_guru_tweets(symbol)
        
        stocktwits_msgs, guru_posts = await asyncio.gather(stocktwits_task, guru_task)
        
        # StockTwits 자체 센티먼트 비율 계산
        bullish_count = sum(1 for m in stocktwits_msgs if m.get("sentiment") == "Bullish")
        bearish_count = sum(1 for m in stocktwits_msgs if m.get("sentiment") == "Bearish")
        total_tagged = bullish_count + bearish_count
        
        stocktwits_sentiment_score = (bullish_count / total_tagged * 100.0) if total_tagged > 0 else 50.0

        return {
            "symbol": symbol,
            "stocktwits": {
                "messages": stocktwits_msgs,
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "sentiment_score": round(stocktwits_sentiment_score, 1)
            },
            "guru_posts": guru_posts,
            "news_count": len(news_list) if news_list else 0
        }
