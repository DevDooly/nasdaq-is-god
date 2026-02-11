import asyncio
from sqlalchemy import text
from core.database import engine
import logging

async def migrate():
    async with engine.begin() as conn:
        print("Starting database migration...")
        try:
            # 💡 User 테이블에 cash_balance 컬럼 추가 (PostgreSQL용)
            await conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS cash_balance FLOAT DEFAULT 100000.0'))
            print("✅ Column 'cash_balance' added to 'user' table.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())