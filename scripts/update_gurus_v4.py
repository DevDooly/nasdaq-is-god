import asyncio
from core.database import engine
from core.models import Guru, GuruInsight
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select
from core.ai_service import AIService
from datetime import datetime, timedelta

async def update_data():
    print("🚀 Updating Guru list and adding example insights...")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    ai_service = AIService()
    
    async with async_session() as session:
        # 1. 도널드 트럼프 추가
        existing_trump = (await session.execute(select(Guru).where(Guru.handle == "@realDonaldTrump"))).first()
        if not existing_trump:
            trump = Guru(
                name="Donald Trump", 
                handle="@realDonaldTrump", 
                influence_score=98, 
                target_symbols="DJT,SPY,BTC", 
                description="45th and 47th President of the United States. High market volatility driver."
            )
            session.add(trump)
            print("✅ Donald Trump added to Guru list.")
        
        await session.commit()

        # 2. 구루 정보 다시 가져오기
        gurus = (await session.execute(select(Guru))).scalars().all()
        guru_map = {g.name: g for g in gurus}

        # 3. 예시 발언 데이터 (최근 시장 상황 반영)
        examples = [
            {"name": "Elon Musk", "content": "Tesla FSD v13 is officially rolling out. The leap in autonomy is mind-blowing."},
            {"name": "Jerome Powell", "content": "Inflation remains above our 2% target. We are prepared to maintain restrictive policy for longer if necessary."},
            {"name": "Jensen Huang", "content": "The next industrial revolution has begun. Demand for Blackwell is significantly exceeding supply."},
            {"name": "Donald Trump", "content": "We will make America the crypto capital of the planet and the Bitcoin superpower of the world."},
            {"name": "Cathie Wood", "content": "We believe Tesla is the biggest AI project in the world and could reach $2000 per share by 2029."},
        ]

        print("🧠 Running AI analysis for example insights...")
        for ex in examples:
            guru = guru_map.get(ex["name"])
            if not guru: continue
            
            # AI 분석 실행
            analysis = await ai_service.analyze_social_impact(guru.name, ex["content"], target_symbols=guru.target_symbols)
            
            # 인사이트 저장
            insight = GuruInsight(
                guru_id=guru.id,
                content=ex["content"],
                sentiment=analysis["sentiment"],
                score=analysis["score"],
                summary=analysis["summary"],
                reason=analysis["reason"],
                symbol=analysis.get("main_symbol"),
                timestamp=datetime.utcnow() - timedelta(hours=len(examples)) # 시간을 조금씩 다르게 배정
            )
            session.add(insight)
            print(f"✅ Added insight for {guru.name}: {analysis['sentiment']} ({analysis['score']})")

        await session.commit()
        print("✨ Data update complete!")

if __name__ == "__main__":
    asyncio.run(update_data())
