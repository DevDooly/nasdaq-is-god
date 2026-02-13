import asyncio
from core.database import engine, init_db
from core.models import Guru
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

async def migrate():
    print("🚀 Starting database migration V3 (Guru Watch)...")
    # 1. 신규 테이블 생성 (SQLModel.metadata.create_all 호출 포함)
    await init_db()
    
    # 2. 초기 데이터 삽입
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # 기존 데이터 확인
        existing = (await session.execute(select(Guru))).first()
        if not existing:
            gurus = [
                Guru(name="Elon Musk", handle="@elonmusk", influence_score=95, target_symbols="TSLA,DOGE", description="CEO of Tesla, SpaceX and X."),
                Guru(name="Jerome Powell", handle="@federalreserve", influence_score=100, target_symbols="QQQ,SPY", description="Chair of the Federal Reserve."),
                Guru(name="Jensen Huang", handle="@nvidia", influence_score=90, target_symbols="NVDA", description="CEO of NVIDIA."),
                Guru(name="Cathie Wood", handle="@cathiedwood", influence_score=75, target_symbols="ARKK,TSLA", description="Founder of ARK Invest."),
                Guru(name="Warren Buffett", handle="@berkshire", influence_score=85, target_symbols="AAPL,KO", description="CEO of Berkshire Hathaway.")
            ]
            session.add_all(gurus)
            await session.commit()
            print("✅ Default Gurus initialized.")
        else:
            print("ℹ️ Gurus already exist. Skipping initialization.")

if __name__ == "__main__":
    asyncio.run(migrate())
