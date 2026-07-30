import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.ai_service import AIService
from core.social_service import SocialService
from core.stock_service import get_stock_news
from core.models import AISentimentHistory

logger = logging.getLogger("sentiment_engine")

class SentimentEngine:
    def __init__(self, ai_service: AIService, social_service: SocialService):
        self.ai_service = ai_service
        self.social_service = social_service

    async def analyze_combined_sentiment(self, symbol: str, session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        종목의 뉴스 + 소셜(StockTwits) + 대가(Guru) 트윗을 통합하여 AI 센티먼트 점수 및 리포트 산출
        """
        # 1. 뉴스 데이터 수집
        news_list = await get_stock_news(symbol)
        
        # 2. 소셜 & Guru 수집
        social_data = await self.social_service.get_aggregated_social_data(symbol, news_list)
        
        # 3. AI 센티먼트 프롬프트에 뉴스 + 소셜 트윗 데이터 전달
        combined_sources = []
        for n in news_list[:5]:
            title = n.get("title", "")
            if title:
                combined_sources.append(f"[뉴스] {title}")
                
        for m in social_data["stocktwits"]["messages"][:5]:
            body = m.get("body", "")
            if body:
                combined_sources.append(f"[StockTwits] {body}")
                
        for g in social_data["guru_posts"][:3]:
            guru_name = g.get("guru", "")
            content = g.get("content", "")
            if content:
                combined_sources.append(f"[대가({guru_name})] {content}")

        # 4. LLM / AI 센티먼트 분석 수행
        formatted_news = [{"title": s} for s in combined_sources]
        ai_res = await self.ai_service.analyze_sentiment_with_rotation(
            symbol=symbol,
            news_list=formatted_news,
            api_configs=[]
        )

        # AI 결과 처리 및 Fallback 스코어 결합
        if "error" in ai_res:
            logger.warning(f"AI Sentiment call error: {ai_res['error']}. Using hybrid fallback.")
            stocktwits_score = social_data["stocktwits"]["sentiment_score"]
            sentiment_score = int(stocktwits_score)
            sentiment_label = "Bullish" if sentiment_score >= 60 else ("Bearish" if sentiment_score <= 40 else "Neutral")
            summary = f"소셜 감성 지표 기반 산출 점수: {sentiment_score}점"
            reason = "AI 프로바이더 응답 지연으로 소셜 감성 데이터를 반영하였습니다."
        else:
            sentiment_score = int(ai_res.get("score", 50))
            sentiment_label = ai_res.get("sentiment", "Neutral")
            summary = ai_res.get("summary", "분석 완료")
            reason = ai_res.get("reason", "")

        result = {
            "symbol": symbol,
            "sentiment_score": sentiment_score,
            "sentiment": sentiment_label,
            "summary": summary,
            "reason": reason,
            "social_metrics": {
                "stocktwits_sentiment_score": social_data["stocktwits"]["sentiment_score"],
                "stocktwits_message_count": len(social_data["stocktwits"]["messages"]),
                "guru_post_count": len(social_data["guru_posts"]),
                "news_count": len(news_list)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        # 5. DB 세션이 제공된 경우 히스토리에 기록
        if session:
            try:
                history_entry = AISentimentHistory(
                    symbol=symbol,
                    score=sentiment_score,
                    sentiment=sentiment_label,
                    summary=summary,
                    reason=reason,
                    created_at=datetime.utcnow()
                )
                session.add(history_entry)
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to save AISentimentHistory for {symbol}: {e}")

        return result
