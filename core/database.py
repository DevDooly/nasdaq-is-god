import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from dotenv import load_dotenv

load_dotenv()

# 환경변수에서 DB URL 가져오기 (기본값은 docker-compose 설정과 맞춤)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@localhost:5432/nasdaq_god"
)

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async def init_db():
    async with engine.begin() as conn:
        # 이 코드는 운영 환경에서는 Alembic 사용을 권장하지만, 
        # 초기 개발 단계에서는 테이블 자동 생성을 위해 사용합니다.
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
