import asyncio
from sqlalchemy import text
from core.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Starting database migration V3 (API Key Management)...")
        try:
            # 💡 APIKeyConfig 테이블 생성
            await conn.execute(text('''
                CREATE TABLE IF NOT EXISTS apikeyconfig (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
                    provider VARCHAR(50) DEFAULT 'Gemini',
                    label VARCHAR(100) NOT NULL,
                    key_value VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT FALSE,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TIMESTAMP WITHOUT TIME ZONE,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            print("✅ Table 'apikeyconfig' created successfully.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
