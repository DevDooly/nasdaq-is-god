import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from core.database import engine
from core.news_scraper import news_scraper
from core.models import NewsArticle
from sqlmodel import select
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_news")

INITIAL_ARTICLES = [
    {
        "symbol": "TSLA",
        "title": "⚡ 테슬라 FSD v12.5 글로벌 출시 및 로보택시 기대감 고조",
        "publisher": "Yahoo Finance",
        "link": "https://finance.yahoo.com/news/tesla-fsd-v12-5-rollout-robotaxi-2026-01",
        "summary": "일론 머스크는 FSD 12.5 버전이 엔드투엔드 AI 추론 효율성을 획기적으로 개선하였으며, 로보택시 공개 카운트다운에 들어갔다고 발표했습니다.",
        "sentiment": "Bullish",
        "sentiment_score": 88,
        "category": "NEWS"
    },
    {
        "symbol": "NVDA",
        "title": "🚀 엔비디아 차세대 블랙웰(Blackwell) AI 칩 수요 폭발",
        "publisher": "Reuters",
        "link": "https://reuters.com/technology/nvidia-blackwell-chip-demand-surge-2026-02",
        "summary": "빅테크 기업들의 AI 데이터센터 투자 확대로 엔비디아의 차세대 가속기 주문량이 공급량을 크게 상회하고 있는 것으로 나타났습니다.",
        "sentiment": "Bullish",
        "sentiment_score": 92,
        "category": "NEWS"
    },
    {
        "symbol": "AAPL",
        "title": "🍎 애플 실적 발표 임박: 애플 인텔리전스 및 신형 아이폰 수요 주목",
        "publisher": "Bloomberg",
        "link": "https://bloomberg.com/news/apple-earnings-preview-ai-integration-2026-03",
        "summary": "월가 분석가들은 애플 인텔리전스(Apple Intelligence) 온디바이스 AI 서비스 탑재가 차세대 아이폰 교체 수요를 강력히 견인할 것으로 전망했습니다.",
        "sentiment": "Bullish",
        "sentiment_score": 75,
        "category": "NEWS"
    },
    {
        "symbol": "TSLA",
        "title": "💬 Elon Musk (@elonmusk) 핵심 발언",
        "publisher": "Elon Musk",
        "link": "https://twitter.com/elonmusk/status/1885000001",
        "summary": "FSD Supervised version 12.5 is rolling out. AI inference efficiency on TSLA is improving exponentially.",
        "sentiment": "Bullish",
        "sentiment_score": 85,
        "category": "GURU"
    },
    {
        "symbol": "NVDA",
        "title": "💬 Cathie Wood (@CathieDWood) 핵심 발언",
        "publisher": "Cathie Wood",
        "link": "https://twitter.com/CathieDWood/status/1885000002",
        "summary": "We continue to see massive disruption in autonomous vehicles and robotics for NVDA. Long term thesis remains strong.",
        "sentiment": "Bullish",
        "sentiment_score": 82,
        "category": "GURU"
    },
    {
        "symbol": "MARKET",
        "title": "💬 Warren Buffett (@BerkshireHathaway) 핵심 발언",
        "publisher": "Warren Buffett",
        "link": "https://twitter.com/BerkshireHathaway/status/1885000003",
        "summary": "Rule No. 1: Never lose money. Rule No. 2: Never forget rule No. 1. Focus on cash flow and moat.",
        "sentiment": "Neutral",
        "sentiment_score": 60,
        "category": "GURU"
    },
    {
        "symbol": "MARKET",
        "title": "📉 연준(Fed) 금리 동향 및 미 증시 인플레이션 데이터 발표 주목",
        "publisher": "MarketWatch",
        "link": "https://marketwatch.com/story/fed-interest-rate-policy-inflation-2026-04",
        "summary": "미 연방준비제도의 통화정책 방향과 물가지표 발표를 앞두고 나스닥 및 S&P 500 지수가 조정을 받으며 유동성 장세가 이어지고 있습니다.",
        "sentiment": "Neutral",
        "sentiment_score": 50,
        "category": "ISSUE"
    }
]

async def seed():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        logger.info("🌱 Seeding initial news & guru statements...")
        added_count = 0
        for item in INITIAL_ARTICLES:
            existing = (await session.execute(select(NewsArticle).where(NewsArticle.link == item["link"]))).scalar_one_or_none()
            if not existing:
                art = NewsArticle(
                    symbol=item["symbol"],
                    title=item["title"],
                    publisher=item["publisher"],
                    link=item["link"],
                    published_at=datetime.utcnow(),
                    summary=item["summary"],
                    sentiment=item["sentiment"],
                    sentiment_score=item["sentiment_score"],
                    category=item["category"]
                )
                session.add(art)
                added_count += 1
        
        if added_count > 0:
            await session.commit()
            logger.info(f"✅ Successfully seeded {added_count} initial articles!")
        
        # 💡 추가로 라이브 뉴스 스크래퍼 실행
        try:
            batch_added = await news_scraper.run_batch_scrape(session)
            logger.info(f"🌐 Live Scraper added {batch_added} fresh items!")
        except Exception as e:
            logger.error(f"Live scraper error during seeding: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
