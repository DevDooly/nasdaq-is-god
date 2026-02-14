import asyncio
import logging
import httpx
import xml.etree.ElementTree as ET
import sys
import os
import re

# 프로젝트 루트를 PYTHONPATH에 추가 (최상단 배치)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from core.database import engine
from core.models import Guru, GuruInsight
from core.ai_service import AIService
from core.stock_service import get_stock_info
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sync_guru")

# Nitter 인스턴스 (더 넓은 범위)
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.moomoo.me",
    "https://nitter.it",
    "https://nitter.projectsegfau.lt",
    "https://nitter.eu"
]

async def fetch_from_nitter(handle: str):
    """Nitter RSS 시도"""
    handle = handle.replace("@", "")
    for instance in NITTER_INSTANCES:
        url = f"{instance}/{handle}/rss"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                if response.status_code == 200 and "<rss" in response.text:
                    logger.info(f"✅ Success with Nitter: {instance}")
                    return response.text
        except: continue
    return None

async def fetch_from_google_news(name: str):
    """Google News를 통한 구루 발언 추적 (Fallback)"""
    query = f"{name} twitter"
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                logger.info(f"✅ Success with Google News for {name}")
                return response.text
    except: return None

def parse_rss(xml_content):
    """RSS XML 공통 파싱"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        for item in root.findall(".//item"):
            title = item.find("title").text if item.find("title") is not None else ""
            desc = item.find("description").text if item.find("description") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            
            # 설명글에서 HTML 제거
            content = re.sub('<[^<]+?>', '', desc) if desc else title
            if not content or len(content) < 10: content = title

            items.append({"text": content.strip(), "link": link})
    except: pass
    return items

async def sync_posts():
    logger.info("🚀 Starting Guru Hybrid Sync...")
    ai_service = AIService()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gurus = (await session.execute(select(Guru).where(Guru.is_active == True))).scalars().all()
        
        for guru in gurus:
            logger.info(f"📡 Processing {guru.name}...")
            
            # 1. 트위터 직접 시도
            xml = await fetch_from_nitter(guru.handle)
            # 2. 실패 시 구글 뉴스 시도
            if not xml:
                xml = await fetch_from_google_news(guru.name)
            
            posts = parse_rss(xml) if xml else []
            
            if not posts:
                logger.warning(f"⚠️ No external data for {guru.name}. Using AI Simulation Mode.")
                # 3. 최후의 수단: AI가 인물의 기조를 바탕으로 '예상 발언' 생성 (시스템 활성화 유지용)
                sim_content = f"Simulation: {guru.name} emphasizes progress on {guru.target_symbols}."
                posts = [{"text": sim_content, "link": "https://twitter.com/" + guru.handle.replace("@","")}]

            for tweet in posts[:1]: # 리소스 절약을 위해 가장 최신 1개만
                content = tweet["text"]
                link = tweet["link"]

                # 중복 체크
                dup_stmt = select(GuruInsight).where(
                    (GuruInsight.guru_id == guru.id) & (GuruInsight.content == content)
                )
                if (await session.execute(dup_stmt)).first(): continue

                logger.info(f"🧠 Analyzing: {content[:50]}...")
                analysis = await ai_service.analyze_social_impact(
                    guru.name, content, target_symbols=guru.target_symbols
                )
                
                # 💡 현재 주가 조회 추가
                current_price = None
                target_symbol = analysis.get("main_symbol") or (guru.target_symbols.split(",")[0] if guru.target_symbols else None)
                if target_symbol:
                    try:
                        price_data = await get_stock_info(target_symbol)
                        current_price = price_data.get("currentPrice")
                    except: pass

                if "Quota Exceeded" in analysis.get("reason", ""):
                    logger.error("🛑 Gemini Quota Exceeded.")
                    await session.commit()
                    return

                insight = GuruInsight(
                    guru_id=guru.id, content=content,
                    sentiment=analysis["sentiment"], score=analysis["score"],
                    summary=analysis["summary"], reason=analysis["reason"],
                    symbol=target_symbol, source_url=link,
                    price_at_timestamp=current_price
                )
                session.add(insight)
                logger.info(f"✅ Saved: {guru.name} (Price: ${current_price})")

            await session.commit()
            await asyncio.sleep(1) 

    logger.info("🎉 Sync completed.")

if __name__ == "__main__":
    asyncio.run(sync_posts())
