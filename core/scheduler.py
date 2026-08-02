"""
뉴스 및 월가 거장(Guru) 발언 배치 수집 및 AI 분석 스케줄러 모듈.
"""

import logging
import asyncio
from datetime import datetime
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import select, or_

from core.database import engine, get_session
from core.models import NewsArticle, GuruInsight, Guru
from core.stock_service import get_stock_news
from core.social_service import SocialService
from core.ai_service import AIService
from core.sentiment_engine import SentimentEngine

logger = logging.getLogger("batch_scheduler")

class BatchCollectorScheduler:
    """
    뉴스 스크레이핑, 거장 발언 수집 및 AI 센티먼트 평가를 주기적 배치(Batch)로 실행하는 스케줄러.
    """

    def __init__(self, target_symbols: List[str] = None):
        """
        BatchCollectorScheduler 초기화.

        :param target_symbols: 스케줄링 수집 대상 주식 종목 리스트
        """
        self.target_symbols = target_symbols or ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL"]
        self.scheduler = AsyncIOScheduler()
        self.social_service = SocialService()
        self.ai_service = AIService()
        self.sentiment_engine = SentimentEngine(self.ai_service, self.social_service)

    def start(self):
        """배치 태스크 스케줄러를 시작합니다."""
        if not self.scheduler.running:
            # 1. 10분 마다 뉴스 자동 배치 수집
            self.scheduler.add_job(
                self.fetch_news_batch,
                'interval',
                minutes=10,
                id='fetch_news_batch',
                replace_existing=True
            )
            # 2. 5분 마다 월가 거장 소셜/트윗 발언 자동 수집
            self.scheduler.add_job(
                self.fetch_guru_insights_batch,
                'interval',
                minutes=5,
                id='fetch_guru_insights_batch',
                replace_existing=True
            )
            # 3. 15분 마다 미분석 항목 AI 감성 일괄 평가
            self.scheduler.add_job(
                self.analyze_pending_sentiments_batch,
                'interval',
                minutes=15,
                id='analyze_pending_sentiments_batch',
                replace_existing=True
            )
            self.scheduler.start()
            logger.info("⏰ BatchCollectorScheduler successfully started with interval jobs (News: 10m, Guru: 5m, AI: 15m).")

    def stop(self):
        """배치 스케줄러를 정지합니다."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("⏹️ BatchCollectorScheduler stopped.")

    async def fetch_news_batch(self):
        """주요 대상 종목에 대한 실시간 뉴스 수집 및 중복 체크 후 DB 저장 배치 태스크."""
        logger.info(f"📰 [Batch Task] Starting news collection for {self.target_symbols}...")
        count = 0
        try:
            async for session in get_session():
                for symbol in self.target_symbols:
                    articles = await get_stock_news(symbol)
                    for item in articles[:5]: # 종목당 최신 5개
                        title = item.get("title")
                        link = item.get("link")
                        publisher = item.get("publisher", "Yahoo Finance")
                        
                        if not title or not link:
                            continue

                        # 중복 수집 체크
                        stmt = select(NewsArticle).where(NewsArticle.link == link)
                        res = await session.execute(stmt)
                        existing = res.scalars().first()

                        if not existing:
                            article = NewsArticle(
                                symbol=symbol,
                                title=title,
                                publisher=publisher,
                                link=link,
                                summary=item.get("summary", ""),
                                category="NEWS"
                            )
                            session.add(article)
                            count += 1
                await session.commit()
                break
            logger.info(f"✅ [Batch Task] News collection completed. {count} new articles saved.")
        except Exception as e:
            logger.error(f"❌ [Batch Task] News collection error: {e}")

    async def fetch_guru_insights_batch(self):
        """월가 대가/거장 소셜 및 트윗 발언 수집 배치 태스크."""
        logger.info("🧙‍♂️ [Batch Task] Starting Guru insights collection...")
        count = 0
        try:
            async for session in get_session():
                # DB의 활성화된 Guru 목록 가져오기
                stmt = select(Guru).where(Guru.is_active == True)
                res = await session.execute(stmt)
                gurus = res.scalars().all()

                for guru in gurus:
                    # 각 거장별 연관 종목 소셜 데이터 수집
                    symbols = [s.strip() for s in guru.target_symbols.split(",") if s.strip()] or ["TSLA", "NVDA"]
                    for sym in symbols:
                        posts = await self.social_service.get_stocktwits_feed(sym)
                        for post in posts[:3]:
                            body = post.get("body", "")
                            if not body:
                                continue

                            # 최근 24시간 내 동일 원문 체크
                            stmt_check = select(GuruInsight).where(
                                GuruInsight.guru_id == guru.id,
                                GuruInsight.content == body
                            )
                            check_res = await session.execute(stmt_check)
                            if not check_res.scalars().first():
                                insight = GuruInsight(
                                    guru_id=guru.id,
                                    symbol=sym,
                                    content=body,
                                    sentiment=post.get("sentiment", "Neutral"),
                                    score=50,
                                    summary=body[:100],
                                    reason="Batch collected social statement"
                                )
                                session.add(insight)
                                count += 1
                await session.commit()
                break
            logger.info(f"✅ [Batch Task] Guru insights collection completed. {count} new insights saved.")
        except Exception as e:
            logger.error(f"❌ [Batch Task] Guru insights collection error: {e}")

    async def analyze_pending_sentiments_batch(self):
        """DB의 미평가 뉴스 건에 대해 AI 센티먼트 일괄 평가 수행 태스크."""
        logger.info("🧠 [Batch Task] Starting AI sentiment batch analysis...")
        count = 0
        try:
            async for session in get_session():
                stmt = select(NewsArticle).where(NewsArticle.sentiment == None).limit(10)
                res = await session.execute(stmt)
                pending_articles = res.scalars().all()

                for article in pending_articles:
                    sentiment_res = await self.sentiment_engine.analyze_combined_sentiment(article.symbol)
                    article.sentiment = sentiment_res.get("sentiment", "Neutral")
                    article.sentiment_score = int(sentiment_res.get("sentiment_score", 50))
                    article.summary = sentiment_res.get("summary", article.summary)
                    count += 1

                await session.commit()
                break
            logger.info(f"✅ [Batch Task] AI sentiment batch analysis completed for {count} items.")
        except Exception as e:
            logger.error(f"❌ [Batch Task] AI sentiment batch error: {e}")
