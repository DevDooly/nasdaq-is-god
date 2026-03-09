import asyncio
from core.database import engine
from core.models import Guru, GuruInsight
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from datetime import datetime, timedelta

async def seed_data():
    print("🌱 Seeding rich Guru example data...")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. 대상 구루들 가져오기
        gurus = (await session.execute(select(Guru))).scalars().all()
        guru_map = {g.name: g for g in gurus}

        # 2. 실감나는 예시 데이터 정의
        insights_data = [
            {
                "name": "Donald Trump",
                "content": "I am officially announcing that under my administration, the US will hold a Strategic National Bitcoin Reserve. Crypto is the future!",
                "sentiment": "Bullish", "score": 95, "symbol": "BTC",
                "summary": "미국 국가 비트코인 비축분 보유 선언",
                "reason": "정부 차원의 암호화폐 수용은 시장에 강력한 제도권 편입 신호를 주며, 비트코인 수요를 폭발적으로 증가시킬 것으로 분석됨."
            },
            {
                "name": "Elon Musk",
                "content": "Tesla Optimus robot is now performing tasks in our factory autonomously. This will be bigger than the car business.",
                "sentiment": "Bullish", "score": 88, "symbol": "TSLA",
                "summary": "테슬라 옵티머스 로봇의 공장 실전 투입",
                "reason": "AI 로봇 기술의 실질적 진보는 테슬라를 단순 자동차 제조사를 넘어 로보틱스/AI 기업으로 재평가하게 만드는 강력한 모멘텀임."
            },
            {
                "name": "Jensen Huang",
                "content": "The demand for Blackwell chips is insane. We are scaling production at an unprecedented rate to meet CSP needs.",
                "sentiment": "Bullish", "score": 92, "symbol": "NVDA",
                "summary": "블랙웰 칩에 대한 '미친' 수준의 수요",
                "reason": "차세대 AI 칩의 강력한 수요가 확인됨에 따라 엔비디아의 데이터 센터 부문 매출 가이던스가 대폭 상향될 것으로 예상됨."
            },
            {
                "name": "Jerome Powell",
                "content": "Labor market remains strong, but we are seeing clear signs of disinflation. The time for recalibrating our policy is approaching.",
                "sentiment": "Bullish", "score": 75, "symbol": "SPY",
                "summary": "금리 인하(정책 재조정) 시기 근접 시사",
                "reason": "연준의 완화적 통화정책으로의 전환 기조는 시장 유동성 공급에 대한 기대를 높여 지수 전체에 호재로 작용함."
            },
            {
                "name": "Warren Buffett",
                "content": "We have increased our stake in high-quality defensive businesses. Cash is a position, not just a place to wait.",
                "sentiment": "Neutral", "score": 55, "symbol": "AAPL",
                "summary": "방어주 비중 확대 및 현금 보유 강조",
                "reason": "보수적인 투자 거물의 스탠스는 시장 변동성에 대한 경고로 읽힐 수 있어 단기적으로는 관망세를 유도함."
            }
        ]

        for data in insights_data:
            guru = guru_map.get(data["name"])
            if not guru: continue
            
            # 기존 데이터 중복 체크 (내용 기반)
            existing = (await session.execute(select(GuruInsight).where(GuruInsight.content == data["content"]))).first()
            if existing: continue

            insight = GuruInsight(
                guru_id=guru.id,
                content=data["content"],
                sentiment=data["sentiment"],
                score=data["score"],
                summary=data["summary"],
                reason=data["reason"],
                symbol=data["symbol"],
                timestamp=datetime.utcnow() - timedelta(minutes=60) # 1시간 전 데이터로 세팅
            )
            session.add(insight)
            print(f"✅ Added: [{guru.name}] {data['summary']}")

        await session.commit()
        print("✨ Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
