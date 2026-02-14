import asyncio
from sqlalchemy import text
from core.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("🚀 Starting database migration V5 (Auto-Trade Flag)...")
        try:
            # Guru 테이블에 is_auto_trade_enabled 컬럼 추가
            await conn.execute(text('ALTER TABLE "guru" ADD COLUMN IF NOT EXISTS is_auto_trade_enabled BOOLEAN DEFAULT FALSE'))
            print("✅ Column 'is_auto_trade_enabled' added to 'guru' table.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
