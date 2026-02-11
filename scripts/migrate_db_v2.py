import asyncio
from sqlalchemy import text
from core.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Starting database migration V2...")
        try:
            # 💡 User 테이블에 is_auto_trading_enabled 컬럼 추가
            await conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_auto_trading_enabled BOOLEAN DEFAULT TRUE'))
            print("✅ Column 'is_auto_trading_enabled' added to 'user' table.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
