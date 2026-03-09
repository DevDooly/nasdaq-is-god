import asyncio
from sqlalchemy import text
from core.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("🚀 Starting database migration V7 (Guru Insight Fields)...")
        try:
            # GuruInsight 테이블에 누락된 컬럼들 추가
            await conn.execute(text('ALTER TABLE "guruinsight" ADD COLUMN IF NOT EXISTS price_at_timestamp FLOAT'))
            await conn.execute(text('ALTER TABLE "guruinsight" ADD COLUMN IF NOT EXISTS price_after_1h FLOAT'))
            await conn.execute(text('ALTER TABLE "guruinsight" ADD COLUMN IF NOT EXISTS impact_confirmed BOOLEAN DEFAULT FALSE'))
            
            print("✅ GuruInsight fields added successfully.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
