import yfinance as yf
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
from sqlmodel import select, or_
from core.models import NewsArticle
from core.social_service import SocialService

logger = logging.getLogger("news_scraper")

MAJOR_SYMBOLS = ["TSLA", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "QQQ", "SPY", "AMD", "BTC-USD"]

class NewsScraper:
    def __init__(self):
        self.social_service = SocialService()

    def normalize_yfinance_news(self, n: dict, default_symbol: str) -> dict:
        """yfinance 뉴스 항목 구조 정규화"""
        if "content" in n and isinstance(n["content"], dict):
            c = n["content"]
            title = c.get("title") or c.get("summary") or "주요 시장 뉴스"
            publisher = c.get("provider", {}).get("displayName") if c.get("provider") else "Yahoo Finance"
            canonical = c.get("canonicalUrl") or {}
            clickthrough = c.get("clickThroughUrl") or {}
            link = canonical.get("url") or clickthrough.get("url") or f"https://finance.yahoo.com/quote/{default_symbol}?id={c.get('id')}"
            summary = c.get("summary") or c.get("description") or title
            pub_time_str = c.get("pubDate")
            if pub_time_str:
                try:
                    pub_time = datetime.fromisoformat(pub_time_str.replace("Z", "+00:00"))
                except Exception:
                    pub_time = datetime.utcnow()
            else:
                pub_time = datetime.utcnow()
        else:
            title = n.get("title", f"{default_symbol} 시장 뉴스")
            publisher = n.get("publisher", "Market News")
            link = n.get("link") or f"https://finance.yahoo.com/quote/{default_symbol}"
            summary = n.get("summary") or title
            pub_time = datetime.fromtimestamp(n.get("providerPublishTime")) if n.get("providerPublishTime") else datetime.utcnow()

        if pub_time and pub_time.tzinfo is not None:
            pub_time = pub_time.replace(tzinfo=None)

        return {
            "symbol": default_symbol,
            "title": title,
            "publisher": publisher or "Market Wire",
            "link": link,
            "summary": summary,
            "published_at": pub_time
        }

    async def fetch_rss_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Yahoo Finance & Google News RSS 백업 뉴스 수집기"""
        items = []
        try:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.text)
                    for item in root.findall("./channel/item")[:5]:
                        title = item.findtext("title", "")
                        link = item.findtext("link", "")
                        pub_date = item.findtext("pubDate", "")
                        if title and link:
                            items.append({
                                "symbol": symbol,
                                "title": title,
                                "publisher": "Yahoo Finance RSS",
                                "link": link,
                                "summary": title,
                                "published_at": datetime.utcnow()
                            })
        except Exception as e:
            logger.warning(f"RSS fetch warning for {symbol}: {e}")
        return items

    async def fetch_and_cache_symbol_news(self, session, symbol: str) -> int:
        """특정 종목의 최신 뉴스 및 발언을 수집하여 DB에 저장 (중복 수집 방지)"""
        added_count = 0
        news_items = []

        # 1. yfinance API 시도
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news or []
            for item in raw_news[:10]:
                news_items.append(self.normalize_yfinance_news(item, symbol))
        except Exception as e:
            logger.warning(f"yfinance ticker.news failed for {symbol}: {e}")

        # 2. 결과가 부족하면 RSS 백업 수집
        if len(news_items) < 3:
            rss_items = await self.fetch_rss_news(symbol)
            news_items.extend(rss_items)

        # DB 기록
        for norm in news_items:
            link = norm["link"]
            existing = (await session.execute(select(NewsArticle).where(NewsArticle.link == link))).scalar_one_or_none()
            if not existing:
                title = norm["title"]
                summary = norm["summary"]
                lower_t = title.lower()
                is_bull = any(w in lower_t for w in ["up", "growth", "high", "rally", "gain", "surge", "record", "beat"])
                is_bear = any(w in lower_t for w in ["drop", "fall", "down", "loss", "crash", "plunge", "cut", "miss"])
                
                sentiment_str = "Bullish" if is_bull else ("Bearish" if is_bear else "Neutral")
                sentiment_score = 78 if is_bull else (32 if is_bear else 50)
                
                art = NewsArticle(
                    symbol=symbol.upper(),
                    title=title,
                    publisher=norm["publisher"],
                    link=link,
                    published_at=norm["published_at"] or datetime.utcnow(),
                    summary=summary,
                    sentiment=sentiment_str,
                    sentiment_score=sentiment_score,
                    category="NEWS"
                )
                session.add(art)
                added_count += 1

        # 3. Guru 소셜 트윗 수집
        try:
            guru_posts = await self.social_service.fetch_guru_tweets(symbol)
            for g in guru_posts:
                now_t = datetime.utcnow()
                g_link = f"https://twitter.com/{g['handle']}/{symbol}_{int(now_t.timestamp())}"
                existing = (await session.execute(select(NewsArticle).where(NewsArticle.link == g_link))).scalar_one_or_none()
                if not existing:
                    art_g = NewsArticle(
                        symbol=symbol.upper(),
                        title=f"💬 {g['guru']} ({g['handle']}) 핵심 발언",
                        publisher=g['guru'],
                        link=g_link,
                        published_at=now_t,
                        summary=g['content'],
                        sentiment="Bullish" if any(w in g['content'].lower() for w in ["disruption", "improving", "strong", "ai"]) else "Neutral",
                        sentiment_score=82 if "ai" in g['content'].lower() else 60,
                        category="GURU"
                    )
                    session.add(art_g)
                    added_count += 1
        except Exception as e:
            logger.warning(f"Guru tweets fetch error for {symbol}: {e}")

        if added_count > 0:
            await session.commit()
            logger.info(f"✅ Cached {added_count} new news/guru items for {symbol}")

        return added_count

    async def run_batch_scrape(self, session) -> int:
        """배치 주기적 자동 수집 (모든 주요 종목 및 이슈 수집)"""
        total_added = 0
        for sym in MAJOR_SYMBOLS:
            cnt = await self.fetch_and_cache_symbol_news(session, sym)
            total_added += cnt
        return total_added

news_scraper = NewsScraper()
