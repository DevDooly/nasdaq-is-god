import asyncio
from sqlalchemy import text
from core.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("🚀 Starting database migration V6 (Multi-AI Provider)...")
        try:
            # provider 컬럼 추가
            await conn.execute(text('ALTER TABLE "apikeyconfig" ADD COLUMN IF NOT EXISTS provider VARCHAR DEFAULT \'GOOGLE\''))
            # base_url 컬럼 추가
            await conn.execute(text('ALTER TABLE "apikeyconfig" ADD COLUMN IF NOT EXISTS base_url VARCHAR'))
            # key_value 컬럼 nullable로 변경
            await conn.execute(text('ALTER TABLE "apikeyconfig" ALTER COLUMN key_value DROP NOT NULL'))
            
            print("✅ Multi-AI columns added to 'apikeyconfig' table.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
